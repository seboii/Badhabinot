"""Chat route authentication and basic contract tests."""

from fastapi.testclient import TestClient

from app.main import app


def _chat_body() -> dict:
    return {
        "conversation_id": "c1",
        "user_id": "u1",
        "timezone": "UTC",
        "report_date": "2026-04-07",
        "message": "hello",
        "history": [],
        "context": {
            "hydration_progress_ml": 1000,
            "water_goal_ml": 2500,
            "analyses_completed": 5,
            "posture_alert_count": 1,
            "hand_movement_count": 0,
            "smoking_like_count": 0,
            "reminder_count": 1,
            "poor_posture_ratio": 0.1,
            "summary": "Normal day.",
            "recommendations": [],
            "facts": [],
            "recent_events": [],
            "recent_reminders": [],
        },
    }


def test_chat_respond_requires_internal_api_key() -> None:
    client = TestClient(app)
    response = client.post("/v1/chat/respond", json=_chat_body())
    assert response.status_code == 401


def test_chat_stream_requires_internal_api_key() -> None:
    client = TestClient(app)
    response = client.post("/v1/chat/stream", json=_chat_body())
    assert response.status_code == 401


def test_chat_respond_rejects_missing_body() -> None:
    client = TestClient(app, raise_server_exceptions=False)
    response = client.post(
        "/v1/chat/respond",
        content=b"",
        headers={"Content-Type": "application/json"},
    )
    # 401 before body validation — auth check happens first
    assert response.status_code == 401


def test_chat_stream_rejects_missing_body() -> None:
    client = TestClient(app, raise_server_exceptions=False)
    response = client.post(
        "/v1/chat/stream",
        content=b"",
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 401
