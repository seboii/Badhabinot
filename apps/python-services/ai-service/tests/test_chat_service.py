import httpx
import pytest

from app.schemas.chat import ChatRequest
from app.services.chat_service import ChatService
from app.services.providers import MockProvider, OpenAiCompatibleProvider, ProviderConfig


def build_request(message: str) -> ChatRequest:
    return ChatRequest(
        conversation_id="c1",
        user_id="u1",
        timezone="Europe/Istanbul",
        report_date="2026-04-07",
        message=message,
        history=[
            {
                "role": "user",
                "content": "Summarize my day.",
                "created_at": "2026-04-07T08:00:00Z",
            }
        ],
        context={
            "hydration_progress_ml": 1400,
            "water_goal_ml": 2500,
            "analyses_completed": 18,
            "posture_alert_count": 6,
            "hand_movement_count": 3,
            "smoking_like_count": 1,
            "reminder_count": 4,
            "poor_posture_ratio": 0.38,
            "summary": "Today included posture and hydration gaps with one smoking-like cue.",
            "recommendations": ["Take posture resets.", "Increase hydration."],
            "facts": [{"label": "posture_alert_count", "value": "6"}],
            "recent_events": [],
            "recent_reminders": [],
            "recent_daily_snapshots": [
                {
                    "report_date": "2026-04-07",
                    "analyses_completed": 18,
                    "posture_alert_count": 6,
                    "hand_movement_count": 3,
                    "smoking_like_count": 1,
                    "reminder_count": 4,
                    "hydration_progress_ml": 1400,
                    "water_goal_ml": 2500,
                    "poor_posture_ratio": 0.38,
                    "summary": "Today included posture and hydration gaps with one smoking-like cue.",
                },
                {
                    "report_date": "2026-04-06",
                    "analyses_completed": 22,
                    "posture_alert_count": 4,
                    "hand_movement_count": 2,
                    "smoking_like_count": 0,
                    "reminder_count": 3,
                    "hydration_progress_ml": 1700,
                    "water_goal_ml": 2500,
                    "poor_posture_ratio": 0.27,
                    "summary": "Yesterday was calmer.",
                },
            ],
            "recent_event_type_counts": {"poor_posture": 6, "hand_movement_pattern": 3},
            "recent_reminder_type_counts": {"water_reminder": 2, "posture_reminder": 2},
            "recent_sessions": [
                {
                    "session_id": "s1",
                    "status": "STOPPED",
                    "started_at": "2026-04-07T08:00:00Z",
                    "ended_at": "2026-04-07T09:15:00Z",
                    "duration_minutes": 75,
                }
            ],
            "total_sessions_last_7_days": 7,
            "total_session_minutes_last_7_days": 480,
            "hydration_last_7_days_ml": 9600,
            "analyses_completed_last_7_days": 121,
            "comparison_to_previous_day": "Compared with 2026-04-06: posture alerts +2, hydration -300 ml, smoking-like cues +1.",
            "data_gaps": [],
        },
    )


@pytest.mark.asyncio
async def test_mock_chat_service_supports_trend_comparison() -> None:
    provider = MockProvider(
        ProviderConfig(
            provider_name="mock",
            api_base_url="https://example.invalid/v1",
            api_key="unused",
            model_name="mock-behavior-analyzer",
            timeout_seconds=5,
            readiness_timeout_seconds=5,
            max_retries=0,
            temperature=0.1,
        )
    )
    service = ChatService(provider=provider)

    response = await service.respond(build_request("Compare today with yesterday."))

    assert "Comparison for 2026-04-07" in response.answer
    assert len(response.grounded_facts) >= 3
    assert len(response.follow_up_suggestions) == 3


@pytest.mark.asyncio
async def test_openai_chat_normalization_fills_missing_facts_and_follow_ups() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1/chat/completions"
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": '{"answer":"Short grounded answer.","grounded_facts":[],"follow_up_suggestions":[]}'
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
    response = await provider.respond_chat(build_request("Summarize my day."))

    assert response.answer == "Short grounded answer."
    assert len(response.grounded_facts) >= 3
    assert len(response.follow_up_suggestions) == 3
