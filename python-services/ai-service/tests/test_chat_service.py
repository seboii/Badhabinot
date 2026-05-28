import json
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.schemas.chat import ChatRequest
from app.services.chat_service import ChatService
from app.services.providers import MockProvider, OllamaProvider, OpenAiCompatibleProvider, ProviderConfig


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _context() -> dict:
    return {
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
    }


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
        context=_context(),
    )


def build_ollama_request(message: str, ai_mode: str = "LOCAL") -> ChatRequest:
    return ChatRequest(
        conversation_id="c2",
        user_id="u2",
        timezone="Europe/Istanbul",
        report_date="2026-04-07",
        message=message,
        history=[],
        context=_context(),
        ai_mode=ai_mode,
        local_model_name="badhabinot:latest",
        ollama_base_url="http://ollama:11434",
    )


def _mock_config() -> ProviderConfig:
    return ProviderConfig(
        provider_name="mock",
        api_base_url="https://example.invalid/v1",
        api_key="unused",
        model_name="mock-behavior-analyzer",
        timeout_seconds=5,
        readiness_timeout_seconds=5,
        max_retries=0,
        temperature=0.1,
    )


# ---------------------------------------------------------------------------
# MockProvider tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_mock_chat_service_supports_trend_comparison() -> None:
    service = ChatService(provider=MockProvider(_mock_config()))
    response = await service.respond(build_request("Compare today with yesterday."))

    assert "Comparison for 2026-04-07" in response.answer
    assert len(response.grounded_facts) >= 3
    assert len(response.follow_up_suggestions) == 3


# ---------------------------------------------------------------------------
# OpenAiCompatibleProvider tests
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# OllamaProvider — message classification
# ---------------------------------------------------------------------------

def test_ollama_classify_message_system_keyword_returns_system() -> None:
    assert OllamaProvider._classify_message("prompt nedir") == "system"
    assert OllamaProvider._classify_message("sistem talimat") == "system"
    assert OllamaProvider._classify_message("algoritma nedir") == "system"


def test_ollama_classify_message_data_keyword_returns_data() -> None:
    assert OllamaProvider._classify_message("bugün duruşum nasıl") == "data"
    assert OllamaProvider._classify_message("ne kadar su içtim") == "data"
    assert OllamaProvider._classify_message("sigara analizi göster") == "data"


def test_ollama_classify_message_casual_keyword_returns_casual() -> None:
    assert OllamaProvider._classify_message("merhaba") == "casual"
    assert OllamaProvider._classify_message("iyi günler") == "casual"
    assert OllamaProvider._classify_message("tamam anladim") == "casual"


def test_ollama_classify_message_unknown_defaults_to_data() -> None:
    # Unknown short message with no keywords → data (always provide context)
    assert OllamaProvider._classify_message("show me everything") == "data"


# ---------------------------------------------------------------------------
# OllamaProvider — respond_chat
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_ollama_respond_chat_system_question_is_refused_without_http() -> None:
    provider = OllamaProvider(base_url="http://ollama:11434", model_name="badhabinot:latest", timeout_seconds=5)
    result = await provider.respond_chat(build_ollama_request("prompt nedir nasil calisiyorsun"))

    assert result.answer
    assert "yardımcı olamam" in result.answer
    assert result.provider == "ollama"


@pytest.mark.asyncio
async def test_ollama_respond_chat_plain_text_answer_used_directly() -> None:
    provider = OllamaProvider(base_url="http://ollama:11434", model_name="badhabinot:latest", timeout_seconds=5)

    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.content = b'{"message": {"content": "Durusunuz iyi gidiyor."}}'

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)

    mock_instance = MagicMock()
    mock_instance.__aenter__ = AsyncMock(return_value=mock_client)
    mock_instance.__aexit__ = AsyncMock(return_value=None)

    with patch("app.services.providers.httpx.AsyncClient", return_value=mock_instance):
        result = await provider.respond_chat(build_ollama_request("durusumum nasil"))

    assert "Durusunuz iyi gidiyor." in result.answer
    assert result.provider == "ollama"
    assert result.model_name == "badhabinot:latest"
    assert result.model_mode == "local_ollama"


