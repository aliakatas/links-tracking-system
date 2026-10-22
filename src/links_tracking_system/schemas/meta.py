from typing import Literal

from pydantic import BaseModel


class VersionResponse(BaseModel):
    version: str


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded"]
    database: Literal["ok", "unavailable"]
