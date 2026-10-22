from fastapi import APIRouter

from links_tracking_system.api.routes import meta, urls

api_router = APIRouter()
api_router.include_router(meta.router)
api_router.include_router(urls.router)
