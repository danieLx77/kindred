"""Only external project data needed by Kindred crosses this boundary."""

import re
from dataclasses import replace
from typing import cast

from projects.errors import ProviderError, ProviderFailure
from projects.models import OrganizationReference, ProjectDetail, ProjectSummary
from projects.urls import safe_url


def invalid_response() -> ProviderError:
    return ProviderError(ProviderFailure.INVALID_RESPONSE)


def object_value(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        raise invalid_response()
    return cast(dict[str, object], value)


def integer(value: object, *, minimum: int = 0) -> int:
    if isinstance(value, str) and re.fullmatch(r"[0-9]{1,20}", value):
        value = int(value)
    if type(value) is not int or value < minimum:
        raise invalid_response()
    return value


def text(value: object) -> str | None:
    return value.strip() or None if isinstance(value, str) else None


def summary(value: object) -> ProjectSummary:
    data = object_value(value)
    project_id = str(integer(data.get("id"), minimum=1))
    organization = None
    raw_organization = data.get("organization")
    if isinstance(raw_organization, dict):
        org = object_value(raw_organization)
        try:
            org_id = str(integer(org.get("id"), minimum=1))
        except ProviderError:
            pass  # Optional reference without a usable ID cannot be constructed.
        else:
            organization = OrganizationReference(
                id=org_id,
                name=text(org.get("name")),
                official_url=safe_url(org.get("url")),
            )
    return ProjectSummary(
        id=project_id,
        title=text(data.get("title")),
        summary=text(data.get("summary")),
        image_url=safe_url(data.get("imageLink")),
        theme=text(data.get("themeName")),
        country=text(data.get("country")),
        organization=organization,
    )


def summaries(container: dict[str, object]) -> tuple[ProjectSummary, ...]:
    raw = container.get("project")
    if raw is None:
        return ()
    if isinstance(raw, dict):
        raw = [raw]
    if not isinstance(raw, list) or len(raw) > 10:
        raise invalid_response()
    result = tuple(summary(item) for item in raw)
    if len({project.id for project in result}) != len(result):
        raise invalid_response()
    return result


def _image_variant(value: object) -> str | None:
    if not isinstance(value, dict):
        return None
    links = object_value(value).get("imagelink")
    if isinstance(links, dict):
        links = [links]
    if not isinstance(links, list):
        return None
    for link in links:
        if isinstance(link, dict):
            url = safe_url(object_value(link).get("url"))
            if url is not None:
                return url
    return None


def detail(value: object, project_id: str) -> ProjectDetail:
    data = object_value(object_value(value).get("project"))
    project = summary(data)
    if project.id != project_id:
        raise invalid_response()
    if project.image_url is None:
        project = replace(project, image_url=_image_variant(data.get("image")))
    return ProjectDetail(
        project=project,
        need=text(data.get("need")),
        activities=text(data.get("activities")),
        long_term_impact=text(data.get("longTermImpact")),
        region=text(data.get("region")),
        official_url=safe_url(data.get("projectLink")),
    )
