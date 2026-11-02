"""Deterministic in-memory provider for application development and tests."""

from collections.abc import Iterable
from uuid import uuid4

from projects.models import (
    Continuation,
    DiscoveryQuery,
    DiscoveryResult,
    ProjectDetail,
    ProjectSummary,
)


class FakeProjectProvider:
    def __init__(self, projects: Iterable[ProjectDetail] = ()) -> None:
        self._projects = {detail.project.id: detail for detail in projects}
        self._continuations: dict[str, tuple[DiscoveryQuery, int]] = {}

    async def discover(
        self,
        query: DiscoveryQuery = DiscoveryQuery(),
        continuation: Continuation | None = None,
    ) -> DiscoveryResult:
        offset = 0
        if continuation is not None:
            saved = self._continuations.get(continuation.token)
            if saved is None or saved[0] != query:
                raise ValueError("Continuation does not belong to this query/provider")
            offset = saved[1]

        matches = tuple(
            detail.project
            for detail in self._projects.values()
            if self._matches(detail.project, query)
        )
        end = offset + query.page_size
        next_page = None
        if end < len(matches):
            next_page = Continuation(uuid4().hex)
            self._continuations[next_page.token] = (query, end)
        return DiscoveryResult(matches[offset:end], next_page)

    async def get_project(self, project_id: str) -> ProjectDetail | None:
        return self._projects.get(project_id)

    @staticmethod
    def _matches(project: ProjectSummary, query: DiscoveryQuery) -> bool:
        if query.theme is not None and project.theme != query.theme:
            return False
        if query.country is not None and project.country != query.country:
            return False
        text = (query.text or "").strip().casefold()
        searchable = " ".join(
            value
            for value in (
                project.title,
                project.summary,
                project.theme,
                project.organization.name if project.organization else None,
            )
            if value is not None
        )
        return text in searchable.casefold()
