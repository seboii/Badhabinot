import httpx
from fastapi import HTTPException

from app.core.config import settings
from app.schemas.inference import InferenceRequest, InferenceResponse


class AiClient:
    async def predict(self, request: InferenceRequest) -> tuple[InferenceResponse, int]:
        timeout = httpx.Timeout(settings.ai_service_timeout_seconds)
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    f"{settings.ai_service_url}/v1/inference/predict",
                    json=request.model_dump(mode="json"),
                    headers={"X-Internal-Api-Key": settings.internal_api_key},
                )
                response.raise_for_status()
                data = response.json()
                elapsed_ms = int(response.elapsed.total_seconds() * 1000)
                return InferenceResponse.model_validate(data), elapsed_ms
        except httpx.TimeoutException as exc:
            raise HTTPException(status_code=504, detail="ai-service timeout") from exc
        except httpx.HTTPStatusError as exc:
            raise HTTPException(status_code=502, detail=f"ai-service error: {exc.response.text}") from exc
        except httpx.HTTPError as exc:
            raise HTTPException(status_code=502, detail="ai-service unavailable") from exc
