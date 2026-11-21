"""Persist only the public first page of the GlobalGiving catalog."""

import asyncio
import hashlib
import logging
import os
from collections.abc import Coroutine
from pathlib import Path
from tempfile import NamedTemporaryFile
from time import time
from typing import Any, Literal
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, model_validator

from projects.models import (
    DiscoveryQuery,
    DiscoveryResult,
    OrganizationReference,
    ProjectSummary,
)
from projects.urls import safe_url

logger = logging.getLogger(__name__)
EXPLORE_QUERY = DiscoveryQuery(page_size=9)
_MAX_AGE = 1800
_MAX_BYTES = 128 * 1024


class _PublicData(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)


class _Organization(_PublicData):
    id: str = Field(pattern=r"^[1-9][0-9]{0,19}$")
    name: str | None


class _Card(_PublicData):
    id: str = Field(pattern=r"^[1-9][0-9]{0,19}$")
    title: str | None
    summary: str | None
    image_url: str | None
    theme: str | None
    country: str | None
    organization: _Organization | None


class _Page(_PublicData):
    version: Literal[1] = 1
    provider: Literal["globalgiving"] = "globalgiving"
    generated_at: float = Field(gt=0, allow_inf_nan=False)
    has_more: bool
    next_position_hint: int | None = Field(default=None, gt=0)
    items: tuple[_Card, ...] = Field(min_length=1, max_length=9)

    @model_validator(mode="after")
    def validate_items(self) -> "_Page":
        if self.has_more and len(self.items) != EXPLORE_QUERY.page_size:
            raise ValueError("A continued snapshot needs a full page")
        if self.next_position_hint is not None and not self.has_more:
            raise ValueError("A snapshot hint requires a continuation")
        if len({item.id for item in self.items}) != len(self.items):
            raise ValueError("Duplicate project in snapshot")
        for item in self.items:
            url = item.image_url
            if url is not None and (_snapshot_image(url) is None):
                raise ValueError(
                    "Snapshot image must have a public URL without parameters"
                )
        return self

    def summaries(self) -> tuple[ProjectSummary, ...]:
        return tuple(
            ProjectSummary(
                item.id,
                item.title,
                item.summary,
                item.image_url,
                item.theme,
                item.country,
                OrganizationReference(item.organization.id, item.organization.name)
                if item.organization is not None
                else None,
            )
            for item in self.items
        )


def _snapshot_image(url: str | None) -> str | None:
    if url is None or safe_url(url) != url:
        return None
    parsed = urlsplit(url)
    return None if parsed.query or parsed.fragment else url


def prefix_digest(items: tuple[ProjectSummary, ...]) -> str:
    # IDs are canonical positive decimal strings from the mapper.
    return hashlib.sha256(",".join(item.id for item in items).encode()).hexdigest()


def _atomic_write(path: Path, body: bytes) -> None:
    temp = None
    try:
        with NamedTemporaryFile(
            dir=path.parent, prefix=f".{path.name}.", delete=False
        ) as file:
            temp = Path(file.name)
            file.write(body)
            file.flush()
            os.fsync(file.fileno())
        os.replace(temp, path)
    finally:
        if temp is not None:
            temp.unlink(missing_ok=True)


class ExploreSnapshot:
    def __init__(self, path: Path, refresh_seconds: int) -> None:
        if not 60 <= refresh_seconds < _MAX_AGE:
            raise ValueError(
                "Snapshot refresh interval must be between 60 and 1799 seconds"
            )
        self.path = path
        self.refresh_seconds = refresh_seconds
        self._page: _Page | None = None
        self._generation = 0
        self._write_lock = asyncio.Lock()

    @property
    def generation(self) -> int:
        return self._generation

    @classmethod
    def from_env(cls) -> "ExploreSnapshot | None":
        path = os.getenv("KINDRED_EXPLORE_SNAPSHOT_PATH", "").strip()
        if not path:
            return None
        return cls(
            Path(path),
            int(os.getenv("KINDRED_EXPLORE_SNAPSHOT_REFRESH_SECONDS", "600")),
        )

    def load(self) -> None:
        try:
            if not self.path.is_file():
                return
            with self.path.open("rb") as file:
                data = file.read(_MAX_BYTES + 1)
            if len(data) > _MAX_BYTES:
                raise ValueError("Snapshot exceeds the byte budget")
            # Require the envelope's identity fields on disk even though generation
            # uses model defaults.
            page = _Page.model_validate_json(data)
            if not {"version", "provider"} <= page.model_fields_set:
                raise ValueError("Snapshot identity is missing")
            self._page = page
        except (OSError, ValueError):
            logger.warning("explore_snapshot event=read_failed")

    def current(self) -> _Page | None:
        page = self._page
        if page is not None and 0 <= time() - page.generated_at < _MAX_AGE:
            return page
        return None

    def initial_delay(self) -> float:
        page = self.current()
        return (
            max(0, self.refresh_seconds - (time() - page.generated_at)) if page else 0
        )

    async def publish(
        self,
        result: DiscoveryResult,
        *,
        generation: int,
        next_position_hint: int | None = None,
    ) -> None:
        # A valid empty result can still be returned dynamically. It cannot
        # replace a usable seed, which may be retained only up to its age limit.
        if not result.items:
            return
        try:
            page = _Page(
                generated_at=time(),
                has_more=result.continuation is not None,
                next_position_hint=next_position_hint,
                items=tuple(
                    _Card(
                        id=item.id,
                        title=item.title,
                        summary=item.summary,
                        image_url=_snapshot_image(item.image_url),
                        theme=item.theme,
                        country=item.country,
                        organization=_Organization(
                            id=item.organization.id, name=item.organization.name
                        )
                        if item.organization is not None
                        else None,
                    )
                    for item in result.items
                ),
            )
            body = page.model_dump_json().encode()
            if len(body) > _MAX_BYTES:
                raise ValueError("Snapshot exceeds the byte budget")
        except ValueError:
            logger.warning("explore_snapshot event=publication_rejected")
            return
        async with self._write_lock:
            if generation != self.generation:
                logger.debug("explore_snapshot event=stale_publication_discarded")
                return
            try:
                await self._finish_io(asyncio.to_thread(_atomic_write, self.path, body))
            except OSError:
                logger.warning("explore_snapshot event=write_failed")
            self._page = page
            logger.debug(
                "explore_snapshot event=updated bytes=%d generated_at=%.0f",
                len(body),
                page.generated_at,
            )

    async def discard(self, expected_prefix: str) -> int | None:
        async with self._write_lock:
            page = self._page
            if page is None or prefix_digest(page.summaries()) != expected_prefix:
                return None
            invalidated_generation = self.generation
            self._generation += 1
            self._page = None
            try:
                await self._finish_io(
                    asyncio.to_thread(self.path.unlink, missing_ok=True)
                )
            except OSError:
                logger.warning("explore_snapshot event=unlink_failed")
            return invalidated_generation

    @staticmethod
    async def _finish_io(operation: Coroutine[Any, Any, None]) -> None:
        # Cancellation may stop the await, but the atomic filesystem operation
        # must finish before releasing the writer lock or shutting down.
        task = asyncio.create_task(operation)
        try:
            await asyncio.shield(task)
        except asyncio.CancelledError:
            await asyncio.gather(task, return_exceptions=True)
            raise
