import asyncio

import pytest

from projects import discovery_cache
from projects.discovery_cache import DiscoveryCache, DiscoveryCacheSettings
from projects.errors import ProviderError, ProviderFailure
from projects.models import DiscoveryResult, ProjectSummary


@pytest.mark.parametrize("ttl", ["0", "-1", "nan", "inf", "invalid"])
def test_invalid_ttl(monkeypatch, ttl):
    monkeypatch.setenv("KINDRED_DISCOVERY_CACHE_TTL_SECONDS", ttl)
    with pytest.raises(ValueError, match="cache configuration|TTL_SECONDS"):
        DiscoveryCacheSettings.from_env()


@pytest.mark.parametrize("capacity", ["0", "-1", "1.5", "invalid"])
def test_invalid_capacity(monkeypatch, capacity):
    monkeypatch.setenv("KINDRED_DISCOVERY_CACHE_MAX_ENTRIES", capacity)
    with pytest.raises(ValueError, match="cache configuration|MAX_ENTRIES"):
        DiscoveryCacheSettings.from_env()


def test_configuration_defaults(monkeypatch):
    monkeypatch.delenv("KINDRED_DISCOVERY_CACHE_TTL_SECONDS", raising=False)
    monkeypatch.delenv("KINDRED_DISCOVERY_CACHE_MAX_ENTRIES", raising=False)
    settings = DiscoveryCacheSettings.from_env()
    assert (settings.ttl_seconds, settings.max_entries) == (600, 256)


async def test_ttl_lru_and_empty_result(monkeypatch, caplog):
    now = 100.0
    monkeypatch.setattr(discovery_cache, "monotonic", lambda: now)
    caplog.set_level("DEBUG", logger=discovery_cache.__name__)
    cache = DiscoveryCache[str](DiscoveryCacheSettings(10, 2))
    loads = 0

    async def load():
        nonlocal loads
        loads += 1
        return DiscoveryResult(), True

    assert await cache.resolve("a", load) == DiscoveryResult()
    await cache.resolve("b", load)
    now = 109.0
    await cache.resolve("a", load)
    await cache.resolve("c", load)
    assert loads == 3
    now = 110.0
    await cache.resolve("a", load)
    await cache.resolve("a", load)
    assert loads == 4
    assert "evictions=1 expirations=1" in caplog.text
    assert "event=cache_hit" in caplog.text
    await cache.resolve("b", load)  # A was used more recently than B.
    assert loads == 5
    await cache.aclose()


async def test_byte_budget_evicts_lru_and_skips_oversize(monkeypatch):
    monkeypatch.setattr(discovery_cache, "_MAX_BYTES", 4096)
    cache = DiscoveryCache[str](DiscoveryCacheSettings())
    loads = 0

    async def medium():
        nonlocal loads
        loads += 1
        return DiscoveryResult((ProjectSummary("1", summary="x" * 1800),)), True

    await cache.resolve("a", medium)
    await cache.resolve("b", medium)
    await cache.resolve("a", medium)
    assert loads == 3

    async def large():
        nonlocal loads
        loads += 1
        return DiscoveryResult((ProjectSummary("2", summary="x" * 5000),)), True

    await cache.resolve("large", large)
    await cache.resolve("large", large)
    await cache.resolve("a", medium)
    assert loads == 5
    await cache.aclose()


@pytest.mark.parametrize("consumers", [2, 10])
async def test_singleflight_shares_failure_and_allows_retry(consumers):
    cache = DiscoveryCache[str](DiscoveryCacheSettings())
    entered = asyncio.Event()
    release = asyncio.Event()
    attempts = 0

    async def load():
        nonlocal attempts
        attempts += 1
        entered.set()
        await release.wait()
        raise ProviderError(ProviderFailure.TIMEOUT)

    pending = [asyncio.create_task(cache.resolve("a", load)) for _ in range(consumers)]
    await entered.wait()
    release.set()
    errors = await asyncio.gather(*pending, return_exceptions=True)
    assert attempts == 1
    assert all(isinstance(error, ProviderError) for error in errors)
    with pytest.raises(ProviderError):
        await cache.resolve("a", load)
    assert attempts == 2
    await cache.aclose()


async def test_distinct_keys_can_run_in_parallel_and_slots_reopen(monkeypatch):
    monkeypatch.setattr(discovery_cache, "_MAX_IN_FLIGHT", 2)
    cache = DiscoveryCache[str](DiscoveryCacheSettings())
    started: asyncio.Queue[str] = asyncio.Queue()
    release = asyncio.Event()

    async def load(key: str):
        started.put_nowait(key)
        await release.wait()
        return DiscoveryResult((ProjectSummary(key),)), True

    tasks = [
        asyncio.create_task(cache.resolve(key, lambda key=key: load(key)))
        for key in ("a", "b", "c")
    ]
    assert {await started.get(), await started.get()} == {"a", "b"}
    assert started.empty()
    release.set()
    assert [r.items[0].id for r in await asyncio.gather(*tasks)] == ["a", "b", "c"]
    assert await started.get() == "c"
    await cache.aclose()


@pytest.mark.parametrize("cancel_all", [False, True])
async def test_consumers_can_cancel_without_cancelling_the_load(cancel_all):
    cache = DiscoveryCache[str](DiscoveryCacheSettings())
    entered = asyncio.Event()
    release = asyncio.Event()
    completed = asyncio.Event()
    attempts = 0

    async def load():
        nonlocal attempts
        attempts += 1
        entered.set()
        await release.wait()
        completed.set()
        return DiscoveryResult(), True

    first, second = (asyncio.create_task(cache.resolve("a", load)) for _ in range(2))
    await entered.wait()
    cancelled = (first, second) if cancel_all else (first,)
    for task in cancelled:
        task.cancel()
    for task in cancelled:
        with pytest.raises(asyncio.CancelledError):
            await task

    release.set()
    await completed.wait()
    if not cancel_all:
        assert await second == DiscoveryResult()
    assert await cache.resolve("a", load) == DiscoveryResult()
    assert attempts == 1
    await cache.aclose()


async def test_shutdown_cancels_and_drains_pending_operations():
    cache = DiscoveryCache[str](DiscoveryCacheSettings())
    entered = asyncio.Event()
    stopped = asyncio.Event()

    async def load():
        try:
            entered.set()
            await asyncio.Future()
            raise AssertionError("shutdown should cancel this operation")
        finally:
            stopped.set()

    consumer = asyncio.create_task(cache.resolve("a", load))
    await entered.wait()
    await cache.aclose()
    assert stopped.is_set()
    with pytest.raises(asyncio.CancelledError):
        await consumer
    with pytest.raises(RuntimeError, match="cache is closed"):
        await cache.resolve("a", load)
