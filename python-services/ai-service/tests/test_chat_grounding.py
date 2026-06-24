"""Sohbet grounding düzeltmeleri için testler.

1) GENERAL_CHAT data-bloğu kapısı Türkçe-diakritik DUYARSIZ olmalı
   (duruş/duruşumu/durusum hepsi tetiklemeli) → tek aksanlı harf yüzünden kaçmasın.
2) Bugün ölçüm yoksa yanıltıcı 100/100 yerine SON ÖLÇÜMLÜ güne düşmeli;
   hiç veri yoksa "kayıtlı ölçüm yok" deyip uydurmamasını istemeli.
"""
from __future__ import annotations

from app.schemas.chat import ChatRequest
from app.services.providers import OpenAiCompatibleProvider


def _ctx(**overrides) -> dict:
    ctx = {
        "hydration_progress_ml": 1400,
        "water_goal_ml": 2500,
        "analyses_completed": 18,
        "posture_alert_count": 6,
        "hand_movement_count": 3,
        "smoking_like_count": 1,
        "reminder_count": 4,
        "poor_posture_ratio": 0.38,
        "summary": "x",
        "recommendations": [],
        "facts": [],
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
                "poor_posture_ratio": 0.38,   # → duruş skoru 62.0/100
                "summary": "son ölçüm",
            }
        ],
        "total_sessions_last_7_days": 7,
        "analyses_completed_last_7_days": 121,
        "hydration_last_7_days_ml": 9600,
        "comparison_to_previous_day": "",
    }
    ctx.update(overrides)
    return ctx


def _req(message: str, **ctx_overrides) -> ChatRequest:
    return ChatRequest(
        conversation_id="c", user_id="u", timezone="Europe/Istanbul",
        report_date="2026-04-08", message=message, history=[], context=_ctx(**ctx_overrides),
    )


def test_gate_is_diacritic_insensitive() -> None:
    inc = OpenAiCompatibleProvider._persona_includes_data_block
    assert inc(_req("Bugün duruşumu merak ediyorum"))   # aksanlı
    assert inc(_req("durusum nasildi"))                  # aksansız/typo-yakın
    assert not inc(_req("merhaba nasilsin"))             # veri sorusu değil


def test_grounding_falls_back_to_last_measured_day_when_today_empty() -> None:
    req = _req("duruşum nasıl", analyses_completed=0, hydration_progress_ml=0,
               posture_alert_count=0, poor_posture_ratio=0.0)
    block = OpenAiCompatibleProvider._build_grounding_block(req.context, req.report_date)
    assert "En son ölçümlü gün" in block
    assert "62.0/100" in block        # son ölçüm (1-0.38), bugünün 100/100'ü DEĞİL
    assert "100/100" not in block


def test_grounding_says_no_data_when_truly_empty() -> None:
    req = _req("duruşum nasıl", analyses_completed=0, hydration_progress_ml=0,
               posture_alert_count=0, poor_posture_ratio=0.0, recent_daily_snapshots=[])
    block = OpenAiCompatibleProvider._build_grounding_block(req.context, req.report_date)
    assert "ölçüm yok" in block.lower()
    assert "UYDURMA" in block
