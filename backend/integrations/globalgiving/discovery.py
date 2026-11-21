"""Discovery half of ProjectProvider. No detail lookup or public API here."""

import asyncio
import base64
import hashlib
import hmac
import json
import logging
import os
import re
import secrets
from dataclasses import replace
from time import perf_counter, time
from types import TracebackType
from typing import TypeVar
from urllib.parse import urlsplit

import httpx

from projects.discovery_cache import DiscoveryCache, DiscoveryCacheSettings
from projects.errors import InvalidDiscoveryContinuation, ProviderError
from projects.models import (
    Continuation,
    DiscoveryQuery,
    DiscoveryResult,
    ProjectSummary,
)

from .explore_snapshot import EXPLORE_QUERY, ExploreSnapshot, prefix_digest
from .http import GlobalGivingHTTP
from .mapping import (
    card_image_variants,
    integer,
    invalid_response,
    object_value,
    summaries,
)

logger = logging.getLogger(__name__)
_IMAGE_LOOKUP_TIMEOUT = 2.0

_CacheKey = tuple[DiscoveryQuery, int | None, int, int | None, str | None]
_EXPLORE_KEY: _CacheKey = (EXPLORE_QUERY, None, 0, None, None)

_DiscoveryAdapterT = TypeVar("_DiscoveryAdapterT", bound="GlobalGivingDiscoveryAdapter")


