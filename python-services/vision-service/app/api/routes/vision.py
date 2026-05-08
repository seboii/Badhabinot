from fastapi import APIRouter, Depends, Query

from app.core.security import require_internal_api_key
from app.schemas.vision import VisionAnalysisRequest, VisionAnalysisResponse
from app.services.vision_analysis_service import VisionAnalysisService

router = APIRouter(prefix="/v1/vision", tags=["vision"])
service = VisionAnalysisService()


@router.post("/analyze", response_model=VisionAnalysisResponse)
async def analyze(
    request: VisionAnalysisRequest,
    render_overlay: bool = Query(default=False, description="Return server-rendered annotated frame as base64 JPEG"),
    _: None = Depends(require_internal_api_key),
) -> VisionAnalysisResponse:
    return await service.analyze(request, render_overlay=render_overlay)
