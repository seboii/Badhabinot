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


def test_face_register_requires_internal_api_key() -> None:
    client = TestClient(app)

    response = client.post(
        "/v1/vision/face/register",
        json={"user_id": "user-1", "image_base64": "aW52YWxpZA=="},
    )

    assert response.status_code == 401


def test_face_delete_requires_internal_api_key() -> None:
    client = TestClient(app)

    response = client.delete("/v1/vision/face/user-1")

    assert response.status_code == 401


def test_face_status_requires_internal_api_key() -> None:
    client = TestClient(app)

    response = client.get("/v1/vision/face/user-1/status")

    assert response.status_code == 401


def test_session_export_json_requires_internal_api_key() -> None:
    client = TestClient(app)

    response = client.get("/v1/vision/sessions/session-1/export.json")

    assert response.status_code == 401


def test_session_export_csv_requires_internal_api_key() -> None:
    client = TestClient(app)

    response = client.get("/v1/vision/sessions/session-1/export.csv")

    assert response.status_code == 401
