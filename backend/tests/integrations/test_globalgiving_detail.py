import logging
import traceback
from collections.abc import AsyncIterator

import httpx
import pytest
from respx import MockRouter

from integrations.globalgiving import GlobalGivingProjectProvider
from projects.errors import ProviderError, ProviderFailure
from projects.models import OrganizationReference, ProjectDetail, ProjectSummary
from projects.provider import ProjectProvider

URL = "https://api.globalgiving.org/api/public/projectservice/projects/42"
KEY = "test-globalgiving-key"
IMAGE = "https://www.globalgiving.org/pfil/42/pict.jpg"
LINK = "https://www.globalgiving.org/projects/community-library/"


@pytest.fixture
async def provider() -> AsyncIterator[ProjectProvider]:
    async with GlobalGivingProjectProvider() as instance:
        yield instance


async def test_maps_detail_and_makes_one_authenticated_request(
    provider: ProjectProvider, globalgiving_environment: MockRouter
) -> None:
    route = globalgiving_environment.get(URL).respond(
        200,
        json={
            "project": {
                "id": 42,
                "title": " Community library ",
                "summary": "Books and a place to read.",
                "need": "Limited library access.",
                "activities": "Run reading groups.",
                "longTermImpact": "Improve access to books.",
                "region": "South America",
                "themeName": "Education",
                "country": "Brazil",
                "imageLink": IMAGE,
                "image": {"imagelink": [{"url": "https://example.test/variant.jpg"}]},
                "projectLink": LINK,
                "organization": {
                    "id": 7,
                    "name": "Library Association",
                    "url": "https://example.test/",
                },
                "funding": 120,
                "goal": 100,
            }
        },
    )

    assert await provider.get_project("00042") == ProjectDetail(
        project=ProjectSummary(
            id="42",
            title="Community library",
            summary="Books and a place to read.",
            image_url=IMAGE,
            theme="Education",
            country="Brazil",
            organization=OrganizationReference(
                id="7", name="Library Association", official_url="https://example.test/"
            ),
        ),
        need="Limited library access.",
        activities="Run reading groups.",
        long_term_impact="Improve access to books.",
        region="South America",
        official_url=LINK,
    )
    assert route.call_count == len(globalgiving_environment.calls) == 1
    request = route.calls[0].request
    assert dict(request.url.params) == {"api_key": KEY}
    assert request.headers["accept"] == "application/json"


@pytest.mark.parametrize(
    "fields",
    [
        {},
        dict.fromkeys(
            [
                "title",
                "summary",
                "organization",
                "imageLink",
                "image",
                "projectLink",
                "need",
                "activities",
                "longTermImpact",
                "region",
                "themeName",
                "country",
            ]
        ),
        {
            "organization": {"name": "No usable ID"},
            "image": {"imagelink": [None, {}, {"url": "invalid"}]},
            "projectLink": "javascript:bad",
            "activities": ["unexpected type"],
            "need": " ",
        },
        {
            "image": {"imagelink": []},
            "imageLink": f"{IMAGE}?%61pi_key={KEY}",
            "projectLink": f"{URL}?api_key={KEY}",
        },
    ],
)
async def test_preserves_detail_when_optional_fields_are_unusable(
    provider: ProjectProvider,
    globalgiving_environment: MockRouter,
    fields: dict[str, object],
) -> None:
    globalgiving_environment.get(URL).respond(
        200, json={"project": {"id": "42", **fields}}
    )

    assert await provider.get_project("42") == ProjectDetail(ProjectSummary("42"))


@pytest.mark.parametrize("links", [{"url": IMAGE}, [None, {}, {"url": IMAGE}]])
async def test_maps_nested_image_and_partial_organization(
    provider: ProjectProvider, globalgiving_environment: MockRouter, links: object
) -> None:
    globalgiving_environment.get(URL).respond(
        200,
        json={
            "project": {
                "id": 42,
                "imageLink": "https://example.test:bad/image",
                "image": {"imagelink": links},
                "organization": {"id": 7, "name": None, "url": "invalid"},
            }
        },
    )

    assert await provider.get_project("42") == ProjectDetail(
        ProjectSummary("42", image_url=IMAGE, organization=OrganizationReference("7"))
    )


