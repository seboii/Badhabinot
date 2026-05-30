"""finetune.schema + build_dataset — saf python, torch gerekmez (her zaman koşar)."""

from __future__ import annotations

import pytest

from finetune.build_dataset import build, synthesize
from finetune.schema import (
    BehavioralPattern,
    ChatTurn,
    CoachingExample,
    MonitoringContext,
    dataset_stats,
    dump_jsonl,
    load_jsonl,
)


def _ctx() -> MonitoringContext:
    return MonitoringContext(report_date="2026-05-30", hydration_progress_ml=1500,
                             water_goal_ml=2500, poor_posture_ratio=0.2)


def test_valid_example_passes_validation():
    ex = CoachingExample(persona="BEHAVIOR_COACH", kind="answer", question="Duruşum?",
                         ideal_answer="Skorun 80/100.", context=_ctx())
    ex.validate()  # raise etmemeli


def test_invalid_persona_rejected():
    ex = CoachingExample(persona="WRONG", kind="answer", question="q",
                         ideal_answer="a", context=_ctx())
    with pytest.raises(ValueError):
        ex.validate()


def test_custom_persona_requires_prompt():
    ex = CoachingExample(persona="CUSTOM", kind="answer", question="q",
                         ideal_answer="a", context=_ctx())
    with pytest.raises(ValueError):
        ex.validate()
    ex.custom_system_prompt = "Sen bir koçsun."
    ex.validate()


def test_behavioral_pattern_bounds():
    p = BehavioralPattern(event_type="x", peak_hour_of_day=30, peak_hour_count=1,
                          peak_day_of_week="MONDAY", peak_day_count=1,
                          total_count_last_7_days=1, intensity_label="az", trend_label="stabil")
    with pytest.raises(ValueError):
        p.validate()


def test_context_ratio_bounds():
    ctx = MonitoringContext(report_date="2026-05-30", poor_posture_ratio=1.5)
    with pytest.raises(ValueError):
        ctx.validate()


def test_jsonl_roundtrip(tmp_path):
    ex = CoachingExample(
        persona="GENERAL_CHAT", kind="answer", question="Su?",
        ideal_answer="1500/2500 ml.", context=_ctx(),
        history=[ChatTurn(role="user", content="selam")],
        grounded_facts=["Hidrasyon: 1500/2500 ml"], tags=["t"],
    )
    path = tmp_path / "d.jsonl"
    assert dump_jsonl([ex], path) == 1
    loaded = load_jsonl(path)
    assert len(loaded) == 1
    assert loaded[0].persona == "GENERAL_CHAT"
    assert loaded[0].history[0].content == "selam"
    assert loaded[0].context.water_goal_ml == 2500


def test_load_jsonl_reports_bad_line(tmp_path):
    path = tmp_path / "bad.jsonl"
    path.write_text('{"persona": "BEHAVIOR_COACH"}\n', encoding="utf-8")
    with pytest.raises(ValueError) as exc:
        load_jsonl(path)
    assert "bad.jsonl:1" in str(exc.value)


def test_synthesize_is_deterministic_and_valid():
    a = synthesize(20, seed=1)
    b = synthesize(20, seed=1)
    assert len(a) == 20
    assert [e.question for e in a] == [e.question for e in b]
    for e in a:
        e.validate()


def test_build_writes_gold_and_synthetic(tmp_path):
    out = tmp_path / "ds.jsonl"
    n = build(str(out), synthetic=10, seed=3)
    examples = load_jsonl(out)
    assert n == len(examples) >= 10
    stats = dataset_stats(examples)
    assert stats["total"] == n
    assert set(stats["by_kind"]).issubset({"answer", "casual", "refuse"})
