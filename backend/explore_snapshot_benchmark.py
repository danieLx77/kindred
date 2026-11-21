"""Measure first-page discovery with the same simulated transport on both revisions."""

import asyncio
import gc
import json
import logging
import os
import sys
import tempfile
import tracemalloc
from collections import Counter
from contextlib import asynccontextmanager
from importlib.util import find_spec
from pathlib import Path
from statistics import median
from time import perf_counter, time
from unittest.mock import patch

import httpx
import uvloop

import main
from discovery_cache_benchmark import Upstream
from integrations.globalgiving import GlobalGivingProjectProvider


class Mock(Upstream):
    def __init__(self):
        super().__init__(0.075)
        self.wait = None
        self.entered = asyncio.Event()
        self.unavailable = False

    async def __call__(self, request):
        self.entered.set()
        if self.wait is not None:
            await self.wait.wait()
        if self.unavailable:
            self.calls += 1
            await asyncio.sleep(self.delay)
            return httpx.Response(503)
        return await super().__call__(request)


class CacheEvents(logging.Handler):
    def __init__(self) -> None:
        super().__init__()
        self.counts: Counter[str] = Counter()

    def emit(self, record: logging.LogRecord) -> None:
        message = record.getMessage()
        if " event=" in message:
            source, event = message.split()[:2]
            self.counts[f"{source}.{event.removeprefix('event=')}"] += 1


async def main_bench():
    baseline = "--before" in sys.argv
    if baseline and find_spec("integrations.globalgiving.explore_snapshot") is not None:
        raise SystemExit("Run --before from the Phase 1 checkout.")
    events = CacheEvents()
    for name in ("projects.discovery_cache", "integrations.globalgiving.discovery"):
        logger = logging.getLogger(name)
        logger.addHandler(events)
        logger.setLevel(logging.DEBUG)
    results = {}
    file_bytes = []
    memory = []
    refresh_ms = []
    for scenario in (
        "cold",
        "restart",
        "available",
        "warm",
        "updating",
        "slow",
        "down",
        "expired",
        "next",
    ):
        rows = []
        sampled_events: Counter[str] = Counter()
        for attempt in range(8):
            with tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "first.json"
                upstream = Mock()

                def provider(**kwargs):
                    return GlobalGivingProjectProvider(
                        **kwargs, transport=httpx.MockTransport(upstream)
                    )

                @asynccontextmanager
                async def client():
                    app = main.create_app()
                    async with (
                        app.router.lifespan_context(app),
                        httpx.AsyncClient(
                            transport=httpx.ASGITransport(app=app),
                            base_url="http://test",
                        ) as session,
                    ):
                        yield session

                async def get(session, cursor=None):
                    params = {"page_size": 9}
                    if cursor:
                        params["cursor"] = cursor
                    return await session.get("/api/v1/projects", params=params)

                with (
                    patch.object(main, "GlobalGivingProjectProvider", provider),
                    patch.dict(
                        os.environ,
                        {
                            "GLOBALGIVING_API_KEY": "fixture",
                            "KINDRED_EXPLORE_SNAPSHOT_PATH": str(path),
                            "KINDRED_EXPLORE_SNAPSHOT_REFRESH_SECONDS": "600",
                        },
                    ),
                ):
                    if scenario not in ("cold", "warm", "available"):
                        async with client() as seed:
                            assert (await get(seed)).is_success
                        if not baseline:
                            data = json.loads(path.read_text())
                            if scenario in ("updating", "expired"):
                                data["generated_at"] = time() - (
                                    601 if scenario == "updating" else 1801
                                )
                                path.write_text(json.dumps(data))
                            if scenario == "restart":
                                file_bytes.append(path.stat().st_size)
                    if scenario == "updating":
                        upstream.wait = asyncio.Event()
                        upstream.entered.clear()
                    if scenario == "slow":
                        upstream.delay = 0.350
                    upstream.unavailable = scenario == "down"
                    before = upstream.calls
                    async with client() as session:
                        if scenario == "available" and not baseline:
                            update_start = perf_counter()

                            async def wait_for_snapshot():
                                while not path.exists():
                                    await asyncio.sleep(0.001)

                            await asyncio.wait_for(wait_for_snapshot(), 3)
                            if attempt:
                                refresh_ms.append(
                                    round((perf_counter() - update_start) * 1000, 2)
                                )
                            before = upstream.calls
                        if scenario == "warm":
                            assert (await get(session)).is_success
                            before = upstream.calls
                        concurrent = None
                        if scenario == "updating":
                            if baseline:
                                concurrent = asyncio.create_task(get(session))
                            await upstream.entered.wait()
                            if baseline:
                                asyncio.get_running_loop().call_later(
                                    0.075, upstream.wait.set
                                )
                        events.counts.clear()
                        start = perf_counter()
                        response = await get(session)
                        first_ms = (perf_counter() - start) * 1000
                        if scenario == "next":
                            second = await get(
                                session, response.json()["pagination"]["next_cursor"]
                            )
                            assert [
                                int(p["id"]) for p in second.json()["items"]
                            ] == list(range(10, 19))
                        elapsed = (perf_counter() - start) * 1000
                        calls = upstream.calls - before
                        assert response.status_code == (
                            503 if baseline and scenario == "down" else 200
                        )
                        if response.is_success:
                            assert [
                                int(p["id"]) for p in response.json()["items"]
                            ] == list(range(1, 10))
                        if attempt:
                            rows.append((round(elapsed, 2), calls, round(first_ms, 2)))
                            sampled_events.update(events.counts)
                        if concurrent is not None:
                            assert (await concurrent).is_success
                    if upstream.wait is not None:
                        upstream.wait.set()
        values, calls, first = zip(*rows)
        results[scenario] = {
            "interval": [min(values), median(values), max(values)],
            "calls": sorted(set(calls)),
            "first_ms": median(first),
            "cache_events_in_seven_samples": dict(sampled_events),
        }
    if not baseline:
        from integrations.globalgiving import explore_snapshot

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "memory.json"
            body = {
                "version": 1,
                "provider": "globalgiving",
                "generated_at": time(),
                "has_more": True,
                "items": [
                    {
                        "id": str(i),
                        "title": f"Projeto {i}",
                        "summary": "Resumo " * 100,
                        "image_url": None,
                        "theme": None,
                        "country": None,
                        "organization": None,
                    }
                    for i in range(1, 10)
                ],
            }
            path.write_text(json.dumps(body))
            warmup = explore_snapshot.ExploreSnapshot(path, 600)
            warmup.load()
            for _ in range(7):
                gc.collect()
                tracemalloc.start()
                extra = explore_snapshot.ExploreSnapshot(path, 600)
                extra.load()
                memory.append(tracemalloc.get_traced_memory()[0])
                tracemalloc.stop()
    print(
        json.dumps(
            {
                "scenarios": results,
                "snapshot_bytes": sorted(set(file_bytes)),
                "retained_bytes": memory,
                "refresh_ms": refresh_ms,
            }
        )
    )


if __name__ == "__main__":
    uvloop.run(main_bench())
