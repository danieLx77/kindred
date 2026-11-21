import base64
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
import pytest
from fastapi import FastAPI

from integrations.globalgiving import GlobalGivingProjectProvider
from main import create_app
from projects.discovery_cache import DiscoveryCacheSettings
from projects.errors import ProviderError, ProviderFailure
from projects.fake import FakeProjectProvider
from projects.models import (
    Continuation,
    DiscoveryQuery,
    DiscoveryResult,
    OrganizationReference,
    ProjectDetail,
    ProjectSummary,
)

PATH = "/api/v1/projects"


@asynccontextmanager
async def app_client(app: FastAPI) -> AsyncIterator[httpx.AsyncClient]:
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            yield client


@pytest.fixture
async def discovery_client() -> AsyncIterator[httpx.AsyncClient]:
    provider = FakeProjectProvider(
        [
            ProjectDetail(ProjectSummary("1", "Educação & inclusão")),
            ProjectDetail(
                ProjectSummary(
                    "2",
                    "Educação & inclusão II",
                    summary="Resumo",
                    organization=OrganizationReference(
                        "27", "Organização", "https://example.org"
                    ),
                )
            ),
            ProjectDetail(ProjectSummary("3", "Água")),
        ]
    )
    async with app_client(create_app(provider)) as client:
        yield client


@pytest.mark.parametrize(
    "query,expected", [(None, ["1", "2", "3"]), ("Educação & inclusão", ["1", "2"])]
)
async def test_next_and_replay_previous(discovery_client, query, expected):
    params = {"page_size": "1"}
    if query:
        params["q"] = query

    visited = []
    cursor = None
    for page, project_id in enumerate(expected, start=1):
        active = {**params, **({"cursor": cursor} if cursor else {})}
        visited.append(active)
        response = await discovery_client.get(PATH, params=active)
        assert response.status_code == 200
        body = response.json()
        assert [item["id"] for item in body["items"]] == [project_id]
        assert body["pagination"]["page"] == page
        assert body["pagination"]["page_size"] == 1
        cursor = body["pagination"]["next_cursor"]
        assert bool(cursor) == (page < len(expected))

    for page in range(len(visited) - 1, 0, -1):
        previous = await discovery_client.get(PATH, params=visited[page - 1])
        assert previous.json()["pagination"]["page"] == page
        assert previous.json()["items"][0]["id"] == expected[page - 1]


@pytest.mark.parametrize("query", [None, "", " \t "])
async def test_catalog_and_serialized_cards(discovery_client, query):
    response = await discovery_client.get(
        PATH, params={"q": query} if query is not None else None
    )
    assert response.status_code == 200
    body = response.json()
    assert body["pagination"] == {"page": 1, "page_size": 10, "next_cursor": None}
    assert body["items"][0] == {
        "id": "1",
        "title": "Educação & inclusão",
        "summary": None,
        "image_url": None,
        "theme": None,
        "country": None,
        "organization": None,
    }
    assert body["items"][1]["organization"] == {"id": "27", "name": "Organização"}
    assert "https://example.org" not in response.text


async def test_empty_search(discovery_client):
    response = await discovery_client.get(PATH, params={"q": "desconhecido"})
    assert response.status_code == 200
    assert response.json() == {
        "items": [],
        "pagination": {"page": 1, "page_size": 10, "next_cursor": None},
    }


@pytest.mark.parametrize(
    "params",
    [
        {"page_size": "0"},
        {"page_size": "11"},
        {"page_size": "foo"},
        {"q": "x" * 201},
        {"cursor": ""},
        {"cursor": "x" * 6145},
        {"theme": "edu"},
        {"country": "BR"},
        {"start": "5"},
        {"nextProjectId": "7"},
    ],
)
async def test_invalid_input_does_not_echo_values(discovery_client, params):
    response = await discovery_client.get(PATH, params=params)
    assert response.status_code == 422
    assert response.json() == {"code": "invalid_request"}


async def test_cursor_integrity_and_binding(discovery_client):
    params = {"q": "Educação & inclusão", "page_size": "1"}
    first = await discovery_client.get(PATH, params=params)
    cursor = first.json()["pagination"]["next_cursor"]
    tampered = ("B" if cursor[0] == "A" else "A") + cursor[1:]
    for invalid in (
        {**params, "cursor": "malformado"},
        {**params, "cursor": tampered},
        {**params, "cursor": cursor, "q": "Água"},
        {**params, "cursor": cursor, "page_size": "2"},
    ):
        response = await discovery_client.get(PATH, params=invalid)
        assert response.status_code == 400
        assert response.json() == {"code": "invalid_cursor"}

    normalized = await discovery_client.get(
        PATH, params={**params, "q": "  Educação   & inclusão   ", "cursor": cursor}
    )
    assert normalized.status_code == 200
    assert normalized.json()["pagination"]["page"] == 2


