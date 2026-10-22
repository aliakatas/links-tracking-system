import logging
from importlib.metadata import version
from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import Engine, text
from sqlalchemy.exc import SQLAlchemyError

from links_tracking_system.db.session import get_engine
from links_tracking_system.schemas.meta import HealthResponse, VersionResponse

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