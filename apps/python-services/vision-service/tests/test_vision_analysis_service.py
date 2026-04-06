import base64

import cv2
import numpy as np
import pytest

from app.schemas.inference import InferenceResponse
from app.schemas.vision import VisionAnalysisRequest, VisionSettings
from app.services.vision_analysis_service import VisionAnalysisService


class DummyAiClient:
    async def predict(self, request):
        return (
            InferenceResponse(
                request_id=request.request_id,
                behavior_type="nail_biting",
                confidence=0.81,
                scores={"nail_biting": 0.81, "smoking": 0.13},
                model={"name": "dummy", "version": "test", "mode": "local"},
            ),
            12,
        )


@pytest.mark.asyncio
async def test_analyze_returns_dimensions_and_inference() -> None:
    image = np.full((64, 64, 3), 180, dtype=np.uint8)
    ok, encoded = cv2.imencode(".jpg", image)
    assert ok

    service = VisionAnalysisService()
    service.ai_client = DummyAiClient()

    request = VisionAnalysisRequest(
        request_id="req-1",
        user_id="user-1",
        session_id="session-1",
        frame_id="frame-1",
        captured_at="2026-04-06T09:00:00Z",
        image_base64=base64.b64encode(encoded.tobytes()).decode("utf-8"),
        image_content_type="image/jpeg",
        settings=VisionSettings(
            sensitivity="MEDIUM",
            model_mode="LOCAL",
            remote_inference_accepted=False,
        ),
    )

    response = await service.analyze(request)

    assert response.subject_present is True
    assert response.processing.frame_width == 64
    assert response.processing.frame_height == 64
    assert response.inference.behavior_type == "nail_biting"