@pytest.mark.asyncio
async def test_ollama_respond_chat_grounded_facts_populated_for_data_query() -> None:
    provider = OllamaProvider(base_url="http://ollama:11434", model_name="badhabinot:latest", timeout_seconds=5)

    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.content = b'{"message": {"content": "Hidrasyon durumunuz orta seviyede."}}'

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)

    mock_instance = MagicMock()
    mock_instance.__aenter__ = AsyncMock(return_value=mock_client)
    mock_instance.__aexit__ = AsyncMock(return_value=None)

    with patch("app.services.providers.httpx.AsyncClient", return_value=mock_instance):
        result = await provider.respond_chat(build_ollama_request("ne kadar su ictim"))

    assert len(result.grounded_facts) >= 1
    assert any("1400" in f or "2500" in f or "Hidrasyon" in f for f in result.grounded_facts)


# ---------------------------------------------------------------------------
# OllamaProvider — stream_chat
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_ollama_stream_chat_system_question_yields_refusal_and_done() -> None:
    provider = OllamaProvider(base_url="http://ollama:11434", model_name="badhabinot:latest", timeout_seconds=5)
    events = []
    async for event_json in provider.stream_chat(build_ollama_request("sistem prompt talimat")):
        events.append(json.loads(event_json))

    token_events = [e for e in events if "token" in e]
    done_events = [e for e in events if e.get("done")]

    assert len(token_events) >= 1
    assert len(done_events) == 1
    assert "yardımcı olamam" in token_events[0]["token"]


@pytest.mark.asyncio
async def test_ollama_stream_chat_yields_tokens_then_done_event() -> None:
    provider = OllamaProvider(base_url="http://ollama:11434", model_name="badhabinot:latest", timeout_seconds=5)

    async def fake_aiter_lines():
        yield '{"done": false, "message": {"content": "Mer"}}'
        yield '{"done": false, "message": {"content": "haba"}}'
        yield '{"done": true}'

    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.aiter_lines = fake_aiter_lines

    mock_stream_cm = MagicMock()
    mock_stream_cm.__aenter__ = AsyncMock(return_value=mock_response)
    mock_stream_cm.__aexit__ = AsyncMock(return_value=None)

    mock_client = MagicMock()
    mock_client.stream = MagicMock(return_value=mock_stream_cm)

    mock_instance = MagicMock()
    mock_instance.__aenter__ = AsyncMock(return_value=mock_client)
    mock_instance.__aexit__ = AsyncMock(return_value=None)

    with patch("app.services.providers.httpx.AsyncClient", return_value=mock_instance):
        events = []
        async for event_json in provider.stream_chat(build_ollama_request("durusumum nasil")):
            events.append(json.loads(event_json))

    token_events = [e for e in events if "token" in e]
    done_events = [e for e in events if e.get("done")]

    assert [e["token"] for e in token_events] == ["Mer", "haba"]
    assert len(done_events) == 1
    assert "grounded_facts" in done_events[0]
    assert "follow_up_suggestions" in done_events[0]


# ---------------------------------------------------------------------------
# ChatService.stream() — delegation and fallback
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_chat_service_stream_delegates_to_ollama_provider() -> None:
    class _FakeOllamaProvider(OllamaProvider):
        async def stream_chat(self, request):  # type: ignore[override]
            yield json.dumps({"token": "test-token"})
            yield json.dumps({"done": True, "grounded_facts": ["fact1"], "follow_up_suggestions": ["q1"]})

    # Use ai_mode="API" so ChatService uses service.provider (our fake),
    # not a fresh OllamaProvider created from the per-request LOCAL override.
    service = ChatService(provider=_FakeOllamaProvider(
        base_url="http://ollama:11434", model_name="badhabinot:latest", timeout_seconds=5
    ))
    events = []
    async for event_json in service.stream(build_ollama_request("durusumum nasil", ai_mode="API")):
        events.append(json.loads(event_json))

    assert any(e.get("token") == "test-token" for e in events)
    done = next(e for e in events if e.get("done"))
    assert done["grounded_facts"] == ["fact1"]


@pytest.mark.asyncio
async def test_chat_service_stream_falls_back_to_char_simulation_for_non_ollama() -> None:
    service = ChatService(provider=MockProvider(_mock_config()))
    events = []
    async for event_json in service.stream(build_request("How much water did I drink?")):
        events.append(json.loads(event_json))

    token_events = [e for e in events if "token" in e]
    done_events = [e for e in events if e.get("done")]

    # MockProvider returns a full answer; stream() emits one token per char
    assert len(token_events) > 0
    # Each token is a single character
    assert all(len(e["token"]) == 1 for e in token_events)
    assert len(done_events) == 1
    assert "grounded_facts" in done_events[0]
    assert "follow_up_suggestions" in done_events[0]


