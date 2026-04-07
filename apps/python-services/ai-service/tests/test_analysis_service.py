import httpx
import pytest

from app.schemas.analysis import (
    AnalysisRequest,
    AnalysisSettings,
    VisionContext,
    VisionDetection,
    VisionEvidence,
    VisionSignals,
)
from app.services.analysis_service import AnalysisService
from app.services.providers import OpenAiCompatibleProvider, ProviderConfig


def build_request() -> AnalysisRequest:
    return AnalysisRequest(
        request_id="r1",
        user_id="u1",
        session_id="s1",
        frame_id="f1",
        captured_at="2026-04-06T09:00:00Z",
        timezone="Europe/Istanbul",
        image_base64="ZmFrZQ==",
        image_content_type="image/jpeg",
        settings=AnalysisSettings(
            sensitivity="MEDIUM",
            model_mode="API",
            remote_inference_accepted=True,
        ),
        vision=VisionContext(
            subject_present=True,
            posture_state="poor",
            frame_width=128,
            frame_height=128,
            detections=[
                VisionDetection(
                    event_type="poor_posture",
                    confidence=0.72,
                    severity="medium",
                    recommendation_hint="Reset posture.",
                    evidence=VisionEvidence(
                        face_detected=True,
                        upper_body_detected=True,
                        hand_count=1,
                        posture_alignment_score=0.72,
                        hand_face_proximity_score=0.45,
                        hand_motion_score=0.22,
                        repetitive_motion_score=0.18,
                        repeated_hand_to_face_score=0.12,
                        elongated_object_score=0.08,
                    ),
                )
            ],
            signals=VisionSignals(
                brightness_mean=120.0,
                edge_density=0.2,
                center_edge_density=0.5,
                posture_risk_score=0.72,
                hand_face_proximity_score=0.8,
                elongated_object_score=0.1,
                focus_score=42.0,
                posture_confidence=0.88,
                posture_alignment_score=0.72,
                hand_motion_score=0.38,
                repetitive_motion_score=0.31,
                smoking_gesture_score=0.22,
                face_size_ratio=0.14,
            ),
        ),
    )


@pytest.mark.asyncio
async def test_analysis_service_normalizes_openai_compatible_response() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1/chat/completions"
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": (
                                '{"behavior_type":"hand_movement_pattern","confidence":0.83,'
                                '"scores":{"hand_movement_pattern":0.83,"smoking_like_gesture":0.08},'
                                '"summary":"Repeated hand motion is likely.","recommendation":"Ask for a pause.",'
                                '"grounded_facts":["Hand motion score reached 0.38."]}'
                            )
                        }
                    }
                ]
            },
        )

    provider = OpenAiCompatibleProvider(
        ProviderConfig(
            provider_name="openai-compatible",
            api_base_url="https://provider.example/v1",
            api_key="test-key",
            model_name="test-model",
            timeout_seconds=5,
            readiness_timeout_seconds=5,
            max_retries=0,
            temperature=0.1,
        ),
        transport=httpx.MockTransport(handler),
    )
    service = AnalysisService(provider=provider)

    response = await service.analyze(build_request())

    assert response.behavior_type == "hand_movement_pattern"
    assert response.confidence == pytest.approx(0.83)
    assert response.model.provider == "openai-compatible"
    assert response.summary == "Repeated hand motion is likely."
    assert response.grounded_facts == ["Hand motion score reached 0.38."]


@pytest.mark.asyncio
async def test_analysis_service_requires_remote_consent() -> None:
    request = build_request()
    request.settings.remote_inference_accepted = False
    service = AnalysisService()

    with pytest.raises(Exception) as exc:
        await service.analyze(request)

    assert "remote inference consent" in str(exc.value)
