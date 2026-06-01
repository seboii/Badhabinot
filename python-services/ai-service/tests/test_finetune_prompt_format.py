"""finetune.prompt_format + evaluate metrikleri — saf python (torch gerekmez)."""

from __future__ import annotations

from finetune.evaluate import grounding_score, is_plaintext, is_refusal, is_turkish
from finetune.prompt_format import (
    BEHAVIOR_COACH_SYSTEM_PROMPT,
    build_chat_messages,
    build_inference_messages,
    compose_user_message,
    includes_data_block,
)
from finetune.schema import CoachingExample, MonitoringContext


def _coach_example() -> CoachingExample:
    return CoachingExample(
        persona="BEHAVIOR_COACH", kind="answer", question="Bugün duruşum nasıldı?",
        ideal_answer="Duruş skorun 80/100, 2 uyarı aldın.",
        context=MonitoringContext(report_date="2026-05-30", hydration_progress_ml=1500,
                                  water_goal_ml=2500, poor_posture_ratio=0.2,
                                  posture_alert_count=2),
    )


def test_behavior_coach_uses_rich_summary_block():
    ex = _coach_example()
    assert includes_data_block(ex) is True
    user_msg = compose_user_message(ex)
    assert "PERFORMANS ÖZETİ" in user_msg          # BEHAVIOR_COACH zengin blok
    assert "kötü duruş oranı" in user_msg          # yalnızca zengin blokta var
    assert "Soru: Bugün duruşum nasıldı?" in user_msg


def test_general_chat_casual_excludes_data_block():
    ex = CoachingExample(persona="GENERAL_CHAT", kind="casual", question="Merhaba",
                         ideal_answer="Merhaba!", context=MonitoringContext(report_date="2026-05-30"))
    assert includes_data_block(ex) is False
    assert compose_user_message(ex) == "Merhaba"


def test_general_chat_data_keyword_triggers_block():
    ex = CoachingExample(persona="GENERAL_CHAT", kind="answer", question="Skorum kaç?",
                         ideal_answer="...", context=MonitoringContext(report_date="2026-05-30"))
    assert includes_data_block(ex) is True


def test_build_chat_messages_structure():
    ex = _coach_example()
    msgs = build_chat_messages(ex)
    assert msgs[0]["role"] == "system"
    assert msgs[0]["content"] == BEHAVIOR_COACH_SYSTEM_PROMPT
    assert msgs[-1]["role"] == "assistant"
    assert msgs[-1]["content"] == ex.ideal_answer
    # inference = hedef (assistant) hariç
    assert build_inference_messages(ex) == msgs[:-1]


def test_grounding_score_rewards_context_numbers():
    ex = _coach_example()
    # 80 = (1-0.2)*100, 2 = posture_alert_count → bağlamda var
    assert grounding_score("Duruş skorun 80/100, 2 uyarı aldın.", ex.context) == 1.0


def test_grounding_score_penalizes_hallucinated_numbers():
    ex = _coach_example()
    # 999 bağlamda yok → düşük skor
    assert grounding_score("Skorun 999/100.", ex.context) < 1.0


def test_grounding_score_no_numbers_is_one():
    ex = _coach_example()
    assert grounding_score("Genel olarak iyisin.", ex.context) == 1.0


def test_turkish_and_english_detection():
    assert is_turkish("Bugün duruşun iyiydi, böyle devam et.") is True
    assert is_turkish("Today your posture was good and you are doing well.") is False


def test_refusal_and_plaintext_detection():
    assert is_refusal("Bu konuda sana yardımcı olamam.") is True
    assert is_refusal("Tabii, skorun 80.") is False
    assert is_plaintext("Skorun 80/100.") is True
    assert is_plaintext('{"answer": "x"}') is False
