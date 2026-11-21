import asyncio
import json
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
import pytest
from fastapi import FastAPI

import main
from integrations.globalgiving import GlobalGivingProjectProvider, explore_snapshot
from projects.models import Continuation

PATH = "/api/v1/projects"
KEY = "discovery-cache-test-credential"


def project(identifier: int, *, image: bool = False) -> dict:
    value = {"id": identifier, "title": f"Projeto {identifier}"}
    if image:
        value["imageLink"] = f"https://www.globalgiving.org/pfil/{identifier}/pict.jpg"
    return value


class GlobalGivingStub:
    def __init__(self) -> None:
        self.calls: list[str] = []
        self.catalog_start = 1
        self.catalog_batch_size = 10
        self.repeat_first_id = False
        self.failure: int | str | None = None
        self.timeout_once = False
        self.image_failure = False
        self.uses_images = False
        self.started = asyncio.Event()
        self.release: asyncio.Event | None = None
        self.closed = 0
        self.cancelled = asyncio.Event()

    async def respond(self, request: httpx.Request) -> httpx.Response:
        path, params = request.url.path, request.url.params
        self.calls.append(path.rsplit("/", 1)[-1])
        assert params["api_key"] == KEY
        self.started.set()
        if self.release is not None:
            try:
                await self.release.wait()
            except asyncio.CancelledError:
                self.cancelled.set()
                raise
        if self.timeout_once or self.failure == "timeout":
            self.timeout_once = False
            raise httpx.ReadTimeout("fixture", request=request)
        if isinstance(self.failure, int):
            return httpx.Response(self.failure)
        if self.failure == "invalid":
            return httpx.Response(200, json={"unexpected": True})
        if path.endswith("/collection/ids"):
            if self.image_failure:
                return httpx.Response(503)
            items = [
                {
                    "id": int(value),
                    "image": {
                        "imagelink": {
                            "@size": "large",
                            "url": "https://img.example.org/card.jpg",
                        }
                    },
                }
                for value in params["projectIds"].split(",")
            ]
            return httpx.Response(200, json={"projects": {"project": items}})
        if path.endswith("/search/projects"):
            start = int(params["start"])
            matches = {
                "Água limpa": range(101, 122),
                "água limpa": range(201, 210),
            }.get(params["q"], range(0))
            items = [
                project(i, image=self.uses_images) for i in matches[start : start + 10]
            ]
            return httpx.Response(
                200,
                json={
                    "search": {
                        "response": {"@start": start, "projects": {"project": items}}
                    }
                },
            )
        start = int(params.get("nextProjectId", str(self.catalog_start)))
        end = start + self.catalog_batch_size
        batch: dict[str, object] = {
            "project": [
                project(i, image=self.uses_images) for i in range(start, min(end, 22))
            ]
        }
        if start > self.catalog_start and self.repeat_first_id:
            batch["project"] = [project(self.catalog_start)]
        if end < 22:
            batch.update(hasNext=True, nextProjectId=end)
        return httpx.Response(200, json={"projects": batch})


@pytest.fixture
def upstream(monkeypatch):
    stub = GlobalGivingStub()

    class Transport(httpx.MockTransport):
        async def aclose(self) -> None:
            if stub.release is not None and not stub.release.is_set():
                assert stub.cancelled.is_set()
            stub.closed += 1

    def factory(**kwargs):
        return GlobalGivingProjectProvider(transport=Transport(stub.respond), **kwargs)

    monkeypatch.setattr(main, "GlobalGivingProjectProvider", factory)
    monkeypatch.setenv("GLOBALGIVING_API_KEY", KEY)
    monkeypatch.setenv("KINDRED_DISCOVERY_CACHE_TTL_SECONDS", "600")
    monkeypatch.setenv("KINDRED_DISCOVERY_CACHE_MAX_ENTRIES", "256")
    return stub


@asynccontextmanager
async def client_for(app: FastAPI) -> AsyncIterator[httpx.AsyncClient]:
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client