class GlobalGivingDiscoveryAdapter:
    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str = "https://api.globalgiving.org/api/public/",
        timeout: float = 10.0,
        transport: httpx.AsyncBaseTransport | None = None,
        cache_settings: DiscoveryCacheSettings | None = None,
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
        self._cache = (
            DiscoveryCache[_CacheKey](cache_settings)
            if cache_settings is not None
            else None
        )

        self._snapshot: ExploreSnapshot | None = None
        self._refresh_task: asyncio.Task[None] | None = None

    def start_explore_snapshot(self, snapshot: ExploreSnapshot) -> None:
        if self._snapshot is not None or self._cache is None:
            raise RuntimeError("Explore snapshot requires a single discovery cache")
        snapshot.load()
        self._snapshot = snapshot
        self._refresh_task = asyncio.create_task(self._refresh_explore(snapshot))

    async def _refresh_explore(self, snapshot: ExploreSnapshot) -> None:
        await asyncio.sleep(snapshot.initial_delay())
        while True:
            started = perf_counter()
            try:
                if self._cache is not None:
                    self._cache.discard(_EXPLORE_KEY)
                await self._resolve_page(_EXPLORE_KEY, "")
            except ProviderError as error:
                logger.warning(
                    "explore_snapshot event=refresh_failed reason=%s",
                    error.reason.value,
                )
            finally:
                logger.debug(
                    "explore_snapshot event=refresh_finished duration_ms=%.3f",
                    (perf_counter() - started) * 1000,
                )
            await asyncio.sleep(snapshot.refresh_seconds)

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
        position, skip, hint, prefix = (0 if searching else None), 0, None, None
        if continuation is not None:
            position, skip, hint, prefix = self._decode(continuation, query)
        elif self._snapshot is not None and query == EXPLORE_QUERY:
            page = self._snapshot.current()
            if page is not None:
                items = page.summaries()
                next_page = (
                    self._encode(query, None, len(items), prefix=prefix_digest(items))
                    if page.has_more
                    else None
                )
                logger.debug(
                    "explore_snapshot event=hit age_seconds=%.3f",
                    time() - page.generated_at,
                )
                return DiscoveryResult(items, next_page)
            logger.debug("explore_snapshot event=miss")

        return await self._resolve_page((query, position, skip, hint, prefix), text)

    async def _resolve_page(self, key: _CacheKey, text: str) -> DiscoveryResult:
        async def load() -> tuple[DiscoveryResult, bool]:
            result, complete = await self._discover_page(key, text)
            if complete and key == _EXPLORE_KEY and self._snapshot is not None:
                await self._snapshot.publish(result)
            return result, complete

        if self._cache is None:
            result, _ = await load()
            return result
        return await self._cache.resolve(key, load)

    async def _discover_page(
        self, key: _CacheKey, text: str
    ) -> tuple[DiscoveryResult, bool]:
        query, position, skip, hint, prefix = key
        if text:
            assert position is not None
            data = object_value(
                await self._http.get(
                    "services/search/projects",
                    {"q": text, "start": str(position)},
                    retry_timeout=True,
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
            items, next_page = await self._listing_page(
                query, position, skip, hint, prefix
            )
        items, complete = await self._enrich_card_images(items)
        return DiscoveryResult(items, next_page), complete

    async def _listing_page(
        self,
        query: DiscoveryQuery,
        position: int | None,
        skip: int,
        hint: int | None,
        prefix: str | None,
    ) -> tuple[tuple[ProjectSummary, ...], Continuation | None]:
        # The previous response already reported this position. Start the two
        # reads together, but use the second only if the fresh first batch agrees.
        following = (
            asyncio.create_task(self._listing_batch(hint)) if hint is not None else None
        )
        try:
            projects, next_position = await self._listing_batch(position)
            if prefix is not None:
                if len(projects) < skip or prefix_digest(projects[:skip]) != prefix:
                    if self._snapshot is not None and await self._snapshot.discard(
                        prefix
                    ):
                        if self._cache is not None:
                            self._cache.discard(_EXPLORE_KEY)
                    raise InvalidDiscoveryContinuation
            elif skip and skip >= len(projects):
                raise invalid_response()
            preceding = (
                {project.id for project in projects[:skip]}
                if prefix is not None
                else set()
            )
            items = projects[skip : skip + query.page_size]
            consumed = skip + len(items)
            if skip and len(items) < query.page_size and next_position is not None:
                # Finish a page that starts with the remainder of a split batch.
                position = next_position
                if following is not None and position == hint:
                    projects, next_position = await following
                else:
                    if following is not None:
                        following.cancel()
                    projects, next_position = await self._listing_batch(position)
                consumed = min(query.page_size - len(items), len(projects))
                items += projects[:consumed]
                if len({item.id for item in items}) != len(items):
                    raise invalid_response()

            if any(item.id in preceding for item in items):
                raise invalid_response()

            next_page = None
            if consumed < len(projects):
                next_hint = (
                    next_position
                    if len(projects) - consumed < query.page_size
                    else None
                )
                next_page = self._encode(query, position, consumed, next_hint)
            elif next_position is not None:
                next_page = self._encode(query, next_position, 0)
            return items, next_page
        finally:
            if following is not None:
                following.cancel()
                await asyncio.gather(following, return_exceptions=True)

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
    ) -> tuple[tuple[ProjectSummary, ...], bool]:
        pending = [project.id for project in items if _uses_default_image(project)]
        if not pending:
            return items, True

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
            return items, False

        return tuple(
            replace(project, image_url=images[project.id])
            if project.id in pending and project.id in images
            else project
            for project in items
        ), True

    @staticmethod
    def _query_key(query: DiscoveryQuery) -> str:
        raw = json.dumps([query.text, query.theme, query.country, query.page_size])
        return hashlib.sha256(raw.encode()).hexdigest()

    def _encode(
        self,
        query: DiscoveryQuery,
        position: int | None,
        skip: int,
        hint: int | None = None,
        *,
        prefix: str | None = None,
    ) -> Continuation:
        payload = json.dumps(
            [self._query_key(query), position, skip, hint, prefix]
        ).encode()
        signature = hmac.digest(self._signing_key, payload, "sha256")
        return Continuation(base64.urlsafe_b64encode(signature + payload).decode())

    def _decode(
        self, continuation: Continuation, query: DiscoveryQuery
    ) -> tuple[int | None, int, int | None, str | None]:
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
            key, position, skip, hint, prefix = json.loads(payload)
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
            if hint is not None and (
                searching
                or not skip
                or type(hint) is not int
                or hint <= (position or 0)
            ):
                raise ValueError
            if prefix is not None and (
                query != EXPLORE_QUERY
                or position is not None
                or skip != query.page_size
                or hint is not None
                or not isinstance(prefix, str)
                or not re.fullmatch(r"[0-9a-f]{64}", prefix)
            ):
                raise ValueError
            return position, skip, hint, prefix
        except (ValueError, TypeError):
            raise ValueError(
                "Invalid discovery continuation for this query/provider"
            ) from None

    async def aclose(self) -> None:
        try:
            if self._refresh_task is not None:
                self._refresh_task.cancel()
                await asyncio.gather(self._refresh_task, return_exceptions=True)
            if self._cache is not None:
                await self._cache.aclose()
        finally:
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
