from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.services.analysis_service import get_analysis_service

router = APIRouter()


@router.get("/health", tags=["health"])
async def health() -> dict:
    return {
        "status": "ok",
        "service": settings.app_name,
        "version": settings.app_version,
        "provider": settings.ai_provider,
        "model": settings.model_name,
    }


@router.get("/ready", tags=["health"])
async def ready() -> JSONResponse:
    readiness = await get_analysis_service().readiness()
    status_code = 200 if readiness.get("ready") else 503
    body = {
        "status": "ready" if status_code == 200 else "not_ready",
        "service": settings.app_name,
        "version": settings.app_version,
        **readiness,
    }
    return JSONResponse(status_code=status_code, content=body)