@pytest.mark.parametrize("query,first_id", [("", 1), ("Água limpa", 101)])
async def test_pages_shared_across_clients_with_fresh_authenticated_public_cursors(
    upstream, query, first_id
):
    app = main.create_app()
    params = {"q": query, "page_size": "9"}
    async with (
        app.router.lifespan_context(app),
        client_for(app) as one,
        client_for(app) as two,
    ):
        initial = (await one.get(PATH, params=params)).json()
        first_calls = len(upstream.calls)
        same = (
            await two.get(
                PATH, params={**params, "q": f"  {query.replace(' ', '   ')}  "}
            )
        ).json()
        assert initial["items"] == same["items"]
        assert initial["pagination"]["next_cursor"] != same["pagination"]["next_cursor"]
        assert len(upstream.calls) == first_calls

        cursor = initial["pagination"]["next_cursor"]
        second_params = {**params, "cursor": cursor}
        second = (await one.get(PATH, params=second_params)).json()
        second_calls = len(upstream.calls)
        replay = (
            await two.get(
                PATH, params={**params, "cursor": same["pagination"]["next_cursor"]}
            )
        ).json()
        assert replay["items"] == second["items"]
        assert replay["pagination"]["page"] == 2
        assert len(upstream.calls) == second_calls

        for invalid in (
            {**second_params, "cursor": "malformed"},
            {**second_params, "page_size": "8"},
            {**second_params, "q": "different"},
        ):
            response = await two.get(PATH, params=invalid)
            assert response.status_code == 400
            assert response.json() == {"code": "invalid_cursor"}
        assert len(upstream.calls) == second_calls

        third = (
            await one.get(
                PATH, params={**params, "cursor": second["pagination"]["next_cursor"]}
            )
        ).json()
        assert [len(page["items"]) for page in (initial, second, third)] == [9, 9, 3]
        assert third["pagination"]["page"] == 3
        assert [
            int(item["id"])
            for page in (initial, second, third)
            for item in page["items"]
        ] == list(range(first_id, first_id + 21))
        if query:
            end = (
                await two.get(
                    PATH,
                    params={**params, "cursor": third["pagination"]["next_cursor"]},
                )
            ).json()
            assert end["items"] == []
            assert end["pagination"]["next_cursor"] is None
        else:
            assert third["pagination"]["next_cursor"] is None


async def test_search_and_page_size_are_isolated_and_valid_empty_is_cached(upstream):
    app = main.create_app()
    async with app.router.lifespan_context(app), client_for(app) as client:
        for query, size, expected in (
            ("", 2, ["1", "2"]),
            ("", 1, ["1"]),
            ("Água limpa", 2, ["101", "102"]),
            ("água limpa", 2, ["201", "202"]),
            ("missing", 2, []),
        ):
            calls = len(upstream.calls)
            for _ in range(2):
                response = await client.get(
                    PATH, params={"page_size": size, "q": query}
                )
                assert response.status_code == 200
                assert [item["id"] for item in response.json()["items"]] == expected
            assert len(upstream.calls) == calls + 1


async def test_concurrent_http_clients_share_one_operation(upstream, caplog):
    upstream.release = asyncio.Event()
    caplog.set_level(logging.DEBUG)
    app = main.create_app()
    async with (
        app.router.lifespan_context(app),
        client_for(app) as one,
        client_for(app) as two,
    ):
        group = asyncio.gather(
            *(
                client.get(PATH, params={"q": "Água limpa", "page_size": 9})
                for client in [one, two] * 5
            )
        )
        await upstream.started.wait()
        upstream.release.set()
        responses = await group
        assert upstream.calls == ["projects"]
    assert all(response.status_code == 200 for response in responses)
    assert "joins=9" in caplog.text
    assert "provider_operations_avoided=9" in caplog.text
    assert KEY not in caplog.text
    assert "Água limpa" not in caplog.text
    # The ASGI test client logs its own outgoing requests in the same process.
    server_messages = [
        record.getMessage() for record in caplog.records if record.name != "httpx"
    ]
    assert all("%C3%81gua" not in message for message in server_messages)


