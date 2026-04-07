from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.core.config import settings

router = APIRouter()


@router.get("/health", tags=["health"])
async def health() -> dict:
    return {
        "status": "ok",
        "service": settings.app_name,
        "version": settings.app_version,
    }


@router.get("/ready", tags=["health"])
async def ready() -> JSONResponse:
    return JSONResponse(
        status_code=200,
        content={
            "status": "ready",
            "service": settings.app_name,
            "version": settings.app_version,
        },
    )
