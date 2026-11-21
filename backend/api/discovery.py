"""HTTP contract for Kindred project discovery."""

import logging
from typing import Annotated, ClassVar, Literal

from fastapi import APIRouter, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from projects.models import DiscoveryQuery

from .discovery_cursor import MAX_CURSOR_LENGTH, InvalidCursor
from .project_common import (
    CommonErrorCode,
    ProjectCard,
    ProjectRoute,
    error_response,
    project_card,
    project_services,
)


class _DiscoveryAccessLogFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        # Uvicorn access records include the raw URL query by default.
        args = record.args
        if isinstance(args, tuple) and len(args) == 5 and isinstance(args[2], str):
            path, _, _ = args[2].partition("?")
            if path.rstrip("/").endswith("/api/v1/projects"):
                record.args = (*args[:2], path, *args[3:])
        return True


logging.getLogger("uvicorn.access").addFilter(_DiscoveryAccessLogFilter())


class DiscoveryParameters(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")

    q: str | None = Field(
        default=None,
        max_length=200,
        description="Texto livre. Ausente ou em branco lista o catálogo.",
    )
    page_size: int = Field(
        default=10, ge=1, le=10, description="Limite de itens por lote."
    )
    cursor: str | None = Field(
        default=None,
        min_length=1,
        max_length=MAX_CURSOR_LENGTH,
        description="Cursor opaco emitido pelo Kindred para o mesmo texto e tamanho de lote.",
    )


class DiscoveryPage(BaseModel):
    page: int = Field(ge=1, description="Posição na sequência de navegação.")
    page_size: int = Field(ge=1, le=10)
    next_cursor: str | None = Field(
        description="Cursor do próximo lote. Nulo quando não há continuação."
    )


class DiscoveryResponse(BaseModel):
    items: list[ProjectCard]
    pagination: DiscoveryPage


class DiscoveryError(BaseModel):
    code: Literal[CommonErrorCode, "invalid_cursor"]


router = APIRouter(prefix="/api/v1/projects", route_class=ProjectRoute)


@router.get(
    "",
    response_model=DiscoveryResponse,
    responses={
        400: {"model": DiscoveryError, "description": "Cursor inválido ou expirado."},
        422: {
            "model": DiscoveryError,
            "description": "Parâmetros de consulta inválidos.",
        },
        500: {"model": DiscoveryError, "description": "Falha interna."},
        502: {
            "model": DiscoveryError,
            "description": "Falha de comunicação ou resposta inválida.",
        },
        503: {
            "model": DiscoveryError,
            "description": "Provedor indisponível ou limitado.",
        },
        504: {
            "model": DiscoveryError,
            "description": "Tempo de resposta do provedor excedido.",
        },
    },
    summary="Listar ou pesquisar projetos",
    description=(
        "A busca depende dos campos indexados pelo provedor. Campos opcionais podem ser nulos. "
        "A navegação usa cursores opacos e não informa um total de páginas. "
        "Para voltar, reutilize o cursor de uma posição já visitada."
    ),
)
async def discover_projects(
    request: Request, params: Annotated[DiscoveryParameters, Query()]
) -> DiscoveryResponse | JSONResponse:
    services = project_services(request)
    if services.provider is None:
        return error_response(503, "provider_unavailable")

    query = DiscoveryQuery(
        text=" ".join((params.q or "").split()) or None, page_size=params.page_size
    )
    page, continuation = 1, None
    if params.cursor is not None:
        try:
            page, continuation = services.cursors.decode(params.cursor, query)
        except InvalidCursor:
            return error_response(400, "invalid_cursor")

    result = await services.provider.discover(query, continuation)

    next_cursor = None
    if result.continuation is not None:
        next_cursor = services.cursors.encode(result.continuation, page + 1, query)

    return DiscoveryResponse(
        items=[project_card(project) for project in result.items],
        pagination=DiscoveryPage(
            page=page, page_size=query.page_size, next_cursor=next_cursor
        ),
    )
