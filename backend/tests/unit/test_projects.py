from dataclasses import FrozenInstanceError

import pytest

from projects.fake import FakeProjectProvider
from projects.models import (
    Continuation,
    DiscoveryQuery,
    DiscoveryResult,
    OrganizationReference,
    ProjectDetail,
    ProjectSummary,
)
from projects.provider import ProjectProvider


def full_project() -> ProjectDetail:
    return ProjectDetail(
        project=ProjectSummary(
            id="school",
            title="Education for all",
            summary="Help children learn",
            image_url="https://example.org/school.jpg",
            theme="Education",
            country="Brazil",
            organization=OrganizationReference(
                id="teachers",
                name="Teachers Together",
                official_url="https://example.org/teachers",
            ),
        ),
        need="Classrooms need books",
        activities="Provide reading materials",
        long_term_impact="More children can read",
        region="South America",
        official_url="https://example.org/school",
    )


def test_full_and_partial_product_data() -> None:
    full = full_project()
    assert full.project.organization is not None
    assert full.project.organization.name == "Teachers Together"
    assert full.official_url == "https://example.org/school"
    assert full.need == "Classrooms need books"
    assert full.activities == "Provide reading materials"
    assert full.long_term_impact == "More children can read"

    partial = ProjectDetail(ProjectSummary(id="partial"))
    assert partial.project.title is None
    assert partial.project.summary is None
    assert partial.project.image_url is None
    assert partial.project.theme is None
    assert partial.project.country is None
    assert partial.project.organization is None
    assert partial.need is None
    assert partial.activities is None
    assert partial.long_term_impact is None
    assert partial.region is None
    assert partial.official_url is None
    assert OrganizationReference(id="unknown").name is None
    assert OrganizationReference(id="unknown").official_url is None


def test_product_data_is_immutable() -> None:
    project = ProjectSummary(id="one")
    with pytest.raises(FrozenInstanceError):
        setattr(project, "title", "changed")


@pytest.mark.parametrize("page_size", [0, -1])
def test_invalid_page_size(page_size: int) -> None:
    with pytest.raises(ValueError, match="positive"):
        DiscoveryQuery(page_size=page_size)


async def test_application_uses_fake_through_provider_contract() -> None:
    detail = full_project()
    provider: ProjectProvider = FakeProjectProvider([detail])
    assert await provider.discover() == DiscoveryResult((detail.project,))
    assert await provider.get_project("school") == detail
    assert await provider.get_project("missing") is None


@pytest.mark.parametrize("text", ["EDUCATION", "children", "teachers"])
async def test_fake_text_search_with_combined_filters(text: str) -> None:
    detail = full_project()
    provider: ProjectProvider = FakeProjectProvider(
        [detail, ProjectDetail(ProjectSummary(id="partial"))]
    )
    result = await provider.discover(
        DiscoveryQuery(text=text, theme="Education", country="Brazil")
    )
    assert result.items == (detail.project,)
    assert result.continuation is None


@pytest.mark.parametrize(
    "query",
    [
        DiscoveryQuery(text="no match"),
        DiscoveryQuery(theme="Health"),
        DiscoveryQuery(country="Portugal"),
    ],
)
async def test_fake_no_results(query: DiscoveryQuery) -> None:
    provider = FakeProjectProvider([full_project()])
    assert await provider.discover(query) == DiscoveryResult()


async def test_empty_fake() -> None:
    provider = FakeProjectProvider()
    assert await provider.discover() == DiscoveryResult()
    assert await provider.get_project("missing") is None


async def test_continuation_traversal_replay_and_partial_last_page() -> None:
    projects = [ProjectDetail(ProjectSummary(id=str(i))) for i in range(5)]
    provider: ProjectProvider = FakeProjectProvider(projects)
    query = DiscoveryQuery(page_size=2)
    first = await provider.discover(query)
    assert first.items == tuple(p.project for p in projects[:2])
    assert first.continuation is not None
    second = await provider.discover(query, first.continuation)
    assert second.items == tuple(p.project for p in projects[2:4])
    assert second.continuation is not None
    last = await provider.discover(query, second.continuation)
    assert last == DiscoveryResult((projects[4].project,))
    replay = await provider.discover(query, first.continuation)
    assert replay.items == second.items
    assert replay.continuation is not None


async def test_exact_full_page_has_no_continuation() -> None:
    provider = FakeProjectProvider([full_project()])
    assert (await provider.discover(DiscoveryQuery(page_size=1))).continuation is None


async def test_pagination_applies_filters_before_slicing() -> None:
    first = full_project()
    second = ProjectDetail(ProjectSummary(id="other", country="Brazil"))
    provider = FakeProjectProvider(
        [ProjectDetail(ProjectSummary(id="excluded")), first, second]
    )
    query = DiscoveryQuery(country="Brazil", page_size=1)
    result = await provider.discover(query)
    assert result.items == (first.project,)
    assert result.continuation is not None
    assert await provider.discover(query, result.continuation) == DiscoveryResult(
        (second.project,)
    )


async def test_continuation_rejects_other_queries_and_providers() -> None:
    projects = [full_project(), ProjectDetail(ProjectSummary(id="partial"))]
    provider = FakeProjectProvider(projects)
    query = DiscoveryQuery(page_size=1)
    first = await provider.discover(query)
    assert first.continuation is not None
    with pytest.raises(ValueError, match="query/provider"):
        await provider.discover(DiscoveryQuery(page_size=2), first.continuation)
    with pytest.raises(ValueError, match="query/provider"):
        await provider.discover(
            DiscoveryQuery(text="Education", page_size=1), first.continuation
        )
    with pytest.raises(ValueError, match="query/provider"):
        await FakeProjectProvider(projects).discover(query, first.continuation)
    with pytest.raises(ValueError, match="query/provider"):
        await provider.discover(query, Continuation("unknown"))
