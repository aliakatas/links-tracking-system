from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from importlib.metadata import version

from fastapi import FastAPI

from links_tracking_system.api.router import api_router
from links_tracking_system.db.session import get_engine


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    yield
    # Only dispose an engine that was actually created; don't build one here.
    if get_engine.cache_info().currsize:
        get_engine().dispose()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Links Tracking System",
        version=version("links-tracking-system"),
        lifespan=lifespan,
    )
    app.include_router(api_router)
    return app


app = create_app()