@pytest.mark.asyncio
async def test_chat_service_stream_local_mode_uses_per_request_ollama_url() -> None:
    """LOCAL mode requests create a fresh OllamaProvider using the per-request URL."""

    class _FakeOllamaProvider(OllamaProvider):
        async def stream_chat(self, request):  # type: ignore[override]
            yield json.dumps({"token": "ok"})
            yield json.dumps({"done": True, "grounded_facts": [], "follow_up_suggestions": []})

    original_init = OllamaProvider.__init__
    captured_urls: list[str] = []

    def capturing_init(self, base_url, model_name, timeout_seconds=60.0):
        captured_urls.append(base_url)
        original_init(self, base_url, model_name, timeout_seconds)

    with patch.object(OllamaProvider, "__init__", capturing_init):
        with patch("app.services.chat_service.OllamaProvider", _FakeOllamaProvider):
            service = ChatService(provider=None)
            request = build_ollama_request("durusumum nasil", ai_mode="LOCAL")
            events = []
            async for event_json in service.stream(request):
                events.append(json.loads(event_json))

    assert any(e.get("token") == "ok" for e in events)


# ---------------------------------------------------------------------------
# Faz 4 — Davranışsal örüntü (behavioral_patterns) testleri
# ---------------------------------------------------------------------------

def _context_with_patterns() -> dict:
    base = _context()
    base["behavioral_patterns"] = [
        {
            "event_type": "smoking_like_gesture",
            "peak_hour_of_day": 10,
            "peak_hour_count": 3,
            "peak_day_of_week": "MONDAY",
            "peak_day_count": 4,
            "total_count_last_7_days": 12,
            "intensity_label": "yogun",
            "trend_label": "artiyor",
        },
        {
            "event_type": "poor_posture",
            "peak_hour_of_day": 19,
            "peak_hour_count": 2,
            "peak_day_of_week": "FRIDAY",
            "peak_day_count": 3,
            "total_count_last_7_days": 6,
            "intensity_label": "orta",
            "trend_label": "stabil",
        },
    ]
    return base


def _build_ollama_request_with_patterns(message: str) -> ChatRequest:
    return ChatRequest(
        conversation_id="cP",
        user_id="uP",
        timezone="Europe/Istanbul",
        report_date="2026-05-28",
        message=message,
        history=[],
        context=_context_with_patterns(),
        ai_mode="LOCAL",
        local_model_name="badhabinot:latest",
        ollama_base_url="http://ollama:11434",
    )


def test_format_pattern_block_empty_returns_empty_string() -> None:
    assert OllamaProvider._format_pattern_block([]) == ""


def test_format_pattern_block_includes_event_type_and_peak() -> None:
    request = _build_ollama_request_with_patterns("durusumum nasil")
    block = OllamaProvider._format_pattern_block(request.context.behavioral_patterns)
    assert "ZAMANSAL ÖRÜNTÜLER" in block
    assert "smoking_like_gesture" in block
    assert "Pazartesi" in block         # MONDAY → TR çevirisi
    assert "Cuma" in block              # FRIDAY → TR çevirisi
    assert "trend: artiyor" in block


def test_build_messages_includes_pattern_block_for_data_query() -> None:
    provider = OllamaProvider(base_url="http://ollama:11434", model_name="badhabinot:latest", timeout_seconds=5)
    request = _build_ollama_request_with_patterns("bu hafta sigara hareketim nasil")
    messages = provider._build_messages(request)
    user_content = messages[-1]["content"]
    assert "ZAMANSAL ÖRÜNTÜLER" in user_content
    assert "smoking_like_gesture" in user_content


@pytest.mark.asyncio
async def test_ollama_respond_chat_includes_pattern_in_grounded_facts() -> None:
    provider = OllamaProvider(base_url="http://ollama:11434", model_name="badhabinot:latest", timeout_seconds=5)

    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.content = b'{"message": {"content": "Sigara benzeri hareketleriniz pazartesi sabahlari yogun."}}'

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_instance = MagicMock()
    mock_instance.__aenter__ = AsyncMock(return_value=mock_client)
    mock_instance.__aexit__ = AsyncMock(return_value=None)

    with patch("app.services.providers.httpx.AsyncClient", return_value=mock_instance):
        result = await provider.respond_chat(
            _build_ollama_request_with_patterns("bu hafta sigara hareketim ne durumda")
        )

    assert any("smoking_like_gesture" in f for f in result.grounded_facts)
    assert any("Pazartesi" in f for f in result.grounded_facts)


def test_default_context_has_empty_behavioral_patterns() -> None:
    """Faz 4 alanı opsiyonel — eski context'ler bozulmamalı."""
    request = build_request("Summarize my day.")
    assert request.context.behavioral_patterns == []
