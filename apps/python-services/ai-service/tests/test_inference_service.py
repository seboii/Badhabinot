from app.schemas.inference import InferenceRequest, InferenceSettings, VisionMetrics
from app.services.inference_service import InferenceService


def test_predict_returns_nail_biting_for_high_hand_face_signal() -> None:
    service = InferenceService()
    request = InferenceRequest(
        request_id="r1",
        user_id="u1",
        session_id="s1",
        frame_id="f1",
        captured_at="2026-04-06T09:00:00Z",
        settings=InferenceSettings(
            sensitivity="MEDIUM",
            model_mode="LOCAL",
            remote_inference_accepted=False,
        ),
        metrics=VisionMetrics(
            brightness_mean=120.0,
            edge_density=0.2,
            center_edge_density=0.5,
            posture_risk_score=0.4,
            hand_face_proximity_score=0.9,
            elongated_object_score=0.2,
        ),
    )

    response = service.predict(request)

    assert response.behavior_type == "nail_biting"
    assert response.confidence >= 0.6