@pytest.mark.parametrize(
    "project_id",
    ["", "0", "000", "-1", " 42", "42/summary", "42?x=1", "４２", "9" * 21, 42, True],
)
async def test_rejects_invalid_id_without_network(
    provider: ProjectProvider, globalgiving_environment: MockRouter, project_id: str
) -> None:
    with pytest.raises(ValueError, match="positive integer"):
        await provider.get_project(project_id)
    assert not globalgiving_environment.calls


@pytest.mark.parametrize(
    "payload",
    [
        [],
        {},
        {"project": None},
        {"project": [{"id": 42}]},
        {"project": {"title": "Missing ID"}},
        {"project": {"id": True}},
        {"project": {"id": 42.0}},
        {"project": {"id": 43}},
    ],
)
async def test_rejects_invalid_detail(
    provider: ProjectProvider, globalgiving_environment: MockRouter, payload: object
) -> None:
    globalgiving_environment.get(URL).respond(200, json=payload)

    with pytest.raises(ProviderError) as error:
        await provider.get_project("42")
    assert error.value.reason == ProviderFailure.INVALID_RESPONSE


async def test_returns_none_only_for_not_found(
    provider: ProjectProvider, globalgiving_environment: MockRouter
) -> None:
    globalgiving_environment.get(URL).respond(404)

    assert await provider.get_project("42") is None


@pytest.mark.parametrize(
    ("status", "reason"),
    [
        (400, ProviderFailure.INVALID_REQUEST),
        (401, ProviderFailure.AUTHENTICATION),
        (403, ProviderFailure.AUTHENTICATION),
        (410, ProviderFailure.UNAVAILABLE),
        (429, ProviderFailure.RATE_LIMITED),
        (500, ProviderFailure.UNAVAILABLE),
        (503, ProviderFailure.UNAVAILABLE),
    ],
)
async def test_classifies_provider_status(
    provider: ProjectProvider,
    globalgiving_environment: MockRouter,
    status: int,
    reason: ProviderFailure,
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.DEBUG)
    url_with_key = f"{URL}?api_key={KEY}"
    globalgiving_environment.get(URL).respond(status, text=url_with_key)

    with pytest.raises(ProviderError) as error:
        await provider.get_project("42")
    assert error.value.reason == reason
    assert KEY not in caplog.text
    assert KEY not in "".join(traceback.format_exception(error.value))


@pytest.mark.parametrize(
    ("error_type", "reason"),
    [
        (httpx.ReadTimeout, ProviderFailure.TIMEOUT),
        (httpx.ConnectError, ProviderFailure.NETWORK),
    ],
)
async def test_transport_errors_do_not_leak_credentials(
    provider: ProjectProvider,
    globalgiving_environment: MockRouter,
    error_type: type[httpx.RequestError],
    reason: ProviderFailure,
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.DEBUG)

    def fail(request: httpx.Request) -> httpx.Response:
        raise error_type(str(request.url), request=request)

    globalgiving_environment.get(URL).mock(side_effect=fail)

    with pytest.raises(ProviderError) as error:
        await provider.get_project("42")
    assert error.value.reason == reason
    assert KEY not in caplog.text
    assert KEY not in "".join(traceback.format_exception(error.value))


async def test_rejects_invalid_json(
    provider: ProjectProvider, globalgiving_environment: MockRouter
) -> None:
    globalgiving_environment.get(URL).respond(200, text="{")

    with pytest.raises(ProviderError) as error:
        await provider.get_project("42")
    assert error.value.reason == ProviderFailure.INVALID_RESPONSE