class FailedProvider(FakeProjectProvider):
    def __init__(self, failure: Exception) -> None:
        super().__init__()
        self.failure = failure

    async def discover(
        self,
        query: DiscoveryQuery = DiscoveryQuery(),
        continuation: Continuation | None = None,
    ) -> DiscoveryResult:
        raise self.failure


@pytest.mark.parametrize(
    "reason,status,code",
    [
        (ProviderFailure.AUTHENTICATION, 503, "provider_unavailable"),
        (ProviderFailure.UNAVAILABLE, 503, "provider_unavailable"),
        (ProviderFailure.RATE_LIMITED, 503, "provider_rate_limited"),
        (ProviderFailure.TIMEOUT, 504, "provider_timeout"),
        (ProviderFailure.NETWORK, 502, "provider_failure"),
        (ProviderFailure.INVALID_RESPONSE, 502, "provider_failure"),
        (ProviderFailure.INVALID_REQUEST, 502, "provider_failure"),
        (ProviderFailure.NOT_FOUND, 502, "provider_failure"),
    ],
)
async def test_provider_failures(reason, status, code):
    async with app_client(create_app(FailedProvider(ProviderError(reason)))) as client:
        response = await client.get(PATH)
    assert response.status_code == status
    assert response.json() == {"code": code}


async def test_unexpected_failure_has_safe_body_and_log(caplog):
    failure = RuntimeError("https://example.org/?api_key=segredo-de-teste")
    async with app_client(create_app(FailedProvider(failure))) as client:
        response = await client.get(PATH)
    assert response.status_code == 500
    assert response.json() == {"code": "internal_error"}
    assert "segredo-de-teste" not in caplog.text


async def test_missing_provider_does_not_break_root(monkeypatch):
    monkeypatch.delenv("GLOBALGIVING_API_KEY", raising=False)
    async with app_client(create_app()) as client:
        assert (await client.get("/")).json() == {"status": "ok"}
        response = await client.get(PATH)
    assert response.status_code == 503
    assert response.json() == {"code": "provider_unavailable"}


async def test_openapi_and_documentation(discovery_client):
    response = await discovery_client.get("/openapi.json")
    operation = response.json()["paths"][PATH]["get"]
    assert {parameter["name"] for parameter in operation["parameters"]} == {
        "q",
        "page_size",
        "cursor",
    }
    assert operation["responses"]["200"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/DiscoveryResponse"
    }
    for status in ("400", "422", "500", "502", "503", "504"):
        assert operation["responses"][status]["content"]["application/json"][
            "schema"
        ] == {"$ref": "#/components/schemas/DiscoveryError"}
    assert (await discovery_client.get("/docs")).status_code == 200


async def test_lifespan_owns_client_and_cursor_with_real_adapter(monkeypatch):
    monkeypatch.setenv("GLOBALGIVING_API_KEY", "fake-key")
    providers = []
    positions = []

    def respond(request: httpx.Request) -> httpx.Response:
        assert request.url.params["api_key"] == "fake-key"
        position = request.url.params.get("nextProjectId")
        positions.append(position)
        listing: dict[str, object] = {"project": [{"id": int(position or "1")}]}
        if position is None:
            listing.update(hasNext=True, nextProjectId=2)
        return httpx.Response(200, json={"projects": listing})

    class TrackedProvider(GlobalGivingProjectProvider):
        closed = False

        def __init__(
            self, *, api_key: str, cache_settings: DiscoveryCacheSettings
        ) -> None:
            super().__init__(
                api_key=api_key,
                cache_settings=cache_settings,
                transport=httpx.MockTransport(respond),
            )
            providers.append(self)

        async def aclose(self) -> None:
            await super().aclose()
            self.closed = True

    monkeypatch.setattr("main.GlobalGivingProjectProvider", TrackedProvider)
    app = create_app()
    async with app_client(app) as client:
        first = await client.get(PATH)
        assert first.status_code == 200
        cursor = first.json()["pagination"]["next_cursor"]
        assert b"fake-key" not in base64.urlsafe_b64decode(cursor)
        next_page = await client.get(PATH, params={"cursor": cursor})
        assert next_page.json()["items"][0]["id"] == "2"
        assert positions == [None, "2"]
        assert len(providers) == 1
        assert not providers[0].closed
    assert providers[0].closed

    async with app_client(app) as client:
        expired = await client.get(PATH, params={"cursor": cursor})
        assert expired.status_code == 400
        assert expired.json() == {"code": "invalid_cursor"}
        assert positions == [None, "2"]


