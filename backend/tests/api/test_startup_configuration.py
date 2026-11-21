import logging
import os
from pathlib import Path

import httpx
import pytest
from uvicorn import Config

import main
from integrations.globalgiving import GlobalGivingProjectProvider
from projects.discovery_cache import DiscoveryCacheSettings

KEY = "GLOBALGIVING_API_KEY"
LOCAL_KEY = "local-fixture-key"
EXPORTED_KEY = "exported-fixture-key"
PROJECTS = "/api/v1/projects"


@pytest.fixture
def checkout(tmp_path, monkeypatch):
    root = tmp_path / "checkout"
    root.mkdir()
    (root / ".git").touch()  # A linked Git worktree uses a file.
    monkeypatch.setattr(main, "REPOSITORY_ROOT", root)
    monkeypatch.delenv(KEY, raising=False)
    monkeypatch.delenv("KINDRED_LOAD_LOCAL_ENV", raising=False)
    monkeypatch.delenv("CI", raising=False)

    cwd = tmp_path / "other"
    cwd.mkdir()
    (cwd / ".env").write_text(f"{KEY}=ignored-cwd-fixture\n", encoding="utf-8")
    monkeypatch.chdir(cwd)
    return root


@pytest.mark.parametrize(
    "local, exported, mode, expected",
    [
        (LOCAL_KEY, None, "development", LOCAL_KEY),
        (None, EXPORTED_KEY, "development", EXPORTED_KEY),
        (LOCAL_KEY, EXPORTED_KEY, "development", EXPORTED_KEY),
        (LOCAL_KEY, "", "development", None),
        ("", None, "development", None),
        (None, None, "development", None),
        (LOCAL_KEY, None, "ci", None),
        (LOCAL_KEY, None, "disabled", None),
        (LOCAL_KEY, None, "without_checkout", None),
        (LOCAL_KEY, EXPORTED_KEY, "without_checkout", EXPORTED_KEY),
        (LOCAL_KEY, None, "test_factory", None),
    ],
)
async def test_startup_configures_real_provider(
    checkout, monkeypatch, caplog, local, exported, mode, expected
):
    if local is not None:
        (checkout / ".env").write_text(
            f'export {KEY}="{local}" # fixture\n', encoding="utf-8"
        )
    if exported is not None:
        monkeypatch.setenv(KEY, exported)
    if mode == "ci":
        monkeypatch.setenv("CI", "true")
    elif mode == "disabled":
        monkeypatch.setenv("KINDRED_LOAD_LOCAL_ENV", "0")
    elif mode == "without_checkout":
        (checkout / ".git").unlink()

    constructed = []
    sent = []

    def respond(request: httpx.Request) -> httpx.Response:
        sent.append(request.url.params["api_key"])
        return httpx.Response(200, json={"projects": {"project": [{"id": 42}]}})

    class TestProvider(GlobalGivingProjectProvider):
        def __init__(
            self, *, api_key: str, cache_settings: DiscoveryCacheSettings
        ) -> None:
            constructed.append(api_key)
            super().__init__(
                api_key=api_key,
                transport=httpx.MockTransport(respond),
                cache_settings=cache_settings,
            )

    monkeypatch.setattr(main, "GlobalGivingProjectProvider", TestProvider)
    caplog.set_level(logging.DEBUG)

    if mode == "test_factory":
        app = main.create_app()
    else:
        config = Config("main:app", reload=True, log_config=None, proxy_headers=False)
        config.load()
        assert config.loaded_app is main.app
        app = main.app

    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            response = await client.get(PROJECTS)

    assert os.getenv(KEY) == exported
    for secret in (LOCAL_KEY, EXPORTED_KEY):
        assert secret not in caplog.text
        assert secret not in response.text

    if expected:
        assert constructed == sent == [expected]
        assert response.status_code == 200
        assert response.json()["items"][0]["id"] == "42"
    else:
        assert constructed == sent == []
        assert response.status_code == 503
        assert response.json() == {"code": "provider_unavailable"}


def test_default_env_root_is_relative_to_source():
    assert main.REPOSITORY_ROOT == Path(main.__file__).resolve().parents[1]