@pytest.mark.parametrize(
    "failure,code,status",
    [
        ("timeout", "provider_timeout", 504),
        (429, "provider_rate_limited", 503),
        (403, "provider_unavailable", 503),
        ("invalid", "provider_failure", 502),
    ],
)
async def test_upstream_failures_are_mapped_and_retried_by_subsequent_requests(
    upstream, failure, code, status
):
    upstream.failure = failure
    app = main.create_app()
    async with app.router.lifespan_context(app), client_for(app) as client:
        for _ in range(2):
            response = await client.get(PATH)
            assert response.status_code == status
            assert response.json() == {"code": code}
        assert upstream.calls == ["summary", "summary"]
        upstream.failure = None
        assert (await client.get(PATH)).status_code == 200
        assert (await client.get(PATH)).status_code == 200
        assert upstream.calls == ["summary", "summary", "summary"]


async def test_transient_search_timeout_retries_once_and_caches_success(upstream):
    upstream.timeout_once = True
    app = main.create_app()
    async with app.router.lifespan_context(app), client_for(app) as client:
        for _ in range(2):
            response = await client.get(
                PATH, params={"q": "Água limpa", "page_size": 9}
            )
            assert response.status_code == 200
            assert len(response.json()["items"]) == 9
    assert upstream.calls == ["projects", "projects"]


async def test_image_fallback_is_returned_without_caching_failed_enrichment(upstream):
    upstream.uses_images = upstream.image_failure = True
    app = main.create_app()
    async with app.router.lifespan_context(app), client_for(app) as client:
        first = (await client.get(PATH)).json()
        assert first["items"][0]["image_url"].endswith("/pict.jpg")
        upstream.image_failure = False
        second = (await client.get(PATH)).json()
        third = (await client.get(PATH)).json()
        assert second["items"] == third["items"]
        assert third["items"][0]["image_url"] == "https://img.example.org/card.jpg"
    assert upstream.calls == ["summary", "ids", "summary", "ids"]


async def test_lifespan_restart_discards_pages_and_tokens(upstream):
    app = main.create_app()
    async with app.router.lifespan_context(app), client_for(app) as client:
        first = (await client.get(PATH)).json()
    async with app.router.lifespan_context(app), client_for(app) as client:
        assert (await client.get(PATH)).status_code == 200
        invalid = await client.get(
            PATH, params={"cursor": first["pagination"]["next_cursor"]}
        )
        assert invalid.status_code == 400
    assert upstream.calls == ["summary", "summary"]
    assert upstream.closed == 2


async def test_shutdown_drains_shared_request_before_closing_http_client(upstream):
    app = main.create_app()
    upstream.release = asyncio.Event()
    async with client_for(app) as client:
        async with app.router.lifespan_context(app):
            request = asyncio.create_task(client.get(PATH))
            await upstream.started.wait()
            request.cancel()
            with pytest.raises(asyncio.CancelledError):
                await request
        assert upstream.cancelled.is_set()
        assert upstream.closed == 1


async def test_adapter_rejects_invalid_internal_continuation_even_with_warm_page(
    upstream,
):
    app = main.create_app()
    async with app.router.lifespan_context(app), client_for(app) as client:
        first = (await client.get(PATH)).json()
        assert (
            await client.get(
                PATH, params={"cursor": first["pagination"]["next_cursor"]}
            )
        ).is_success
        provider = app.state.projects.provider
        with pytest.raises(ValueError, match="Invalid discovery continuation"):
            await provider.discover(continuation=Continuation("invalid"))
    assert upstream.calls == ["summary", "summary"]


def test_uvicorn_access_logger_omits_search_parameters(caplog):
    with caplog.at_level(logging.INFO, logger="uvicorn.access"):
        logging.getLogger("uvicorn.access").info(
            '%s - "%s %s HTTP/%s" %d',
            "client",
            "GET",
            "/api/v1/projects?q=termo-privado&cursor=cursor-privado",
            "1.1",
            200,
        )
    assert "GET /api/v1/projects HTTP/1.1" in caplog.text
    assert "termo-privado" not in caplog.text
    assert "cursor-privado" not in caplog.text


