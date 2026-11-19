"""HTTP contract for Kindred project details."""

from typing import Annotated, Literal

from fastapi import APIRouter, Path, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from projects.urls import safe_url

from .project_common import (
    CommonErrorCode,
    ProjectCard,
    ProjectRoute,
    error_response,
    project_card,
    project_services,
)


class ProjectDetailResponse(ProjectCard):
    need: str | None = None
    activities: str | None = None
    long_term_impact: str | None = None
    region: str | None = None
    official_url: str | None = Field(
        default=None, description="Link oficial externo do projeto, quando disponível."
    )


class ProjectDetailError(BaseModel):
    code: Literal[CommonErrorCode, "project_not_found"]


router = APIRouter(prefix="/api/v1/projects", route_class=ProjectRoute)


@router.get(
    "/{project_id}",
    response_model=ProjectDetailResponse,
    responses={
        404: {"model": ProjectDetailError, "description": "Projeto inexistente."},
        422: {"model": ProjectDetailError, "description": "Identificador inválido."},
        500: {"model": ProjectDetailError, "description": "Falha interna."},
        502: {
            "model": ProjectDetailError,
            "description": "Falha ou resposta inválida do provedor.",
        },
        503: {
            "model": ProjectDetailError,
            "description": "Provedor indisponível ou limitado.",
        },
        504: {
            "model": ProjectDetailError,
            "description": "Tempo de resposta do provedor excedido.",
        },
    },
    summary="Consultar detalhes de um projeto",
    description="Retorna os dados disponíveis do projeto. Campos opcionais podem ser nulos.",
)
async def get_project_detail(
    request: Request,
    project_id: Annotated[
        str,
        Path(
            min_length=1,
            max_length=20,
            pattern=r"^[0-9]*[1-9][0-9]*$",
            description="ID decimal positivo, com até 20 dígitos ASCII.",
        ),
    ],
) -> ProjectDetailResponse | JSONResponse:
    provider = project_services(request).provider
    if provider is None:
        return error_response(503, "provider_unavailable")

    canonical_id = project_id.lstrip("0")
    detail = await provider.get_project(canonical_id)
    if detail is None:
        return error_response(404, "project_not_found")
    if detail.project.id != canonical_id:
        return error_response(502, "provider_failure")

    return ProjectDetailResponse(
        **project_card(detail.project).model_dump(),
        need=detail.need,
        activities=detail.activities,
        long_term_impact=detail.long_term_impact,
        region=detail.region,
        official_url=safe_url(detail.official_url),
    )
