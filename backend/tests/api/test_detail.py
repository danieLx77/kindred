from collections.abc import AsyncIterator

import httpx
import pytest
from fastapi import FastAPI

from main import create_app
from projects.errors import ProviderError, ProviderFailure
from projects.fake import FakeProjectProvider
from projects.models import OrganizationReference, ProjectDetail, ProjectSummary

PATH = "/api/v1/projects"


class DetailProvider(FakeProjectProvider):
    def __init__(self) -> None:
        super().__init__()
        self.calls: list[str] = []
        self.result: ProjectDetail | None = None
        self.failure: Exception | None = None

    async def get_project(self, project_id: str) -> ProjectDetail | None:
        self.calls.append(project_id)
        if self.failure is not None:
            raise self.failure
        return self.result


@pytest.fixture
def provider() -> DetailProvider:
    return DetailProvider()


@pytest.fixture
def detail_app(provider: DetailProvider) -> FastAPI:
    return create_app(provider)


@pytest.fixture
async def detail_client(detail_app: FastAPI) -> AsyncIterator[httpx.AsyncClient]:
    async with detail_app.router.lifespan_context(detail_app):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=detail_app), base_url="http://test"
        ) as client:
            yield client


async def test_complete_detail(detail_client, provider):
    provider.result = ProjectDetail(
        project=ProjectSummary(
            id="42",
            title="Educação",
            summary="Resumo",
            image_url="https://example.org/project.png",
            theme="Educação",
            country="Brasil",
            organization=OrganizationReference(
                id="12", name="Organização", official_url="https://example.org/org"
            ),
        ),
        need="Necessidade",
        activities="Atividades",
        long_term_impact="Impacto",
        region="Minas Gerais",
        official_url="https://example.org/project?ref=kindred",
    )
    response = await detail_client.get(f"{PATH}/00042")
    assert response.status_code == 200
    assert provider.calls == ["42"]
    assert response.json() == {
        "id": "42",
        "title": "Educação",
        "summary": "Resumo",
        "image_url": "https://example.org/project.png",
        "theme": "Educação",
        "country": "Brasil",
        "organization": {"id": "12", "name": "Organização"},
        "need": "Necessidade",
        "activities": "Atividades",
        "long_term_impact": "Impacto",
        "region": "Minas Gerais",
        "official_url": "https://example.org/project?ref=kindred",
    }


@pytest.mark.parametrize(
    "organization,expected",
    [(None, None), (OrganizationReference("12"), {"id": "12", "name": None})],
)
async def test_partial_detail(detail_client, provider, organization, expected):
    provider.result = ProjectDetail(
        ProjectSummary("42", country="Brasil", organization=organization)
    )
    response = await detail_client.get(f"{PATH}/42")
    assert response.status_code == 200
    assert response.json() == {
        "id": "42",
        "title": None,
        "summary": None,
        "image_url": None,
        "theme": None,
        "country": "Brasil",
        "organization": expected,
        "need": None,
        "activities": None,
        "long_term_impact": None,
        "region": None,
        "official_url": None,
    }


@pytest.mark.parametrize(
    "value",
    [
        "0",
        "000",
        "-42",
        "+42",
        "42.0",
        "4e2",
        "abc",
        "%2042",
        "４２",
        "9" * 21,
        "0" * 20 + "1",
    ],
)
async def test_invalid_id_does_not_call_provider(detail_client, provider, value):
    response = await detail_client.get(f"{PATH}/{value}")
    assert response.status_code == 422
    assert response.json() == {"code": "invalid_request"}
    assert provider.calls == []


async def test_missing_segment_remains_discovery(detail_client, provider):
    response = await detail_client.get(PATH)
    assert response.status_code == 200
    assert response.json()["items"] == []
    assert provider.calls == []


async def test_missing_project_with_valid_id(detail_client, provider):
    value = "9" * 20
    response = await detail_client.get(f"{PATH}/{value}")
    assert response.status_code == 404
    assert response.json() == {"code": "project_not_found"}
    assert provider.calls == [value]


async def test_mismatched_project(detail_client, provider):
    provider.result = ProjectDetail(ProjectSummary("43"))
    response = await detail_client.get(f"{PATH}/42")
    assert response.status_code == 502
    assert response.json() == {"code": "provider_failure"}


@pytest.mark.parametrize(
    "url",
    [
        "javascript:alert(1)",
        "//example.org/project",
        "https://user:pass@example.org/project",
        "https://example.org/project?%61pi_key=fake-secret",
        "https://example.org:bad/project",
    ],
)
async def test_unsafe_official_link_is_omitted(detail_client, provider, url):
    provider.result = ProjectDetail(ProjectSummary("42"), official_url=url)
    response = await detail_client.get(f"{PATH}/42")
    assert response.status_code == 200
    assert response.json()["official_url"] is None
    assert "fake-secret" not in response.text


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
async def test_provider_errors(detail_client, provider, reason, status, code):
    provider.failure = ProviderError(reason)
    response = await detail_client.get(f"{PATH}/42")
    assert response.status_code == status
    assert response.json() == {"code": code}


async def test_unexpected_failure_is_sanitized(detail_client, provider, caplog):
    provider.failure = RuntimeError("https://example.org/?api_key=fake-secret")
    response = await detail_client.get(f"{PATH}/42")
    assert response.status_code == 500
    assert response.json() == {"code": "internal_error"}
    assert "fake-secret" not in caplog.text
    assert "https://example.org" not in caplog.text


async def test_absent_credentials(monkeypatch):
    monkeypatch.delenv("GLOBALGIVING_API_KEY", raising=False)
    app = create_app()
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get(f"{PATH}/42")
    assert response.status_code == 503
    assert response.json() == {"code": "provider_unavailable"}


async def test_openapi(detail_client):
    document = (await detail_client.get("/openapi.json")).json()
    operation = document["paths"][f"{PATH}/{{project_id}}"]["get"]
    (parameter,) = operation["parameters"]
    assert parameter["name"] == "project_id"
    assert parameter["in"] == "path"
    assert parameter["required"]
    assert parameter["schema"]["maxLength"] == 20
    for status, name in (
        ("200", "ProjectDetailResponse"),
        *((str(code), "ProjectDetailError") for code in (404, 422, 500, 502, 503, 504)),
    ):
        schema = operation["responses"][status]["content"]["application/json"]["schema"]
        assert schema == {"$ref": f"#/components/schemas/{name}"}
    model = document["components"]["schemas"]["ProjectDetailResponse"]
    assert model["required"] == ["id"]
    assert {"type": "null"} in model["properties"]["official_url"]["anyOf"]
    assert "externo" in model["properties"]["official_url"]["description"]
    assert (await detail_client.get("/docs")).status_code == 200