@pytest.fixture
def snapshot_file(tmp_path, monkeypatch):
    path = tmp_path / "explore.json"
    monkeypatch.setenv("KINDRED_EXPLORE_SNAPSHOT_PATH", str(path))
    monkeypatch.setenv("KINDRED_EXPLORE_SNAPSHOT_REFRESH_SECONDS", "600")
    monkeypatch.setattr(explore_snapshot, "time", lambda: 10_000.0)
    return path


async def fetch_explore(client, cursor=None, **params):
    return await client.get(
        PATH,
        params={"page_size": 9, **({"cursor": cursor} if cursor else {}), **params},
    )


def project_ids(response):
    assert response.status_code == 200
    return [int(item["id"]) for item in response.json()["items"]]


def next_cursor(response):
    return response.json()["pagination"]["next_cursor"]


async def generate_snapshot():
    app = main.create_app()
    async with app.router.lifespan_context(app), client_for(app) as client:
        response = await fetch_explore(client)
        assert project_ids(response)
        return response


@pytest.mark.parametrize("batch_size", [9, 10])
async def test_snapshot_restarts_and_reconstructs_continuation(
    upstream, snapshot_file, batch_size
):
    upstream.catalog_batch_size = batch_size
    previous = await generate_snapshot()
    assert upstream.calls == ["summary"]
    raw = snapshot_file.read_text()
    assert KEY not in raw and next_cursor(previous) not in raw
    assert set(json.loads(raw)) == {
        "version",
        "provider",
        "generated_at",
        "items",
        "has_more",
        "next_position_hint",
    }

    app = main.create_app()
    async with (
        app.router.lifespan_context(app),
        client_for(app) as one,
        client_for(app) as two,
    ):
        first = await fetch_explore(one)
        assert first.json()["items"] == previous.json()["items"]
        assert upstream.calls == ["summary"]
        assert (await fetch_explore(two, next_cursor(previous))).status_code == 400
        cursor = next_cursor(first)
        assert cursor is not None
        assert (await fetch_explore(two, cursor, page_size=10)).status_code == 400
        second = await fetch_explore(two, cursor)
        third = await fetch_explore(one, next_cursor(second))
        assert project_ids(first) == list(range(1, 10))
        assert project_ids(second) == list(range(10, 19))
        assert project_ids(third) == [19, 20, 21]
        assert next_cursor(third) is None
        count = len(upstream.calls)
        assert project_ids(await fetch_explore(one, cursor)) == project_ids(second)
        assert len(upstream.calls) == count


@pytest.mark.parametrize("age", [601, 1800])
async def test_snapshot_refresh_shares_work_with_visitors(
    upstream, snapshot_file, monkeypatch, age
):
    first = await generate_snapshot()
    monkeypatch.setattr(explore_snapshot, "time", lambda: float(10_000 + age))
    upstream.started.clear()
    upstream.release = asyncio.Event()
    app = main.create_app()
    async with (
        app.router.lifespan_context(app),
        client_for(app) as one,
        client_for(app) as two,
    ):
        await upstream.started.wait()
        if age == 601:
            assert project_ids(await fetch_explore(one)) == project_ids(first)
            assert not upstream.release.is_set()
            assert upstream.calls == ["summary", "summary"]
            # This also verifies shutdown drains the refresh and its HTTP operation.
        else:
            responses = asyncio.gather(fetch_explore(one), fetch_explore(two))
            upstream.release.set()
            assert all(
                project_ids(result) == project_ids(first) for result in await responses
            )
            assert upstream.calls == ["summary", "summary"]
            assert json.loads(snapshot_file.read_text())["generated_at"] == 11_800


@pytest.mark.parametrize(
    "bad_snapshot", ["missing", "json", "schema", "future", "oversize"]
)
async def test_bad_snapshot_uses_dynamic_flow(upstream, snapshot_file, bad_snapshot):
    if bad_snapshot == "json":
        snapshot_file.write_text("{")
    elif bad_snapshot == "schema":
        snapshot_file.write_text('{"version":42,"provider":"globalgiving"}')
    elif bad_snapshot == "future":
        await generate_snapshot()
        payload = json.loads(snapshot_file.read_text())
        payload["generated_at"] = 10_001
        snapshot_file.write_text(json.dumps(payload))
    elif bad_snapshot == "oversize":
        snapshot_file.write_bytes(b" " * (128 * 1024 + 1))
    count = len(upstream.calls)
    first = await generate_snapshot()
    assert project_ids(first) == list(range(1, 10))
    assert len(upstream.calls) == count + 1
    assert json.loads(snapshot_file.read_text())["generated_at"] == 10_000


