"""Owned HTTP client and scoped protection for credential-bearing requests."""

import asyncio
import json
import logging
import math
from contextvars import ContextVar
from types import TracebackType

import httpx

from projects.errors import ProviderError, ProviderFailure

_sensitive_request: ContextVar[bool] = ContextVar("globalgiving_request", default=False)


class _RequestLogFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return not _sensitive_request.get()


# Logger filters do not propagate to children. Cover the HTTPX/HTTPcore loggers
# used by the pinned HTTP stack, including connection and response-header traces.
# ContextVar scopes suppression to these requests, never other concurrent tasks.
for _name in (
    "httpx",
    "httpcore",
    "httpcore.connection",
    "httpcore.connection_pool",
    "httpcore.http11",
    "httpcore.http2",
    "httpcore.proxy",
    "httpcore.http_proxy",
    "httpcore.socks",
):
    logging.getLogger(_name).addFilter(_RequestLogFilter())


class GlobalGivingHTTP:
    def __init__(
        self,
        api_key: str,
        *,
        base_url: str,
        timeout: float,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        try:
            url = httpx.URL(base_url)
            valid = (
                url.scheme == "https"
                and bool(url.host)
                and not url.userinfo
                and not url.query
                and not url.fragment
            )
        except (ValueError, httpx.InvalidURL):
            valid = False
        if not valid:
            raise ValueError("GlobalGiving base URL must be HTTPS without credentials")
        if not math.isfinite(timeout) or timeout <= 0:
            raise ValueError("GlobalGiving timeout must be finite and positive")
        self._api_key = api_key
        self._timeout = timeout
        self._client = httpx.AsyncClient(
            base_url=base_url,
            timeout=httpx.Timeout(timeout),
            headers={"Accept": "application/json"},
            follow_redirects=False,
            trust_env=False,
            transport=transport,
        )

    async def get(self, path: str, params: dict[str, str]) -> object:
        token = _sensitive_request.set(True)
        try:
            return await asyncio.wait_for(self._get(path, params), self._timeout)
        except (asyncio.TimeoutError, httpx.TimeoutException):
            raise ProviderError(ProviderFailure.TIMEOUT) from None
        except httpx.DecodingError:
            raise ProviderError(ProviderFailure.INVALID_RESPONSE) from None
        except httpx.RequestError:
            raise ProviderError(ProviderFailure.NETWORK) from None
        except (ValueError, UnicodeError, RecursionError):
            raise ProviderError(ProviderFailure.INVALID_RESPONSE) from None
        finally:
            _sensitive_request.reset(token)

    async def _get(self, path: str, params: dict[str, str]) -> object:
        async with self._client.stream(
            "GET", path, params={**params, "api_key": self._api_key}
        ) as response:
            status = response.status_code
            if status != 200:
                reason = {
                    400: ProviderFailure.INVALID_REQUEST,
                    401: ProviderFailure.AUTHENTICATION,
                    403: ProviderFailure.AUTHENTICATION,
                    404: ProviderFailure.NOT_FOUND,
                    410: ProviderFailure.UNAVAILABLE,
                    429: ProviderFailure.RATE_LIMITED,
                }.get(status, ProviderFailure.UNAVAILABLE)
                raise ProviderError(reason)
            body = bytearray()
            async for chunk in response.aiter_bytes():
                if len(body) + len(chunk) > 2 * 1024 * 1024:
                    raise ProviderError(ProviderFailure.INVALID_RESPONSE)
                body.extend(chunk)
            # Never propagate decoder messages or provider bodies.
            return json.loads(body)

    async def aclose(self) -> None:
        token = _sensitive_request.set(True)
        try:
            await self._client.aclose()
        finally:
            _sensitive_request.reset(token)

    async def __aenter__(self) -> "GlobalGivingHTTP":
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        await self.aclose()
