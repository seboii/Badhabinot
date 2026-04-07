from fastapi.testclient import TestClient

from app.main import app


def test_analyze_requires_internal_api_key() -> None:
    client = TestClient(app)

    response = client.post(
        "/v1/vision/analyze",
        json={
            "request_id": "req-1",
            "user_id": "user-1",
            "session_id": "session-1",
            "frame_id": "frame-1",
            "captured_at": "2026-04-06T09:00:00Z",
            "image_base64": "aW52YWxpZA==",
            "image_content_type": "image/jpeg",
        },
    )

    assert response.status_code == 401