@pytest.mark.parametrize("failure", [503, 429, "timeout"])
async def test_failed_refresh_preserves_last_snapshot(
    upstream, snapshot_file, monkeypatch, caplog, failure
):
    previous = await generate_snapshot()
    before = snapshot_file.read_bytes()
    monkeypatch.setattr(explore_snapshot, "time", lambda: 10_601.0)
    upstream.failure = failure
    upstream.started.clear()
    app = main.create_app()
    async with app.router.lifespan_context(app), client_for(app) as client:
        await upstream.started.wait()
        assert project_ids(await fetch_explore(client)) == project_ids(previous)
        # A continued page is still allowed to report a provider error.
        current = await fetch_explore(client)
        second = await fetch_explore(client, next_cursor(current))
        assert second.status_code == (504 if failure == "timeout" else 503)
        assert "event=refresh_failed" in caplog.text
    assert snapshot_file.read_bytes() == before


async def test_catalog_drift_rejects_snapshot_cursor_and_recovers(
    upstream, snapshot_file
):
    await generate_snapshot()
    upstream.catalog_start = 2
    app = main.create_app()
    async with app.router.lifespan_context(app), client_for(app) as client:
        old = await fetch_explore(client)
        assert project_ids(old) == list(range(1, 10))
        moved = await fetch_explore(client, next_cursor(old))
        assert moved.status_code == 400
        assert moved.json() == {"code": "invalid_cursor"}
        assert not snapshot_file.exists()
        fresh = await fetch_explore(client)
        assert project_ids(fresh) == list(range(2, 11))
        second = await fetch_explore(client, next_cursor(fresh))
        assert project_ids(second) == list(range(11, 20))


async def test_snapshot_applies_only_to_first_nine_catalog_items(
    upstream, snapshot_file
):
    upstream.catalog_start = 17
    await generate_snapshot()
    app = main.create_app()
    async with app.router.lifespan_context(app), client_for(app) as client:
        last = await fetch_explore(client)
        assert project_ids(last) == list(range(17, 22))
        assert next_cursor(last) is None
        assert upstream.calls == ["summary"]
        assert project_ids(await fetch_explore(client, q="Água limpa")) == list(
            range(101, 110)
        )
        assert project_ids(await fetch_explore(client, page_size=2)) == [17, 18]
    assert upstream.calls == ["summary", "projects", "summary"]


async def test_snapshot_continuation_rejects_provider_overlap(upstream, snapshot_file):
    await generate_snapshot()
    upstream.repeat_first_id = True
    app = main.create_app()
    async with app.router.lifespan_context(app), client_for(app) as client:
        first = await fetch_explore(client)
        second = await fetch_explore(client, next_cursor(first))
        assert second.status_code == 502
        assert second.json() == {"code": "provider_failure"}


async def test_unavailable_catalog_without_snapshot_keeps_public_error(
    upstream, snapshot_file
):
    upstream.failure = 503
    app = main.create_app()
    async with app.router.lifespan_context(app), client_for(app) as client:
        response = await fetch_explore(client)
        assert response.status_code == 503
        assert response.json() == {"code": "provider_unavailable"}
    assert not snapshot_file.exists()


