"""Tests for Module F: BehaviorStateStore — all event types, thresholds, severities, cooldowns."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import pytest

from app.services.vision.behavior_engine import (
    BehaviorFrameInput,
    BehaviorStateStore,
    _EVENT_SEVERITY,
)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _t(seconds: float = 0.0) -> datetime:
    return datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc) + timedelta(seconds=seconds)


def _input(**kwargs: Any) -> BehaviorFrameInput:
    defaults: dict[str, Any] = dict(
        captured_at=_t(),
        session_id="s1",
        user_id="u1",
        face_detected=True,
        face_authenticated=True,
        auth_confidence=1.0,
        owner_tracked=True,
        owner_gaze_looking_at_screen=True,
        strangers_in_frame=0,
    )
    defaults.update(kwargs)
    return BehaviorFrameInput(**defaults)


# ─────────────────────────────────────────────────────────────────────────────
# 1. Severity mapping
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("event_type,expected_severity", [
    ("FACE_TOUCH",       "low"),
    ("SMOKING",          "high"),
    ("EATING",           "medium"),
    ("DRINKING",         "medium"),
    ("LEFT_SCREEN",      "high"),
    ("SLOUCHING",        "medium"),
    ("DROWSY",           "high"),
    ("YAWNING",          "low"),
    ("DISTRACTED",       "medium"),
    ("UNKNOWN_PERSON",   "high"),
    ("GAZE_AWAY",        "medium"),
    ("OWNER_ABSENT",     "high"),
    ("STRANGER_DETECTED","high"),
])
def test_severity_mapping(event_type: str, expected_severity: str) -> None:
    assert _EVENT_SEVERITY[event_type] == expected_severity


# ─────────────────────────────────────────────────────────────────────────────
# 2. Immediate events (no duration threshold)
# ─────────────────────────────────────────────────────────────────────────────

def test_face_touch_fires_immediately() -> None:
    store = BehaviorStateStore()
    events = store.evaluate(_input(face_touch_detected=True))
    assert any(e.event_type == "FACE_TOUCH" for e in events)


def test_face_touch_not_fired_without_touch() -> None:
    store = BehaviorStateStore()
    events = store.evaluate(_input(face_touch_detected=False))
    assert not any(e.event_type == "FACE_TOUCH" for e in events)


def test_yawning_fires_immediately_above_threshold() -> None:
    store = BehaviorStateStore()
    events = store.evaluate(_input(is_yawning=True, mar=0.75))
    assert any(e.event_type == "YAWNING" for e in events)


def test_yawning_not_fired_below_threshold() -> None:
    store = BehaviorStateStore()
    events = store.evaluate(_input(is_yawning=False, mar=0.40))
    assert not any(e.event_type == "YAWNING" for e in events)


def test_unknown_person_fires_when_face_not_authenticated() -> None:
    store = BehaviorStateStore()
    events = store.evaluate(_input(face_detected=True, face_authenticated=False, auth_confidence=0.3))
    assert any(e.event_type == "UNKNOWN_PERSON" for e in events)


def test_unknown_person_not_fired_when_authenticated() -> None:
    store = BehaviorStateStore()
    events = store.evaluate(_input(face_detected=True, face_authenticated=True))
    assert not any(e.event_type == "UNKNOWN_PERSON" for e in events)


def test_stranger_detected_fires_with_one_stranger() -> None:
    store = BehaviorStateStore()
    events = store.evaluate(_input(strangers_in_frame=1))
    assert any(e.event_type == "STRANGER_DETECTED" for e in events)


def test_stranger_not_fired_when_zero_strangers() -> None:
    store = BehaviorStateStore()
    events = store.evaluate(_input(strangers_in_frame=0))
    assert not any(e.event_type == "STRANGER_DETECTED" for e in events)


def test_drinking_fires_when_bottle_near_mouth() -> None:
    store = BehaviorStateStore()
    events = store.evaluate(_input(bottle_near_mouth=True))
    assert any(e.event_type == "DRINKING" for e in events)


def test_eating_fires_when_cup_near_mouth() -> None:
    store = BehaviorStateStore()
    events = store.evaluate(_input(cup_near_mouth=True))
    assert any(e.event_type == "EATING" for e in events)


def test_smoking_fires_on_hand_to_mouth_without_drink() -> None:
    store = BehaviorStateStore()
    events = store.evaluate(_input(mouth_touch_detected=True))
    assert any(e.event_type == "SMOKING" for e in events)


def test_smoking_not_fired_when_drink_object_present() -> None:
    store = BehaviorStateStore()
    events = store.evaluate(_input(mouth_touch_detected=True, bottle_near_mouth=True))
    assert not any(e.event_type == "SMOKING" for e in events)


# ─────────────────────────────────────────────────────────────────────────────
# 3. Duration-based events — LEFT_SCREEN (5 s)
# ─────────────────────────────────────────────────────────────────────────────

def test_left_screen_not_fired_before_threshold() -> None:
    store = BehaviorStateStore()
    for delta in (0, 2, 4):
        events = store.evaluate(_input(
            captured_at=_t(delta), session_id="ls", face_detected=False,
            face_authenticated=False,
        ))
        assert not any(e.event_type == "LEFT_SCREEN" for e in events), \
            f"LEFT_SCREEN fired at t+{delta}s"


def test_left_screen_fires_at_threshold() -> None:
    store = BehaviorStateStore()
    for delta in (0, 3):
        store.evaluate(_input(captured_at=_t(delta), session_id="ls2", face_detected=False, face_authenticated=False))
    events = store.evaluate(_input(captured_at=_t(6), session_id="ls2", face_detected=False, face_authenticated=False))
    assert any(e.event_type == "LEFT_SCREEN" for e in events)


def test_left_screen_resets_when_face_returns() -> None:
    store = BehaviorStateStore()
    # Trigger LEFT_SCREEN
    for delta in (0, 6):
        store.evaluate(_input(captured_at=_t(delta), session_id="ls3", face_detected=False, face_authenticated=False))
    # Face returns
    store.evaluate(_input(captured_at=_t(7), session_id="ls3", face_detected=True))
    # Face absent again for only 1 s — should NOT fire
    events = store.evaluate(_input(captured_at=_t(8), session_id="ls3", face_detected=False, face_authenticated=False))
    assert not any(e.event_type == "LEFT_SCREEN" for e in events)


# ─────────────────────────────────────────────────────────────────────────────
# 4. Duration-based events — DROWSY (2 s)
# ─────────────────────────────────────────────────────────────────────────────

def test_drowsy_not_fired_before_threshold() -> None:
    store = BehaviorStateStore()
    events = store.evaluate(_input(is_drowsy=True, ear=0.20))
    assert not any(e.event_type == "DROWSY" for e in events)


def test_drowsy_fires_after_sustained_low_ear() -> None:
    store = BehaviorStateStore()
    store.evaluate(_input(captured_at=_t(0), session_id="d1", is_drowsy=True, ear=0.20))
    events = store.evaluate(_input(captured_at=_t(3), session_id="d1", is_drowsy=True, ear=0.20))
    assert any(e.event_type == "DROWSY" for e in events)


def test_drowsy_timer_resets_on_normal_ear() -> None:
    store = BehaviorStateStore()
    store.evaluate(_input(captured_at=_t(0), session_id="d2", is_drowsy=True, ear=0.20))
    store.evaluate(_input(captured_at=_t(1), session_id="d2", is_drowsy=False, ear=0.35))
    events = store.evaluate(_input(captured_at=_t(2), session_id="d2", is_drowsy=True, ear=0.20))
    assert not any(e.event_type == "DROWSY" for e in events)


# ─────────────────────────────────────────────────────────────────────────────
# 5. Duration-based events — SLOUCHING (10 s)
# ─────────────────────────────────────────────────────────────────────────────

def test_slouching_not_fired_before_threshold() -> None:
    store = BehaviorStateStore()
    for delta in (0, 5, 9):
        events = store.evaluate(_input(captured_at=_t(delta), session_id="sl1", is_slouching=True, posture_score=60))
        assert not any(e.event_type == "SLOUCHING" for e in events)


def test_slouching_fires_after_sustained_poor_posture() -> None:
    store = BehaviorStateStore()
    for delta in (0, 5):
        store.evaluate(_input(captured_at=_t(delta), session_id="sl2", is_slouching=True, posture_score=60))
    events = store.evaluate(_input(captured_at=_t(11), session_id="sl2", is_slouching=True, posture_score=60))
    assert any(e.event_type == "SLOUCHING" for e in events)


# ─────────────────────────────────────────────────────────────────────────────
# 6. Duration-based events — DISTRACTED (8 s via gaze_off_screen)
# ─────────────────────────────────────────────────────────────────────────────

def test_distracted_not_fired_before_threshold() -> None:
    store = BehaviorStateStore()
    for delta in (0, 4, 7):
        events = store.evaluate(_input(captured_at=_t(delta), session_id="dist1", gaze_off_screen=True))
        assert not any(e.event_type == "DISTRACTED" for e in events)


def test_distracted_fires_after_sustained_gaze_off_screen() -> None:
    store = BehaviorStateStore()
    for delta in (0, 5):
        store.evaluate(_input(captured_at=_t(delta), session_id="dist2", gaze_off_screen=True))
    events = store.evaluate(_input(captured_at=_t(9), session_id="dist2", gaze_off_screen=True))
    assert any(e.event_type == "DISTRACTED" for e in events)


# ─────────────────────────────────────────────────────────────────────────────
# 7. Session isolation
# ─────────────────────────────────────────────────────────────────────────────

def test_sessions_are_isolated() -> None:
    """State from session A must not pollute session B."""
    store = BehaviorStateStore()
    # Drive session A into DROWSY state
    store.evaluate(_input(captured_at=_t(0), session_id="A", is_drowsy=True))
    store.evaluate(_input(captured_at=_t(3), session_id="A", is_drowsy=True))

    # Session B's first frame should see no DROWSY
    events_b = store.evaluate(_input(captured_at=_t(0), session_id="B", is_drowsy=True))
    assert not any(e.event_type == "DROWSY" for e in events_b)


# ─────────────────────────────────────────────────────────────────────────────
# 8. Confidence bounds
# ─────────────────────────────────────────────────────────────────────────────

def test_all_event_confidences_are_in_unit_range() -> None:
    """Every emitted event must have confidence in [0.0, 1.0]."""
    store = BehaviorStateStore()
    # Emit as many different events as possible in one batch
    events = store.evaluate(_input(
        captured_at=_t(10),
        session_id="conf",
        face_detected=False,
        face_authenticated=False,
        owner_tracked=False,
        strangers_in_frame=2,
        face_touch_detected=True,
        is_yawning=True,
        mar=0.80,
        bottle_near_mouth=True,
        cup_near_mouth=True,
        mouth_touch_detected=True,
        # Force LEFT_SCREEN by building absence streak first
    ))
    for event in events:
        assert 0.0 <= event.confidence <= 1.0, \
            f"Event {event.event_type} has out-of-range confidence {event.confidence}"
