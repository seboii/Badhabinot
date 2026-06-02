"""PARİTE: fine-tune eğitim promptu == üretim çıkarım promptu.

Eğer bu test geçerse, modelin eğitimde gördüğü user-content ile üretimde
(OllamaProvider) göreceği user-content BİREBİR aynıdır → "programa göre eğitim"
garanti. Hem BEHAVIOR_COACH (zengin) hem GENERAL_CHAT (basit) + zengin sinyaller.
"""

from __future__ import annotations

from datetime import date, datetime, timezone

from app.schemas.chat import (
    BehavioralPattern as PBehavioralPattern,
    ChatContext,
    ChatEvent,
    ChatReminder,
    ChatRequest,
)
from app.services.providers import OllamaProvider

from finetune.prompt_format import compose_user_message
from finetune.schema import (
    BehavioralPattern,
    CoachingExample,
    EventLite,
    MonitoringContext,
    ReminderLite,
)

_REPORT = date(2026, 5, 30)
_ISO = _REPORT.isoformat()


def _production_context() -> ChatContext:
    return ChatContext(
        hydration_progress_ml=1500,
        water_goal_ml=2500,
        analyses_completed=120,
        posture_alert_count=4,
        hand_movement_count=6,
        smoking_like_count=3,
        reminder_count=2,
        poor_posture_ratio=0.22,
        summary="Karisik bir gun.",
        recommendations=[],
        facts=[],
        recent_events=[
            ChatEvent(event_type="SLOUCHING", confidence=0.82, severity="medium",
                      interpretation="Omurga egimi yuksek",
                      occurred_at=datetime(2026, 5, 30, 15, 30, tzinfo=timezone.utc), evidence={}),
            ChatEvent(event_type="DROWSY", confidence=0.75, severity="high",
                      interpretation="Goz kapanma orani yuksek",
                      occurred_at=datetime(2026, 5, 30, 16, 5, tzinfo=timezone.utc), evidence={}),
        ],
        recent_reminders=[
            ChatReminder(reminder_type="hydration", message="1 saattir su icmedin",
                         trigger_reason="interval", occurred_at=datetime(2026, 5, 30, 14, 0, tzinfo=timezone.utc)),
        ],
        recent_event_type_counts={"SLOUCHING": 5, "DROWSY": 2, "FACE_TOUCH": 3},
        total_sessions_last_7_days=8,
        total_session_minutes_last_7_days=420,
        hydration_last_7_days_ml=12500,
        analyses_completed_last_7_days=940,
        comparison_to_previous_day="Compared with 2026-05-29: posture alerts +1, hydration -200 ml.",
        data_gaps=["Historical comparison is limited."],
        behavioral_patterns=[
            PBehavioralPattern(event_type="smoking_like_gesture", peak_hour_of_day=15, peak_hour_count=6,
                               peak_day_of_week="FRIDAY", peak_day_count=9, total_count_last_7_days=18,
                               intensity_label="orta", trend_label="artiyor"),
        ],
    )


def _training_context() -> MonitoringContext:
    """Üretim bağlamıyla AYNI değerler (eğitim tarafı)."""
    return MonitoringContext(
        report_date=_ISO,
        hydration_progress_ml=1500, water_goal_ml=2500, analyses_completed=120,
        posture_alert_count=4, hand_movement_count=6, smoking_like_count=3,
        poor_posture_ratio=0.22, summary="Karisik bir gun.",
        comparison_to_previous_day="Compared with 2026-05-29: posture alerts +1, hydration -200 ml.",
        behavioral_patterns=[
            BehavioralPattern(event_type="smoking_like_gesture", peak_hour_of_day=15, peak_hour_count=6,
                              peak_day_of_week="FRIDAY", peak_day_count=9, total_count_last_7_days=18,
                              intensity_label="orta", trend_label="artiyor"),
        ],
        recent_events=[
            EventLite("SLOUCHING", "medium", 0.82, "Omurga egimi yuksek", 15),
            EventLite("DROWSY", "high", 0.75, "Goz kapanma orani yuksek", 16),
        ],
        recent_reminders=[ReminderLite("hydration", "1 saattir su icmedin", 14)],
        recent_event_type_counts={"SLOUCHING": 5, "DROWSY": 2, "FACE_TOUCH": 3},
        total_sessions_last_7_days=8, total_session_minutes_last_7_days=420,
        hydration_last_7_days_ml=12500, analyses_completed_last_7_days=940,
        data_gaps=["Historical comparison is limited."],
    )


def _prod_user_content(message: str, persona: str) -> str:
    req = ChatRequest(
        conversation_id="c", user_id="u", report_date=_REPORT, message=message,
        history=[], context=_production_context(), chat_persona=persona,
    )
    provider = OllamaProvider(base_url="http://x", model_name="m")
    return provider._build_messages(req)[-1]["content"]


def test_parity_behavior_coach_data():
    message = "Bugün duruşum nasıldı?"  # 'duruş' → data dalı
    train = compose_user_message(CoachingExample(
        persona="BEHAVIOR_COACH", kind="answer", question=message,
        ideal_answer="x", context=_training_context()))
    assert train == _prod_user_content(message, "BEHAVIOR_COACH")
    # zengin sinyallerin gerçekten girdiğini de doğrula
    assert "SON DAVRANIŞ OLAYLARI" in train
    assert "SLOUCHING (medium, %82) saat 15" in train
    assert "SON 7 GÜN" in train


def test_parity_general_chat_data():
    message = "Skorum kaç?"  # 'skor' → veri bloğu
    train = compose_user_message(CoachingExample(
        persona="GENERAL_CHAT", kind="answer", question=message,
        ideal_answer="x", context=_training_context()))
    assert train == _prod_user_content(message, "GENERAL_CHAT")
    assert "Bugünün özeti" in train
    assert "HATIRLATICILAR" in train


def test_parity_analyst():
    message = "Bu oturumu analiz et"
    train = compose_user_message(CoachingExample(
        persona="ANALYST", kind="answer", question=message,
        ideal_answer="x", context=_training_context()))
    assert train == _prod_user_content(message, "ANALYST")
    # ANALYST = zengin blok + 'Görev:' + özet/Öneri talimatı
    assert "BUGÜNÜN PERFORMANS ÖZETİ" in train
    assert "Görev: Bu oturumu analiz et" in train
    assert "'Öneri:'" in train
    assert "SON DAVRANIŞ OLAYLARI" in train  # zengin sinyaller de giriyor
