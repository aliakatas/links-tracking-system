# Links Tracking System

A small FastAPI + SQLModel service backed by Postgres for tracking links.

## Current state

- `POST /urls` creates a URL record (`source_key`, `name`, `tags`); duplicate `source_key` returns 409.
- `GET /version` returns the package version (no DB access).
- `GET /health` checks database connectivity (503 if unreachable).
- Not yet implemented: schema migrations or table creation, and read/update/delete endpoints.

## Setup

Requires [uv](https://docs.astral.sh/uv/) (Python 3.14) and Podman or Docker for Postgres.

```sh
uv sync
cp .env.example .env   # then set POSTGRES_PASSWORD and keep DATABASE_URL in sync
```

## Run

Postgres only, with the API running locally (auto-reload):

```sh
podman compose up -d db
uv run uvicorn links_tracking_system.main:app --reload
```

Everything in containers (use `docker compose` if not on Podman):

```sh
podman compose up --build
```

The API listens on <http://127.0.0.1:8000>. Interactive docs are at `/docs`.

## Debug

- Check the API and DB are up: `curl localhost:8000/health`
- Container logs: `podman compose logs -f api db`
- Debugger: launch `uvicorn links_tracking_system.main:app` (without `--reload`) from your IDE's Python debug configuration.
- Reset local data: `podman compose down` and delete `.pgdata/`.
