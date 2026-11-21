"""Benchmark the FastAPI discovery route with a simulated GlobalGiving transport."""

import argparse
import asyncio
import gc
import importlib
import importlib.util
import json
import tracemalloc
from collections import defaultdict
from statistics import median
from time import perf_counter
from unittest.mock import patch

import httpx

import main
from integrations.globalgiving import GlobalGivingProjectProvider

PATH = "/api/v1/projects"


def project(project_id: int) -> dict:
    return {
        "id": project_id,
        "title": f"Projeto {project_id}",
        "summary": f"Resumo de demonstração do projeto {project_id}. " * 18,
        "imageLink": f"https://www.globalgiving.org/pfil/{project_id}/pict.jpg",
    }


class Upstream:
    def __init__(self, delay: float) -> None:
        self.delay = delay
        self.calls = 0
        self.fail = False

    async def __call__(self, request: httpx.Request) -> httpx.Response:
        self.calls += 1
        if self.delay:
            await asyncio.sleep(self.delay)
        if self.fail:
            raise httpx.ReadTimeout("simulated", request=request)
        params, path = request.url.params, request.url.path
        if path.endswith("/collection/ids"):
            images = [
                {
                    "id": int(value),
                    "image": {
                        "imagelink": {
                            "@size": "large",
                            "url": f"https://img.example.org/{value}.jpg",
                        }
                    },
                }
                for value in params["projectIds"].split(",")
            ]
            body = {"projects": {"project": images}}
        elif path.endswith("/search/projects"):
            start = int(params["start"])
            body = {
                "search": {
                    "response": {
                        "@start": start,
                        "projects": {
                            "project": [
                                project(i) for i in range(101, 132)[start : start + 10]
                            ]
                        },
                    }
                }
            }
        else:
            start = int(params.get("nextProjectId", "1"))
            batch = {"project": [project(i) for i in range(start, min(start + 10, 32))]}
            if start + 10 < 32:
                batch.update(hasNext=True, nextProjectId=start + 10)
            body = {"projects": batch}
        return httpx.Response(200, json=body)


async def run(baseline: bool) -> None:
    if baseline and importlib.util.find_spec("projects.discovery_cache") is not None:
        raise SystemExit("Run --baseline from a checkout before the discovery cache.")
    rows = defaultdict(list)
    clock = [0.0]
    upstream = Upstream(0.075)

    def provider(**kwargs):
        return GlobalGivingProjectProvider(
            **kwargs, transport=httpx.MockTransport(upstream)
        )

    with (
        patch.object(main, "GlobalGivingProjectProvider", provider),
        patch.object(main, "_globalgiving_api_key", return_value="benchmark-fixture"),
        patch.dict(
            "os.environ",
            {
                "KINDRED_DISCOVERY_CACHE_TTL_SECONDS": "600",
                "KINDRED_DISCOVERY_CACHE_MAX_ENTRIES": "256",
            },
        ),
    ):
        if not baseline:
            cache_module = importlib.import_module("projects.discovery_cache")
            patcher = patch.object(cache_module, "monotonic", lambda: clock[0])
            patcher.start()
        try:
            for iteration in range(8):
                for scenario in (
                    "frio",
                    "quente",
                    "concorrência",
                    "busca",
                    "página",
                    "expiração",
                    "falha",
                ):
                    app = main.create_app()
                    async with (
                        app.router.lifespan_context(app),
                        httpx.AsyncClient(
                            transport=httpx.ASGITransport(app=app),
                            base_url="http://test",
                        ) as one,
                        httpx.AsyncClient(
                            transport=httpx.ASGITransport(app=app),
                            base_url="http://test",
                        ) as two,
                    ):
                        params = {"page_size": "9"}
                        if scenario == "busca":
                            params["q"] = "água"
                        if scenario in {"quente", "busca", "página", "expiração"}:
                            first = (await one.get(PATH, params=params)).json()
                            if scenario == "página":
                                params["cursor"] = first["pagination"]["next_cursor"]
                                second = (await one.get(PATH, params=params)).json()
                                assert [item["id"] for item in second["items"]] == [
                                    str(i) for i in range(10, 19)
                                ]
                                assert (
                                    await one.get(PATH, params={"page_size": "9"})
                                ).is_success
                            if scenario == "expiração":
                                clock[0] += 601
                        count = upstream.calls
                        upstream.fail = scenario == "falha"
                        start = perf_counter()
                        if scenario == "concorrência":
                            responses = await asyncio.gather(
                                *(
                                    client.get(PATH, params=params)
                                    for client in [one, two] * 5
                                )
                            )
                        else:
                            responses = [await two.get(PATH, params=params)]
                        elapsed = (perf_counter() - start) * 1000
                        assert all(
                            r.status_code == (504 if upstream.fail else 200)
                            for r in responses
                        )
                        if not upstream.fail:
                            ids = [
                                str(i)
                                for i in (
                                    range(10, 19)
                                    if scenario == "página"
                                    else range(101, 110)
                                    if scenario == "busca"
                                    else range(1, 10)
                                )
                            ]
                            assert all(
                                [item["id"] for item in r.json()["items"]] == ids
                                for r in responses
                            )
                        if iteration:
                            rows[scenario].append((elapsed, upstream.calls - count))
                        if upstream.fail:
                            assert (
                                await two.get(PATH, params=params)
                            ).status_code == 504
                            assert upstream.calls == count + 2
                            upstream.fail = False
                            assert (await two.get(PATH, params=params)).is_success
            upstream.delay = 0
            app = main.create_app()
            async with (
                app.router.lifespan_context(app),
                httpx.AsyncClient(
                    transport=httpx.ASGITransport(app=app), base_url="http://test"
                ) as client,
            ):
                await client.get(PATH, params={"q": "aquecimento", "page_size": 9})
                tracemalloc.start()
                gc.collect()
                initial = tracemalloc.get_traced_memory()[0]
                for i in range(256):
                    response = await client.get(
                        PATH, params={"q": f"consulta {i}", "page_size": 9}
                    )
                    assert response.is_success
                del response
                gc.collect()
                retained = tracemalloc.get_traced_memory()[0] - initial
                tracemalloc.stop()
        finally:
            if not baseline:
                patcher.stop()
    result = {}
    for stage, measurements in rows.items():
        durations, counts = zip(*measurements)
        result[stage] = {
            "ms_min_med_max": [
                round(value, 2)
                for value in (min(durations), median(durations), max(durations))
            ],
            "upstream_calls": sorted(set(counts)),
        }
    print(
        json.dumps(
            {"scenarios": result, "retained_bytes": retained},
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", action="store_true")
    asyncio.run(run(parser.parse_args().baseline))