@pytest.mark.parametrize("recover_before_refresh_finishes", [False, True])
async def test_invalidation_prevents_in_flight_refresh_from_restoring_snapshot(
    upstream, snapshot_file, monkeypatch, recover_before_refresh_finishes
):
    await generate_snapshot()
    monkeypatch.setattr(explore_snapshot, "time", lambda: 10_601.0)
    refresh_started, release_refresh, refresh_finished = (
        asyncio.Event() for _ in range(3)
    )
    original = upstream.respond
    publish = explore_snapshot.ExploreSnapshot.publish
    first_read = True

    async def respond(request):
        nonlocal first_read
        response = await original(request)
        if first_read and not request.url.params.get("nextProjectId"):
            first_read = False
            refresh_started.set()
            await release_refresh.wait()
        return response

    async def track_publication(snapshot, result, **kwargs):
        await publish(snapshot, result, **kwargs)
        if kwargs["generation"] == 0:
            refresh_finished.set()

    monkeypatch.setattr(upstream, "respond", respond)
    monkeypatch.setattr(explore_snapshot.ExploreSnapshot, "publish", track_publication)
    app = main.create_app()
    async with app.router.lifespan_context(app), client_for(app) as client:
        await asyncio.wait_for(refresh_started.wait(), 2)
        first = await fetch_explore(client)
        assert project_ids(first) == list(range(1, 10))
        upstream.catalog_start = 2
        rejected = await fetch_explore(client, next_cursor(first))
        assert rejected.status_code == 400
        assert rejected.json() == {"code": "invalid_cursor"}
        assert not snapshot_file.exists()

        recovered_file = None
        if recover_before_refresh_finishes:
            first = await asyncio.wait_for(fetch_explore(client), 2)
            assert project_ids(first) == list(range(2, 11))
            recovered_file = snapshot_file.read_bytes()
        release_refresh.set()
        await asyncio.wait_for(refresh_finished.wait(), 2)
        if recovered_file is not None:
            assert snapshot_file.read_bytes() == recovered_file
        else:
            assert not snapshot_file.exists()

        first = await fetch_explore(client)
        assert project_ids(first) == list(range(2, 11))
        assert project_ids(await fetch_explore(client, next_cursor(first))) == list(
            range(11, 20)
        )


async def test_snapshot_position_hint_overlaps_catalog_reads_and_shares_one_flight(
    upstream, snapshot_file, monkeypatch
):
    await generate_snapshot()
    original = upstream.respond
    first_started, next_started, release = (asyncio.Event() for _ in range(3))
    positions = []

    async def respond(request):
        position = request.url.params.get("nextProjectId")
        positions.append(position)
        (first_started if position is None else next_started).set()
        await release.wait()
        return await original(request)

    monkeypatch.setattr(upstream, "respond", respond)
    app = main.create_app()
    async with (
        app.router.lifespan_context(app),
        client_for(app) as one,
        client_for(app) as two,
    ):
        first = await fetch_explore(one)
        cursor = next_cursor(first)
        pending = asyncio.gather(fetch_explore(one, cursor), fetch_explore(two, cursor))
        try:
            await asyncio.wait_for(
                asyncio.gather(first_started.wait(), next_started.wait()), 2
            )
        finally:
            release.set()
        second, shared = await pending
        assert project_ids(second) == project_ids(shared) == list(range(10, 19))
        assert sorted(positions, key=str) == ["11", None]
        assert project_ids(await fetch_explore(one, next_cursor(second))) == [
            19,
            20,
            21,
        ]


@pytest.mark.parametrize("catalog_changed", [False, True])
async def test_snapshot_discards_speculation_when_catalog_or_position_changes(
    upstream, snapshot_file, monkeypatch, caplog, catalog_changed
):
    await generate_snapshot()
    original = upstream.respond
    speculative_started, speculative_cancelled = asyncio.Event(), asyncio.Event()
    positions = []
    upstream.catalog_start = 2 if catalog_changed else 1
    upstream.catalog_batch_size = 9  # Confirms position 10 if the first nine IDs match.

    async def respond(request):
        position = request.url.params.get("nextProjectId")
        positions.append(position)
        if position is None:
            await speculative_started.wait()
        elif position == "11":
            speculative_started.set()
            try:
                await asyncio.Future()
            except asyncio.CancelledError:
                speculative_cancelled.set()
                raise
        return await original(request)

    monkeypatch.setattr(upstream, "respond", respond)
    caplog.set_level(logging.DEBUG, logger="integrations.globalgiving.discovery")
    app = main.create_app()
    async with app.router.lifespan_context(app), client_for(app) as client:
        first = await fetch_explore(client)
        response = await asyncio.wait_for(fetch_explore(client, next_cursor(first)), 2)
        assert speculative_cancelled.is_set()
        assert "speculative_batch_discarded" in caplog.text
        if catalog_changed:
            assert response.status_code == 400
            assert response.json() == {"code": "invalid_cursor"}
            assert not snapshot_file.exists()
            assert sorted(positions, key=str) == ["11", None]
        else:
            assert project_ids(response) == list(range(10, 19))
            assert "position_hint_mismatch" in caplog.text
            assert sorted(positions, key=str) == ["10", "11", None]
            assert project_ids(await fetch_explore(client, next_cursor(response))) == [
                19,
                20,
                21,
            ]


