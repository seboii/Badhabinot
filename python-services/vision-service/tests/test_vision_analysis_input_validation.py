import base64

import cv2
import numpy as np
import pytest
from fastapi import HTTPException

from app.schemas.vision import VisionAnalysisRequest
from app.services.vision_analysis_service import VisionAnalysisService


@pytest.mark.asyncio
async def test_analyze_rejects_invalid_base64_payload() -> None:
    service = VisionAnalysisService()
    request = VisionAnalysisRequest(
        request_id="req-invalid",
        user_id="user-1",
        session_id="session-1",
        frame_id="frame-1",
        captured_at="2026-04-08T09:00:00Z",
        image_base64="this-is-not-valid-base64",
        image_content_type="image/jpeg",
    )

    with pytest.raises(HTTPException) as exc:
        await service.analyze(request)

    assert exc.value.status_code == 400
    assert exc.value.detail in {
        "invalid base64 image payload",
        "image payload could not be decoded",
    }


@pytest.mark.asyncio
async def test_analyze_accepts_data_url_prefixed_base64() -> None:
    image = np.full((32, 48, 3), 150, dtype=np.uint8)
    ok, encoded = cv2.imencode(".jpg", image)
    assert ok

    service = VisionAnalysisService()
    request = VisionAnalysisRequest(
        request_id="req-data-url",
        user_id="user-1",
        session_id="session-1",
        frame_id="frame-2",
        captured_at="2026-04-08T09:01:00Z",
        image_base64=f"data:image/jpeg;base64,{base64.b64encode(encoded.tobytes()).decode('utf-8')}",
        image_content_type="image/jpeg",
    )

    response = await service.analyze(request)

    assert response.processing.frame_width == 48
    assert response.processing.frame_height == 32
    assert response.signals.focus_score >= 0.0
