import logging
from importlib.metadata import version
from typing import Annotated

from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import Engine, text
from sqlalchemy.exc import SQLAlchemyError

from links_tracking_system.db.session import get_engine
from links_tracking_system.schemas.meta import (
    HealthResponse,
    MigrationStatusResponse,
    VersionResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["meta"])


@router.get("/version")
def get_version() -> VersionResponse:
    return VersionResponse(version=version("links-tracking-system"))


@router.get(
    "/health",
    responses={status.HTTP_503_SERVICE_UNAVAILABLE: {"model": HealthResponse}},
)
def get_health(
    engine: Annotated[Engine, Depends(get_engine)], response: Response
) -> HealthResponse:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except SQLAlchemyError:
        logger.exception("Database health check failed")
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return HealthResponse(status="degraded", database="unavailable")
    return HealthResponse(status="ok", database="ok")


@router.get(
    "/meta/migrations",
    responses={
        status.HTTP_503_SERVICE_UNAVAILABLE: {"description": "Database unavailable"}
    },
)
def get_migration_status(
    engine: Annotated[Engine, Depends(get_engine)],
) -> MigrationStatusResponse:
    # Read-only: compares the database's revision with the head in migrations/.
    # alembic.ini is resolved relative to the working directory (the project root).
    head = ScriptDirectory.from_config(Config("alembic.ini")).get_current_head()
    try:
        with engine.connect() as conn:
            current = MigrationContext.configure(conn).get_current_revision()
    except SQLAlchemyError:
        logger.exception("Could not read the current migration revision")
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE, "Database unavailable"
        ) from None
    return MigrationStatusResponse(
        current_revision=current,
        head_revision=head,
        up_to_date=current == head,
    )
