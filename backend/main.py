import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from api.detail import router as detail_router
from api.discovery import router as discovery_router
from api.discovery_cursor import DiscoveryCursors
from api.project_common import ProjectServices
from integrations.globalgiving import GlobalGivingProjectProvider
from projects.provider import ProjectProvider


def read_root() -> dict[str, str]:
    return {"status": "ok"}


def create_app(provider: ProjectProvider | None = None) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        cursors = DiscoveryCursors()
        if provider is not None or not os.getenv("GLOBALGIVING_API_KEY", "").strip():
            app.state.projects = ProjectServices(provider, cursors)
            yield
            return

        async with GlobalGivingProjectProvider() as globalgiving:
            app.state.projects = ProjectServices(globalgiving, cursors)
            yield

    app = FastAPI(lifespan=lifespan)
    app.include_router(discovery_router)
    app.include_router(detail_router)

    app.add_api_route("/", read_root, methods=["GET"])

    return app


app = create_app()
