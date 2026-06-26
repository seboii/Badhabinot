from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.services.analysis_service import get_analysis_service
from app.services.providers import OllamaProvider

router = APIRouter()


@router.get("/health", tags=["health"])
async def health() -> dict:
    readiness = await get_analysis_service().readiness()
    return {
        "status": "ok",
        "service": settings.app_name,
        "version": settings.app_version,
        "provider": settings.effective_provider,
        # Ollama sağlayıcıda gerçek kullanılan model ollama_model_name'dir
        # (model_name openai-compatible içindir) → doğru modeli raporla.
        "model": settings.ollama_model_name if settings.effective_provider == "ollama" else settings.model_name,
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


@router.get("/health/ollama", tags=["health"])
async def ollama_health(
    base_url: str = Query(default="http://localhost:11434"),
    model_name: str = Query(default="llama3.2:3b"),
) -> dict:
    """Check whether Ollama is reachable and whether the requested model is installed."""
    provider = OllamaProvider(base_url=base_url, model_name=model_name)
    readiness = await provider.readiness()
    return readiness.details
