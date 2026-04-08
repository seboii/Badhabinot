import httpx
import pytest

from app.schemas.analysis import (
    AnalysisRequest,
    AnalysisSettings,
    VisionContext,
    VisionSignals,
)
from app.services.providers import OpenAiCompatibleProvider, ProviderConfig, ProviderInvocationError


def build_request() -> AnalysisRequest:
    return AnalysisRequest(
        request_id="r-provider-1",
        user_id="u1",
        session_id="s1",
        frame_id="f1",
        captured_at="2026-04-08T09:00:00Z",
        timezone="UTC",
        image_base64="ZmFrZQ==",
        image_content_type="image/jpeg",
        settings=AnalysisSettings(
            sensitivity="MEDIUM",
            model_mode="API",
            remote_inference_accepted=True,
        ),
        vision=VisionContext(
            subject_present=True,
            posture_state="good",
            frame_width=128,
            frame_height=128,
            detections=[],
            signals=VisionSignals(
                brightness_mean=120.0,
                edge_density=0.2,
                center_edge_density=0.4,
                posture_risk_score=0.25,
                hand_face_proximity_score=0.55,
                elongated_object_score=0.2,
                focus_score=40.0,
                posture_confidence=0.8,
                posture_alignment_score=0.7,
                hand_motion_score=0.6,
                repetitive_motion_score=0.45,
                smoking_gesture_score=0.1,
                face_size_ratio=0.15,
            ),
        ),
    )


def provider_with_transport(transport: httpx.MockTransport) -> OpenAiCompatibleProvider:
    return OpenAiCompatibleProvider(
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
        transport=transport,
    )


@pytest.mark.asyncio
async def test_provider_normalization_falls_back_to_scores_for_invalid_behavior_type() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": (
                                '{"behavior_type":"unsupported_label","confidence":1.9,'
                                '"scores":{"hand_movement_pattern":0.66,"smoking_like_gesture":0.12},'
                                '"summary":"","recommendation":"","grounded_facts":[]}'
                            )
                        }
                    }
                ]
            },
        )

    result = await provider_with_transport(httpx.MockTransport(handler)).analyze(build_request())

    assert result.behavior_type == "hand_movement_pattern"
    assert result.confidence == pytest.approx(1.0)
    assert result.scores["hand_movement_pattern"] == pytest.approx(0.66)
    assert result.summary
    assert result.recommendation


@pytest.mark.asyncio
async def test_provider_maps_rate_limit_to_service_unavailable() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(429, json={"error": "rate_limited"})

    with pytest.raises(ProviderInvocationError) as exc:
        await provider_with_transport(httpx.MockTransport(handler)).analyze(build_request())

    assert exc.value.status_code == 503
    assert "rate limit" in str(exc.value).lower()
