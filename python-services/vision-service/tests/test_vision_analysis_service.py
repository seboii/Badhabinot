import base64

import cv2
import numpy as np
import pytest

from app.schemas.vision import VisionAnalysisRequest
from app.services.vision_analysis_service import VisionAnalysisService


@pytest.mark.asyncio
async def test_analyze_returns_dimensions_and_signals() -> None:
    image = np.full((64, 64, 3), 180, dtype=np.uint8)
    ok, encoded = cv2.imencode(".jpg", image)
    assert ok

    service = VisionAnalysisService()

    request = VisionAnalysisRequest(
        request_id="req-1",
        user_id="user-1",
        session_id="session-1",
        frame_id="frame-1",
        captured_at="2026-04-06T09:00:00Z",
        image_base64=base64.b64encode(encoded.tobytes()).decode("utf-8"),
        image_content_type="image/jpeg",
    )

    response = await service.analyze(request)

    assert response.subject_present is True
    assert response.processing.frame_width == 64
    assert response.processing.frame_height == 64
    assert response.signals.posture_risk_score >= 0.0
    assert response.processing.focus_score >= 0.0
