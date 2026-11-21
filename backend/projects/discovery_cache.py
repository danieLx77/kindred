"""Bounded, process-local cache for validated discovery results."""

import asyncio
import logging
import math
import os
from collections import OrderedDict
from collections.abc import Awaitable, Callable, Hashable
from dataclasses import dataclass
from sys import getsizeof
from time import monotonic, perf_counter
from typing import Generic, TypeVar

from projects.models import DiscoveryResult

logger = logging.getLogger(__name__)

_MAX_BYTES = 16 * 1024 * 1024
_MAX_IN_FLIGHT = 256
_Key = TypeVar("_Key", bound=Hashable)


@dataclass(frozen=True)
class DiscoveryCacheSettings:
    ttl_seconds: float = 600
    max_entries: int = 256

    def __post_init__(self) -> None:
        if not math.isfinite(self.ttl_seconds) or self.ttl_seconds <= 0:
            raise ValueError(
                "KINDRED_DISCOVERY_CACHE_TTL_SECONDS must be finite and positive"
            )
        if type(self.max_entries) is not int or self.max_entries <= 0:
            raise ValueError(
                "KINDRED_DISCOVERY_CACHE_MAX_ENTRIES must be a positive integer"
            )

    @classmethod
    def from_env(cls) -> "DiscoveryCacheSettings":
        try:
            ttl = float(os.getenv("KINDRED_DISCOVERY_CACHE_TTL_SECONDS", "600"))
            capacity = int(os.getenv("KINDRED_DISCOVERY_CACHE_MAX_ENTRIES", "256"))
        except ValueError:
            raise ValueError("Invalid discovery cache configuration") from None
        return cls(ttl, capacity)


@dataclass(frozen=True)
class _Entry:
    result: DiscoveryResult
    expires_at: float
    size: int


def _result_size(result: DiscoveryResult) -> int:
    # Count the retained Python objects plus a conservative per-entry allowance
    # for the key and cache bookkeeping. Shared values may be counted twice.
    size = 1024 + getsizeof(result.items)
    if result.continuation is not None:
        size += getsizeof(result.continuation.token)
    for project in result.items:
        size += getsizeof(project) + getsizeof(vars(project))
        size += sum(getsizeof(value) for value in vars(project).values())
        if project.organization is not None:
            fields = vars(project.organization)
            size += getsizeof(fields) + sum(
                getsizeof(value) for value in fields.values()
            )
    return size


class DiscoveryCache(Generic[_Key]):
    """Event-loop-owned LRU and single-flight for a single provider lifecycle."""

    def __init__(self, settings: DiscoveryCacheSettings) -> None:
        self._settings = settings
        self._entries: OrderedDict[_Key, _Entry] = OrderedDict()
        self._pending: dict[_Key, asyncio.Task[DiscoveryResult]] = {}
        self._slot_available = asyncio.Event()
        self._slot_available.set()
        self._closed = False
        self._bytes = 0
        self._hits = self._misses = self._evictions = self._expirations = (
            self._joins
        ) = 0

    async def resolve(
        self,
        key: _Key,
        load: Callable[[], Awaitable[tuple[DiscoveryResult, bool]]],
    ) -> DiscoveryResult:
        started = perf_counter()
        event = "unavailable"
        try:
            while not self._closed:
                # No await between checking state and registering an operation.
                entry = self._entries.get(key)
                if entry is not None:
                    if entry.expires_at > monotonic():
                        self._entries.move_to_end(key)
                        self._hits += 1
                        event = "cache_hit"
                        return entry.result
                    self._bytes -= self._entries.pop(key).size
                    self._expirations += 1

                task = self._pending.get(key)
                if task is not None:
                    self._joins += 1
                    event = "singleflight_join"
                    return await asyncio.shield(task)

                if len(self._pending) < _MAX_IN_FLIGHT:
                    task = asyncio.create_task(self._load(key, load))
                    task.add_done_callback(self._consume_exception)
                    self._pending[key] = task
                    if len(self._pending) == _MAX_IN_FLIGHT:
                        self._slot_available.clear()
                    self._misses += 1
                    event = "cache_miss"
                    return await asyncio.shield(task)

                await self._slot_available.wait()
            raise RuntimeError("Discovery cache is closed")
        finally:
            logger.debug(
                "discovery_cache event=%s resolution_ms=%.3f hits=%d misses=%d "
                "evictions=%d expirations=%d joins=%d entries=%d in_flight=%d "
                "estimated_bytes=%d provider_operations_avoided=%d",
                event,
                (perf_counter() - started) * 1000,
                self._hits,
                self._misses,
                self._evictions,
                self._expirations,
                self._joins,
                len(self._entries),
                len(self._pending),
                self._bytes,
                self._hits + self._joins,
            )

    async def _load(
        self,
        key: _Key,
        load: Callable[[], Awaitable[tuple[DiscoveryResult, bool]]],
    ) -> DiscoveryResult:
        try:
            result, complete = await load()
            if complete and not self._closed:
                self._store(key, result)
            return result
        finally:
            self._pending.pop(key, None)
            self._slot_available.set()

    def _store(self, key: _Key, result: DiscoveryResult) -> None:
        size = _result_size(result)
        if size > _MAX_BYTES:
            return
        self._entries[key] = _Entry(
            result, monotonic() + self._settings.ttl_seconds, size
        )
        self._bytes += size
        while (
            len(self._entries) > self._settings.max_entries or self._bytes > _MAX_BYTES
        ):
            _, removed = self._entries.popitem(last=False)
            self._bytes -= removed.size
            self._evictions += 1

    @staticmethod
    def _consume_exception(task: asyncio.Task[DiscoveryResult]) -> None:
        # A shared load may fail after every HTTP consumer has disconnected.
        if not task.cancelled():
            task.exception()

    async def aclose(self) -> None:
        self._closed = True
        self._entries.clear()
        self._bytes = 0
        self._slot_available.set()
        pending = tuple(self._pending.values())
        for task in pending:
            task.cancel()
        await asyncio.gather(*pending, return_exceptions=True)
        # A task cancelled before its first instruction cannot run _load's finally.
        self._pending.clear()
