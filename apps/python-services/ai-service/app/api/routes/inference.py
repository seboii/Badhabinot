from fastapi import APIRouter, Depends

from app.core.security import require_internal_api_key
from app.schemas.inference import InferenceRequest, InferenceResponse
from app.services.inference_service import InferenceService

router = APIRouter(prefix="/v1/inference", tags=["inference"])
service = InferenceService()


@router.post("/predict", response_model=InferenceResponse)
async def predict(
    request: InferenceRequest,
    _: None = Depends(require_internal_api_key),
) -> InferenceResponse:
    return service.predict(request)
