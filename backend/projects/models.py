"""Product data, independent of HTTP and external provider schemas."""

from dataclasses import dataclass


@dataclass(frozen=True)
class OrganizationReference:
    id: str
    name: str | None = None
    official_url: str | None = None


@dataclass(frozen=True)
class ProjectSummary:
    id: str
    title: str | None = None
    summary: str | None = None
    image_url: str | None = None
    theme: str | None = None
    country: str | None = None
    organization: OrganizationReference | None = None


@dataclass(frozen=True)
class ProjectDetail:
    project: ProjectSummary
    need: str | None = None
    activities: str | None = None
    long_term_impact: str | None = None
    region: str | None = None
    official_url: str | None = None


@dataclass(frozen=True)
class DiscoveryQuery:
    text: str | None = None
    theme: str | None = None
    country: str | None = None
    page_size: int = 10

    def __post_init__(self) -> None:
        if self.page_size < 1:
            raise ValueError("page_size must be positive")


@dataclass(frozen=True)
class Continuation:
    """Opaque Kindred handle; callers must reuse it with the original query."""

    token: str


@dataclass(frozen=True)
class DiscoveryResult:
    items: tuple[ProjectSummary, ...] = ()
    continuation: Continuation | None = None
