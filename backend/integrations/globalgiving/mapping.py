"""Only external summary data needed by Kindred crosses this boundary."""

import re
from typing import cast
from urllib.parse import urlsplit

from projects.errors import ProviderError, ProviderFailure
from projects.models import OrganizationReference, ProjectSummary


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


def safe_url(value: object) -> str | None:
    candidate = text(value)
    if candidate is None or any(char.isspace() for char in candidate):
        return None
    try:
        parsed = urlsplit(candidate)
        if (
            parsed.scheme not in ("https", "http")
            or not parsed.hostname
            or parsed.username is not None
            or parsed.password is not None
        ):
            return None
        parsed.port  # Reject malformed ports without exposing the supplied URL.
    except ValueError:
        return None
    return candidate


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
