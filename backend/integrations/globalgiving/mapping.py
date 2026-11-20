"""Only external project data needed by Kindred crosses this boundary."""

import re
from typing import cast

from projects.errors import ProviderError, ProviderFailure
from projects.models import OrganizationReference, ProjectDetail, ProjectSummary
from projects.urls import safe_url

_CARD_SIZES = ("large", "extraLarge", "medium")
_DETAIL_SIZES = ("extraLarge", "large", "medium", "original")


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


def summary(
    value: object, *, image_sizes: tuple[str, ...] = _CARD_SIZES
) -> ProjectSummary:
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
    variants = _image_variants(data)
    return ProjectSummary(
        id=project_id,
        title=text(data.get("title")),
        summary=text(data.get("summary")),
        image_url=(
            _preferred_image(variants, image_sizes)
            or safe_url(data.get("imageLink"))
            or next(iter(variants.values()), None)
        ),
        theme=text(data.get("themeName")),
        country=text(data.get("country")),
        organization=organization,
    )


def _projects(container: dict[str, object]) -> tuple[dict[str, object], ...]:
    raw = container.get("project")
    if raw is None:
        return ()
    if isinstance(raw, dict):
        raw = [raw]
    if not isinstance(raw, list) or len(raw) > 10:
        raise invalid_response()
    return tuple(object_value(item) for item in raw)


def summaries(container: dict[str, object]) -> tuple[ProjectSummary, ...]:
    result = tuple(summary(item) for item in _projects(container))
    if len({project.id for project in result}) != len(result):
        raise invalid_response()
    return result


def _image_variants(data: dict[str, object]) -> dict[str, str]:
    variants: dict[str, str] = {}
    for field, link_field in (("image", "imagelink"), ("imageSizeOptions", "image")):
        image = data.get(field)
        if not isinstance(image, dict):
            continue
        links = object_value(image).get(link_field)
        if isinstance(links, dict):
            links = [links]
        if not isinstance(links, list):
            continue
        for link in links:
            if not isinstance(link, dict):
                continue
            link = object_value(link)
            if (url := safe_url(link.get("url"))) is not None:
                size = text(link.get("@size")) or text(link.get("size")) or ""
                variants.setdefault(size, url)
    return variants


def _preferred_image(variants: dict[str, str], sizes: tuple[str, ...]) -> str | None:
    return next((variants[size] for size in sizes if size in variants), None)


def card_image_variants(payload: object) -> dict[str, str]:
    container = object_value(object_value(payload).get("projects"))
    return {
        str(integer(project.get("id"), minimum=1)): image
        for project in _projects(container)
        if (image := _preferred_image(_image_variants(project), _CARD_SIZES))
        is not None
    }


def detail(value: object, project_id: str) -> ProjectDetail:
    data = object_value(object_value(value).get("project"))
    project = summary(data, image_sizes=_DETAIL_SIZES)
    if project.id != project_id:
        raise invalid_response()
    return ProjectDetail(
        project=project,
        need=text(data.get("need")),
        activities=text(data.get("activities")),
        long_term_impact=text(data.get("longTermImpact")),
        region=text(data.get("region")),
        official_url=safe_url(data.get("projectLink")),
    )
