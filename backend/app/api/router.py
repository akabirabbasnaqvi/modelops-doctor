from fastapi import APIRouter

from app.api.routes.health import router as health_router
from app.api.routes.model_versions import router as model_versions_router
from app.api.routes.projects import router as projects_router


api_router = APIRouter()

api_router.include_router(health_router)
api_router.include_router(projects_router)
api_router.include_router(model_versions_router)
