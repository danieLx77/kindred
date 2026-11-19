"""Discovery half of ProjectProvider. No detail lookup or public API here."""

import base64
import hashlib
import hmac
import json
import os
import secrets
from types import TracebackType

import httpx

from projects.models import Continuation, DiscoveryQuery, DiscoveryResult

from .http import GlobalGivingHTTP
from .mapping import integer, invalid_response, object_value, summaries


class GlobalGivingDiscoveryAdapter:
    def __init__(
        self,
        *,
        base_url: str = "https://api.globalgiving.org/api/public/",
        timeout: float = 10.0,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        api_key = os.environ.get("GLOBALGIVING_API_KEY", "").strip()
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

        params: dict[str, str] = {}
        if searching:
            path = "services/search/projects"
            params = {"q": text, "start": str(position)}
        else:
            path = "projectservice/all/projects/summary"
            if position is not None:
                params["nextProjectId"] = str(position)
        data = object_value(await self._http.get(path, params))
        next_position = None
        if searching:
            response = object_value(object_value(data.get("search")).get("response"))
            if "@start" in response and integer(response["@start"]) != position:
                raise invalid_response()
            raw_projects = response.get("projects")
            container = {} if raw_projects is None else object_value(raw_projects)
            if "project" not in container and container:
                raise invalid_response()
        else:
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
            if flag in (True, "true"):
                next_position = integer(container.get("nextProjectId"), minimum=1)
                if next_position == position:
                    raise invalid_response()

        projects = summaries(container)
        if skip and skip >= len(projects):
            raise invalid_response()
        if not projects and next_position is not None:
            raise invalid_response()
        items = projects[skip : skip + query.page_size]
        consumed = skip + len(items)
        next_page = None
        if searching and projects:
            assert position is not None
            next_page = self._encode(query, position + len(items), 0)
        elif consumed < len(projects):
            next_page = self._encode(query, position, consumed)
        elif next_position is not None:
            next_page = self._encode(query, next_position, 0)
        return DiscoveryResult(items, next_page)

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

    async def __aenter__(self) -> "GlobalGivingDiscoveryAdapter":
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        await self.aclose()
