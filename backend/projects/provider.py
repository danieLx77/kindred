from typing import Protocol

from projects.models import (
    Continuation,
    DiscoveryQuery,
    DiscoveryResult,
    ProjectDetail,
)


class ProjectProvider(Protocol):
    """Application port. No text/filters means browsing, otherwise searching.

    A missing ID returns None; provider failures must not masquerade as missing
    projects or empty results. Continuations belong to the issuing provider and
    original query, and must not be interpreted by the application.
    """

    async def discover(
        self,
        query: DiscoveryQuery = DiscoveryQuery(),
        continuation: Continuation | None = None,
    ) -> DiscoveryResult: ...

    async def get_project(self, project_id: str) -> ProjectDetail | None: ...