@pytest.mark.parametrize("failed_position", [None, "11"])
@pytest.mark.parametrize("failure, expected", [(429, 503), ("timeout", 504)])
async def test_snapshot_preserves_errors_from_either_confirmed_batch(
    upstream, snapshot_file, monkeypatch, failed_position, failure, expected
):
    await generate_snapshot()
    original = upstream.respond

    async def respond(request):
        if request.url.params.get("nextProjectId") == failed_position:
            if failure == "timeout":
                raise httpx.ReadTimeout("fixture", request=request)
            return httpx.Response(failure)
        return await original(request)

    monkeypatch.setattr(upstream, "respond", respond)
    app = main.create_app()
    async with app.router.lifespan_context(app), client_for(app) as client:
        first = await fetch_explore(client)
        second = await fetch_explore(client, next_cursor(first))
        assert second.status_code == expected
        assert snapshot_file.exists()


async def test_snapshot_without_saved_hint_remains_compatible(upstream, snapshot_file):
    await generate_snapshot()
    page = json.loads(snapshot_file.read_text())
    page.pop("next_position_hint")
    snapshot_file.write_text(json.dumps(page))
    app = main.create_app()
    async with app.router.lifespan_context(app), client_for(app) as client:
        first = await fetch_explore(client)
        assert project_ids(first) == list(range(1, 10))
        assert upstream.calls == ["summary"]
        assert project_ids(await fetch_explore(client, next_cursor(first))) == list(
            range(10, 19)
        )


async def test_snapshot_keeps_public_cards_when_dynamic_image_has_query(
    upstream, snapshot_file, monkeypatch
):
    original = upstream.respond
    image = "https://images.example.org/first.jpg?width=300"

    async def respond(request):
        response = await original(request)
        data = response.json()
        first = data["projects"]["project"][0]
        first.update(imageLink=image, summary="Public summary")
        return httpx.Response(200, json=data)

    monkeypatch.setattr(upstream, "respond", respond)
    dynamic = await generate_snapshot()
    assert dynamic.json()["items"][0]["image_url"] == image
    assert image not in snapshot_file.read_text()

    app = main.create_app()
    async with app.router.lifespan_context(app), client_for(app) as client:
        response = await fetch_explore(client)
        assert project_ids(response) == list(range(1, 10))
        card = response.json()["items"][0]
        assert card["summary"] == "Public summary" and card["image_url"] is None
        assert upstream.calls == ["summary"]


async def test_snapshot_ignores_failed_speculation_when_position_is_not_confirmed(
    upstream, snapshot_file, monkeypatch
):
    await generate_snapshot()
    original = upstream.respond
    upstream.catalog_batch_size = 9
    stale_response_ready = asyncio.Event()

    async def respond(request):
        position = request.url.params.get("nextProjectId")
        if position == "11":
            stale_response_ready.set()
            return httpx.Response(429)
        if position is None:
            await stale_response_ready.wait()
        return await original(request)

    monkeypatch.setattr(upstream, "respond", respond)
    app = main.create_app()
    async with app.router.lifespan_context(app), client_for(app) as client:
        first = await fetch_explore(client)
        second = await asyncio.wait_for(fetch_explore(client, next_cursor(first)), 2)
        assert project_ids(second) == list(range(10, 19))
