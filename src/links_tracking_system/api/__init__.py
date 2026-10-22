from fastapi import APIRouter

from links_tracking_system.api.routes import meta

api_router = APIRouter()
api_router.include_router(meta.router)