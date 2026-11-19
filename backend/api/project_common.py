"""Shared HTTP responses and lifecycle state for project endpoints."""

import logging
from collections.abc import Callable, Coroutine
from dataclasses import dataclass
from typing import Any, Literal, cast

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from fastapi.routing import APIRoute
from pydantic import BaseModel

from projects.errors import ProviderError, ProviderFailure
from projects.models import ProjectSummary
from projects.provider import ProjectProvider

from .discovery_cursor import DiscoveryCursors

logger = logging.getLogger(__name__)

CommonErrorCode = Literal[
    "invalid_request",
    "internal_error",
    "provider_unavailable",
    "provider_rate_limited",
    "provider_timeout",
    "provider_failure",
]
PROVIDER_ERRORS: dict[ProviderFailure, tuple[int, CommonErrorCode]] = {
    ProviderFailure.INVALID_REQUEST: (502, "provider_failure"),
    ProviderFailure.AUTHENTICATION: (503, "provider_unavailable"),
    ProviderFailure.NOT_FOUND: (502, "provider_failure"),
    ProviderFailure.UNAVAILABLE: (503, "provider_unavailable"),
    ProviderFailure.RATE_LIMITED: (503, "provider_rate_limited"),
    ProviderFailure.TIMEOUT: (504, "provider_timeout"),
    ProviderFailure.NETWORK: (502, "provider_failure"),
    ProviderFailure.INVALID_RESPONSE: (502, "provider_failure"),
}


@dataclass(frozen=True)
class ProjectServices:
    provider: ProjectProvider | None
    cursors: DiscoveryCursors


def project_services(request: Request) -> ProjectServices:
    return cast(ProjectServices, request.app.state.projects)


def error_response(
    status: int, code: CommonErrorCode | Literal["invalid_cursor", "project_not_found"]
) -> JSONResponse:
    return JSONResponse(status_code=status, content={"code": code})


class ProjectRoute(APIRoute):
    def get_route_handler(self) -> Callable[[Request], Coroutine[Any, Any, Response]]:
        handler = super().get_route_handler()

        async def handle(request: Request) -> Response:
            try:
                return await handler(request)
            except RequestValidationError:
                return error_response(422, "invalid_request")
            except ProviderError as error:
                return error_response(*PROVIDER_ERRORS[error.reason])
            except Exception:
                logger.error("Unexpected project API failure")
                return error_response(500, "internal_error")

        return handle


class OrganizationCard(BaseModel):
    id: str
    name: str | None = None


class ProjectCard(BaseModel):
    id: str
    title: str | None = None
    summary: str | None = None
    image_url: str | None = None
    theme: str | None = None
    country: str | None = None
    organization: OrganizationCard | None = None


def project_card(project: ProjectSummary) -> ProjectCard:
    organization = project.organization
    return ProjectCard(
        id=project.id,
        title=project.title,
        summary=project.summary,
        image_url=project.image_url,
        theme=project.theme,
        country=project.country,
        organization=OrganizationCard(id=organization.id, name=organization.name)
        if organization is not None
        else None,
    )
