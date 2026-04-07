from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.services.analysis_service import get_analysis_service

router = APIRouter()


@router.get("/health", tags=["health"])
async def health() -> dict:
    readiness = await get_analysis_service().readiness()
    return {
        "status": "ok",
        "service": settings.app_name,
        "version": settings.app_version,
        "provider": settings.ai_provider,
        "model": settings.model_name,
        "provider_ready": readiness.get("provider_ready", True),
        "provider_status": readiness.get("provider_status", "unknown"),
        "provider_reason": readiness.get("reason"),
    }


@router.get("/ready", tags=["health"])
async def ready() -> JSONResponse:
    readiness = await get_analysis_service().readiness()
    provider_ready = readiness.get("provider_ready", True)
    body = {
        "status": "ready" if provider_ready else "ready_with_warnings",
        "service": settings.app_name,
        "version": settings.app_version,
        **readiness,
    }
    return JSONResponse(status_code=200, content=body)
