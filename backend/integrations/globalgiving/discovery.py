"""Discovery half of ProjectProvider. No detail lookup or public API here."""

import asyncio
import base64
import hashlib
import hmac
import json
import os
import secrets
from dataclasses import replace
from types import TracebackType
from typing import TypeVar
from urllib.parse import urlsplit

import httpx

from projects.errors import ProviderError
from projects.models import (
    Continuation,
    DiscoveryQuery,
    DiscoveryResult,
    ProjectSummary,
)

from .http import GlobalGivingHTTP
from .mapping import (
    card_image_variants,
    integer,
    invalid_response,
    object_value,
    summaries,
)

_IMAGE_LOOKUP_TIMEOUT = 2.0

_DiscoveryAdapterT = TypeVar("_DiscoveryAdapterT", bound="GlobalGivingDiscoveryAdapter")


class GlobalGivingDiscoveryAdapter:
    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str = "https://api.globalgiving.org/api/public/",
        timeout: float = 10.0,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        if api_key is None:
            api_key = os.getenv("GLOBALGIVING_API_KEY", "")
        api_key = api_key.strip()
        if not api_key:
            raise ValueError("GLOBALGIVING_API_KEY must be configured in the backend")
        self._http = GlobalGivingHTTP(
            api_key, base_url=base_url, timeout=timeout, transport=transport
        )
        self._signing_key = secrets.token_bytes(32)

    async def discover(
        self,
        query: DiscoveryQuery = DiscoveryQuery(),
        continuation: Continuation | None = None,
    ) -> DiscoveryResult:
        if query.theme is not None or query.country is not None:
            raise ValueError("GlobalGiving discovery filters are not supported in M1")
        if type(query.page_size) is not int or query.page_size < 1:
            raise ValueError("page_size must be a positive integer")
        if query.text is not None and not isinstance(query.text, str):
            raise ValueError("Discovery text must be a string")
        text = (query.text or "").strip()
        searching = bool(text)
        position, skip = (0 if searching else None), 0
        if continuation is not None:
            position, skip = self._decode(continuation, query)

        if searching:
            assert position is not None
            data = object_value(
                await self._http.get(
                    "services/search/projects", {"q": text, "start": str(position)}
                )
            )
            response = object_value(object_value(data.get("search")).get("response"))
            if "@start" in response and integer(response["@start"]) != position:
                raise invalid_response()
            raw_projects = response.get("projects")
            container = {} if raw_projects is None else object_value(raw_projects)
            if "project" not in container and container:
                raise invalid_response()
            items = summaries(container)[: query.page_size]
            next_page = self._encode(query, position + len(items), 0) if items else None
        else:
            projects, next_position = await self._listing_batch(position)
            if skip and skip >= len(projects):
                raise invalid_response()
            items = projects[skip : skip + query.page_size]
            consumed = skip + len(items)
            if skip and len(items) < query.page_size and next_position is not None:
                # Finish a page that starts with the remainder of a split batch.
                position = next_position
                projects, next_position = await self._listing_batch(position)
                consumed = min(query.page_size - len(items), len(projects))
                items += projects[:consumed]

            next_page = None
            if consumed < len(projects):
                next_page = self._encode(query, position, consumed)
            elif next_position is not None:
                next_page = self._encode(query, next_position, 0)
        return DiscoveryResult(await self._enrich_card_images(items), next_page)

    async def _listing_batch(
        self, position: int | None
    ) -> tuple[tuple[ProjectSummary, ...], int | None]:
        params = {"nextProjectId": str(position)} if position is not None else {}
        data = object_value(
            await self._http.get("projectservice/all/projects/summary", params)
        )
        container = object_value(data.get("projects"))
        if "project" not in container and set(container) - {
            "hasNext",
            "nextProjectId",
            "@numberFound",
            "numberFound",
        }:
            raise invalid_response()
        flag = container.get("hasNext", False)
        if type(flag) is not bool and flag not in ("true", "false"):
            raise invalid_response()
        projects = summaries(container)
        next_position = None
        if flag in (True, "true"):
            next_position = integer(container.get("nextProjectId"), minimum=1)
            if not projects or (position is not None and next_position <= position):
                raise invalid_response()
        return projects, next_position

    async def _enrich_card_images(
        self, items: tuple[ProjectSummary, ...]
    ) -> tuple[ProjectSummary, ...]:
        pending = [project.id for project in items if _uses_default_image(project)]
        if not pending:
            return items

        # The full-project collection supplies official variants for up to 10 IDs.
        # This optional request must not delay discovery by another full API timeout.
        try:
            payload = await asyncio.wait_for(
                self._http.get(
                    "projectservice/projects/collection/ids",
                    {"projectIds": ",".join(pending)},
                ),
                timeout=_IMAGE_LOOKUP_TIMEOUT,
            )
            images = card_image_variants(payload)
        except (ProviderError, asyncio.TimeoutError):
            return items

        return tuple(
            replace(project, image_url=images[project.id])
            if project.id in pending and project.id in images
            else project
            for project in items
        )

    @staticmethod
    def _query_key(query: DiscoveryQuery) -> str:
        raw = json.dumps([query.text, query.theme, query.country, query.page_size])
        return hashlib.sha256(raw.encode()).hexdigest()

    def _encode(
        self, query: DiscoveryQuery, position: int | None, skip: int
    ) -> Continuation:
        payload = json.dumps([self._query_key(query), position, skip]).encode()
        signature = hmac.digest(self._signing_key, payload, "sha256")
        return Continuation(base64.urlsafe_b64encode(signature + payload).decode())

    def _decode(
        self, continuation: Continuation, query: DiscoveryQuery
    ) -> tuple[int | None, int]:
        try:
            if (
                not isinstance(continuation.token, str)
                or len(continuation.token) > 4096
            ):
                raise ValueError
            decoded = base64.b64decode(
                continuation.token, altchars=b"-_", validate=True
            )
            signature, payload = decoded[:32], decoded[32:]
            if not hmac.compare_digest(
                signature, hmac.digest(self._signing_key, payload, "sha256")
            ):
                raise ValueError
            key, position, skip = json.loads(payload)
            if key != self._query_key(query):
                raise ValueError
            searching = bool((query.text or "").strip())
            if position is not None and (type(position) is not int or position < 0):
                raise ValueError
            if searching and (position is None or skip != 0):
                raise ValueError
            if not searching and position == 0:
                raise ValueError
            if type(skip) is not int or not 0 <= skip < 10:
                raise ValueError
            return position, skip
        except (ValueError, TypeError):
            raise ValueError(
                "Invalid discovery continuation for this query/provider"
            ) from None

    async def aclose(self) -> None:
        await self._http.aclose()

    async def __aenter__(self: _DiscoveryAdapterT) -> _DiscoveryAdapterT:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        await self.aclose()


def _uses_default_image(project: ProjectSummary) -> bool:
    if project.image_url is None:
        return False
    url = urlsplit(project.image_url)
    return url.hostname in {"www.globalgiving.org", "globalgiving.org"} and (
        url.path == f"/pfil/{project.id}/pict.jpg"
    )
