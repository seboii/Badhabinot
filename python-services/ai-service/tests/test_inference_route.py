from fastapi.testclient import TestClient

from app.main import app


def test_predict_requires_internal_api_key() -> None:
    client = TestClient(app)

    response = client.post(
        "/v1/inference/predict",
        json={
            "request_id": "r1",
            "user_id": "u1",
            "session_id": "s1",
            "frame_id": "f1",
            "captured_at": "2026-04-06T09:00:00Z",
            "timezone": "Europe/Istanbul",
            "image_base64": "ZmFrZQ==",
            "image_content_type": "image/jpeg",
            "settings": {
                "sensitivity": "MEDIUM",
                "model_mode": "API",
                "remote_inference_accepted": True,
            },
            "vision": {
                "subject_present": True,
                "posture_state": "good",
                "frame_width": 128,
                "frame_height": 128,
                "detections": [],
                "signals": {
                    "brightness_mean": 100.0,
                    "edge_density": 0.2,
                    "center_edge_density": 0.3,
                    "posture_risk_score": 0.4,
                    "hand_face_proximity_score": 0.5,
                    "elongated_object_score": 0.1,
                    "focus_score": 14.0,
                    "posture_confidence": 0.6,
                    "posture_alignment_score": 0.4,
                    "hand_motion_score": 0.2,
                    "repetitive_motion_score": 0.2,
                    "smoking_gesture_score": 0.1,
                    "face_size_ratio": 0.12,
                },
            },
        },
    )

    assert response.status_code == 401
