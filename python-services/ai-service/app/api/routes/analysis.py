from fastapi import APIRouter, Depends

from app.core.security import require_internal_api_key
from app.schemas.analysis import AnalysisRequest, AnalysisResponse
from app.services.analysis_service import get_analysis_service

router = APIRouter(prefix="/v1/analysis", tags=["analysis"])


@router.post("/interpret", response_model=AnalysisResponse)
async def interpret(
    request: AnalysisRequest,
    _: None = Depends(require_internal_api_key),
) -> AnalysisResponse:
    return await get_analysis_service().analyze(request)
