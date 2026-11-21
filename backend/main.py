import logging
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import dotenv_values
from fastapi import FastAPI

from api.detail import router as detail_router
from api.discovery import router as discovery_router
from api.discovery_cursor import DiscoveryCursors
from api.project_common import ProjectServices
from integrations.globalgiving import GlobalGivingProjectProvider
from integrations.globalgiving.explore_snapshot import ExploreSnapshot
from projects.discovery_cache import DiscoveryCacheSettings
from projects.provider import ProjectProvider

logger = logging.getLogger(__name__)
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def _globalgiving_api_key(load_local_env: bool) -> str:
    name = "GLOBALGIVING_API_KEY"
    exported = os.getenv(name)
    if exported is not None:
        return exported.strip()

    if (
        not load_local_env
        or os.getenv("CI")
        or os.getenv("KINDRED_LOAD_LOCAL_ENV") == "0"
        or not (REPOSITORY_ROOT / ".git").exists()
    ):
        return ""

    local_env = REPOSITORY_ROOT / ".env"
    try:
        if local_env.is_file():
            return (dotenv_values(local_env, interpolate=False).get(name) or "").strip()
    except (OSError, UnicodeError):
        logger.warning("Could not read the local backend .env")
    return ""


def read_root() -> dict[str, str]:
    return {"status": "ok"}


def create_app(
    provider: ProjectProvider | None = None, *, load_local_env: bool = False
) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        cursors = DiscoveryCursors()
        api_key = _globalgiving_api_key(load_local_env) if provider is None else ""
        if not api_key:
            app.state.projects = ProjectServices(provider, cursors)
            yield
            return

        async with GlobalGivingProjectProvider(
            api_key=api_key, cache_settings=DiscoveryCacheSettings.from_env()
        ) as globalgiving:
            snapshot = ExploreSnapshot.from_env()
            if snapshot is not None:
                globalgiving.start_explore_snapshot(snapshot)
            app.state.projects = ProjectServices(globalgiving, cursors)
            yield

    app = FastAPI(lifespan=lifespan)
    app.include_router(discovery_router)
    app.include_router(detail_router)

    app.add_api_route("/", read_root, methods=["GET"])

    return app


app = create_app(load_local_env=True)