@pytest.mark.parametrize("search", [False, True])
async def test_nine_project_pages_preserve_provider_order(monkeypatch, search):
    monkeypatch.setenv("GLOBALGIVING_API_KEY", "fake-key")
    projects = [{"id": 101 + i * 7} for i in range(31)]
    ids = [str(project["id"]) for project in projects]
    positions = []

    def respond(request: httpx.Request) -> httpx.Response:
        if search:
            assert request.url.params["q"] == "water"
            start = int(request.url.params["start"])
            payload = {
                "search": {
                    "response": {
                        "@start": start,
                        "projects": {"project": projects[start : start + 10]},
                    }
                }
            }
        else:
            cursor = request.url.params.get("nextProjectId")
            start = ids.index(cursor) if cursor is not None else 0
            batch: dict[str, object] = {"project": projects[start : start + 10]}
            if start + 10 < len(projects):
                batch.update(hasNext=True, nextProjectId=projects[start + 10]["id"])
            payload = {"projects": batch}
        positions.append(start)
        return httpx.Response(200, json=payload)

    params = {"page_size": "9", **({"q": "water"} if search else {})}
    provider = GlobalGivingProjectProvider(transport=httpx.MockTransport(respond))
    async with provider, app_client(create_app(provider)) as client:
        cursor = None
        for page, offset in enumerate(range(0, len(projects), 9), 1):
            response = await client.get(
                PATH, params={**params, **({"cursor": cursor} if cursor else {})}
            )
            assert response.status_code == 200
            body = response.json()
            assert [item["id"] for item in body["items"]] == ids[offset : offset + 9]
            assert body["pagination"]["page"] == page
            assert body["pagination"]["page_size"] == 9
            cursor = body["pagination"]["next_cursor"]
            if page == 1:
                assert cursor is not None
                incompatible = await client.get(
                    PATH, params={**params, "page_size": "10", "cursor": cursor}
                )
                assert incompatible.status_code == 400
                assert incompatible.json() == {"code": "invalid_cursor"}

        if search:
            assert cursor is not None
            empty = await client.get(PATH, params={**params, "cursor": cursor})
            assert empty.json() == {
                "items": [],
                "pagination": {"page": 5, "page_size": 9, "next_cursor": None},
            }
            assert positions == [0, 9, 18, 27, 31]
        else:
            assert cursor is None
            assert positions == [0, 0, 10, 10, 20, 20, 30]

        first = await client.get(PATH, params=params)
        assert [item["id"] for item in first.json()["items"]] == ids[:9]
        default = await client.get(
            PATH,
            params={key: value for key, value in params.items() if key != "page_size"},
        )
        default_body = default.json()
        assert [item["id"] for item in default_body["items"]] == ids[:10]
        previous_size_cursor = default_body["pagination"]["next_cursor"]
        assert previous_size_cursor is not None
        incompatible = await client.get(
            PATH, params={**params, "cursor": previous_size_cursor}
        )
        assert incompatible.status_code == 400
        assert incompatible.json() == {"code": "invalid_cursor"}


@pytest.mark.parametrize("search", [False, True])
async def test_real_adapter_stops_at_repeated_position_or_empty_batch(
    monkeypatch, search
):
    monkeypatch.setenv("GLOBALGIVING_API_KEY", "fake-key")
    positions = []

    def respond(request: httpx.Request) -> httpx.Response:
        if search:
            start = request.url.params["start"]
            positions.append(start)
            projects = {"project": [{"id": 1}]} if start == "0" else {}
            payload = {"search": {"response": {"@start": start, "projects": projects}}}
        else:
            cursor = request.url.params.get("nextProjectId")
            positions.append(cursor)
            next_id = 2 if cursor is None else 3 if cursor == "2" else 2
            payload = {
                "projects": {
                    "project": [{"id": int(cursor or "1")}],
                    "hasNext": True,
                    "nextProjectId": next_id,
                }
            }
        return httpx.Response(200, json=payload)

    provider = GlobalGivingProjectProvider(transport=httpx.MockTransport(respond))
    params = {"q": "water"} if search else {}
    async with provider, app_client(create_app(provider)) as client:
        first = await client.get(PATH, params=params)
        cursor = first.json()["pagination"]["next_cursor"]
        second = await client.get(PATH, params={**params, "cursor": cursor})
        if search:
            assert second.json() == {
                "items": [],
                "pagination": {"page": 2, "page_size": 10, "next_cursor": None},
            }
            assert positions == ["0", "1"]
        else:
            cursor = second.json()["pagination"]["next_cursor"]
            third = await client.get(PATH, params={**params, "cursor": cursor})
            assert third.status_code == 502
            assert third.json() == {"code": "provider_failure"}
            assert positions == [None, "2", "3"]
