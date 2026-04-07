from functools import lru_cache

from fastapi import HTTPException

from app.core.config import settings
from app.schemas.analysis import AnalysisRequest, AnalysisResponse, ModelDescriptor
from app.services.providers import (
    AnalysisProvider,
    MockProvider,
    OpenAiCompatibleProvider,
    ProviderConfig,
    ProviderConfigurationError,
    ProviderInvocationError,
)


class AnalysisService:
    def __init__(self, provider: AnalysisProvider | None = None) -> None:
        self.provider = provider

    async def analyze(self, request: AnalysisRequest) -> AnalysisResponse:
        if not request.settings.remote_inference_accepted:
            raise HTTPException(status_code=409, detail="remote inference consent is required for API-based analysis")

        if not request.vision.subject_present:
            return AnalysisResponse(
                request_id=request.request_id,
                behavior_type="none",
                confidence=0.0,
                scores={"hand_movement_pattern": 0.0, "smoking_like_gesture": 0.0},
                summary="No subject was detected clearly enough in the frame to analyze behavior.",
                recommendation="Move the subject into frame and capture another image.",
                grounded_facts=[],
                model=ModelDescriptor(provider="none", name="not-invoked", mode="not_invoked"),
            )

        try:
            result = await self._provider().analyze(request)
        except ProviderConfigurationError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except ProviderInvocationError as exc:
            raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc

        return AnalysisResponse(
            request_id=request.request_id,
            behavior_type=result.behavior_type,
            confidence=result.confidence,
            scores=result.scores,
            summary=result.summary,
            recommendation=result.recommendation,
            grounded_facts=result.grounded_facts,
            model=ModelDescriptor(
                provider=result.provider,
                name=result.model_name,
                mode=result.model_mode,
            ),
        )

    async def readiness(self) -> dict:
        try:
            readiness = await self._provider().readiness()
        except ProviderConfigurationError as exc:
            return {
                "ready": True,
                "provider_ready": False,
                "provider": settings.ai_provider,
                "model": settings.model_name,
                "mode": "invalid_configuration",
                "provider_status": "misconfigured",
                "reason": str(exc),
            }

        return {
            "ready": True,
            "provider_ready": readiness.ready,
            **readiness.details,
        }

    def _provider(self) -> AnalysisProvider:
        if self.provider is None:
            self.provider = _build_provider()
        return self.provider


def _build_provider() -> AnalysisProvider:
    config = ProviderConfig(
        provider_name=settings.ai_provider,
        api_base_url=settings.ai_api_base_url,
        api_key=settings.ai_api_key,
        model_name=settings.model_name,
        timeout_seconds=settings.ai_timeout_seconds,
        readiness_timeout_seconds=settings.ai_readiness_timeout_seconds,
        max_retries=settings.ai_max_retries,
        temperature=settings.ai_temperature,
    )

    if settings.ai_provider == "mock":
        return MockProvider(config)
    if settings.ai_provider == "openai-compatible":
        return OpenAiCompatibleProvider(config)

    raise ProviderConfigurationError(f"Unsupported AI_PROVIDER value: {settings.ai_provider}")


@lru_cache(maxsize=1)
def get_analysis_service() -> AnalysisService:
    return AnalysisService()
