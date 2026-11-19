"""HTTP contract for Kindred project discovery."""

import logging
from collections.abc import Callable, Coroutine
from dataclasses import dataclass
from typing import Annotated, Any, ClassVar, Literal, cast

from fastapi import APIRouter, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from fastapi.routing import APIRoute
from pydantic import BaseModel, ConfigDict, Field

from projects.errors import ProviderError, ProviderFailure
from projects.models import DiscoveryQuery, ProjectSummary
from projects.provider import ProjectProvider

from .discovery_cursor import MAX_CURSOR_LENGTH, DiscoveryCursors, InvalidCursor

logger = logging.getLogger(__name__)

ErrorCode = Literal[
    "invalid_request",
    "invalid_cursor",
    "internal_error",
    "provider_unavailable",
    "provider_rate_limited",
    "provider_timeout",
    "provider_failure",
]
PROVIDER_ERRORS: dict[ProviderFailure, tuple[int, ErrorCode]] = {
    ProviderFailure.INVALID_REQUEST: (502, "provider_failure"),
    ProviderFailure.AUTHENTICATION: (503, "provider_unavailable"),
    ProviderFailure.NOT_FOUND: (502, "provider_failure"),
    ProviderFailure.UNAVAILABLE: (503, "provider_unavailable"),
    ProviderFailure.RATE_LIMITED: (503, "provider_rate_limited"),
    ProviderFailure.TIMEOUT: (504, "provider_timeout"),
    ProviderFailure.NETWORK: (502, "provider_failure"),
    ProviderFailure.INVALID_RESPONSE: (502, "provider_failure"),
}


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
    code: ErrorCode


@dataclass(frozen=True)
class DiscoveryServices:
    provider: ProjectProvider | None
    cursors: DiscoveryCursors


def _error(status: int, code: ErrorCode) -> JSONResponse:
    return JSONResponse(
        status_code=status, content=DiscoveryError(code=code).model_dump()
    )


class DiscoveryRoute(APIRoute):
    def get_route_handler(self) -> Callable[[Request], Coroutine[Any, Any, Response]]:
        handler = super().get_route_handler()

        async def handle(request: Request) -> Response:
            try:
                return await handler(request)
            except RequestValidationError:
                return _error(422, "invalid_request")
            except Exception:
                logger.error("Unexpected project discovery failure")
                return _error(500, "internal_error")

        return handle


router = APIRouter(prefix="/api/v1/projects", route_class=DiscoveryRoute)


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
    services = cast(DiscoveryServices, request.app.state.discovery)
    if services.provider is None:
        return _error(503, "provider_unavailable")

    query = DiscoveryQuery(
        text=" ".join((params.q or "").split()) or None, page_size=params.page_size
    )
    page, continuation = 1, None
    if params.cursor is not None:
        try:
            page, continuation = services.cursors.decode(params.cursor, query)
        except InvalidCursor:
            return _error(400, "invalid_cursor")

    try:
        result = await services.provider.discover(query, continuation)
    except ProviderError as error:
        return _error(*PROVIDER_ERRORS[error.reason])

    next_cursor = None
    if result.continuation is not None:
        next_cursor = services.cursors.encode(result.continuation, page + 1, query)

    return DiscoveryResponse(
        items=[_card(project) for project in result.items],
        pagination=DiscoveryPage(
            page=page, page_size=query.page_size, next_cursor=next_cursor
        ),
    )


def _card(project: ProjectSummary) -> ProjectCard:
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
