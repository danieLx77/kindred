# syntax=docker/dockerfile:1

FROM python:3.13.3-slim-bookworm AS base

COPY --from=ghcr.io/astral-sh/uv:0.12.19 /uv /uvx /usr/local/bin/
COPY --from=node:22.20.0-bookworm-slim /usr/local/bin/node /usr/local/bin/node

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_PYTHON_DOWNLOADS=0 \
    UV_LINK_MODE=copy \
    RUFF_CACHE_DIR=/home/app/.cache/ruff \
    PYTEST_ADDOPTS="-o cache_dir=/home/app/.cache/pytest" \
    PATH="/app/.venv/bin:$PATH"

RUN useradd --uid 10001 --create-home --shell /bin/sh app \
    && mkdir /app \
    && chown app:app /app

WORKDIR /app
USER app

FROM base AS dev

COPY --chown=app:app pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/home/app/.cache/uv,uid=10001,gid=10001 \
    uv sync --locked --no-install-project

COPY --chown=app:app . .
RUN --mount=type=cache,target=/home/app/.cache/uv,uid=10001,gid=10001 \
    uv sync --locked

EXPOSE 8000
CMD ["uv", "run", "--locked", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
