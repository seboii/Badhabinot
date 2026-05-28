"""Tests for Module D: VisionHandTracker — proximity detection, face/mouth touch, MediaPipe fallback."""

from __future__ import annotations

import math
from typing import Any
from unittest.mock import MagicMock

import numpy as np
import pytest

from app.services.vision.vision_hand_tracker import (
    VisionHandTracker,
    HandTrackingResult,
    _FACE_TOUCH_DISTANCE,
    _MOUTH_PROXIMITY,
)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _blank_image(h: int = 64, w: int = 64) -> np.ndarray:
    return np.zeros((h, w, 3), dtype=np.uint8)


def _make_hand_landmarks(
    palm_x: float = 0.5,
    palm_y: float = 0.5,
    fingertip_x: float | None = None,
    fingertip_y: float | None = None,
) -> list[tuple[float, float, float]]:
    """Build 21 hand landmarks.

    Indices [0, 5, 9, 13, 17] drive palm centre, so set them to (palm_x, palm_y).
    Indices 4, 8, 12, 16 are fingertips — set to fingertip_x/y when provided,
    else keep them at the palm position.
    """
    tip_x = fingertip_x if fingertip_x is not None else palm_x
    tip_y = fingertip_y if fingertip_y is not None else palm_y

    lms: list[tuple[float, float, float]] = []
    for i in range(21):
        if i in (0, 5, 9, 13, 17):
            lms.append((palm_x, palm_y, 0.0))
        elif i in (4, 8, 12, 16):
            lms.append((tip_x, tip_y, 0.0))
        else:
            lms.append((palm_x, palm_y, 0.0))
    return lms


def _make_face_landmarks(
    cx: float = 0.5,
    cy: float = 0.5,
    spread: float = 0.1,
    mouth_y: float = 0.6,
    n: int = 468,
) -> list[tuple[float, float, float]]:
    """Build *n* face landmarks centred at (cx, cy) with given spread.

    Landmarks 13 and 14 are set near *mouth_y* so proximity tests can be
    written predictably.
    """
    lms: list[tuple[float, float, float]] = []
    for i in range(n):
        lms.append((cx + spread * math.sin(i), cy + spread * math.cos(i), 0.0))
    # Override mouth landmarks
    lms[13] = (cx, mouth_y, 0.0)
    lms[14] = (cx, mouth_y + 0.01, 0.0)
    return lms


# ─────────────────────────────────────────────────────────────────────────────
# Fake MediaPipe objects
# ─────────────────────────────────────────────────────────────────────────────

class _FakeLm:
    def __init__(self, x: float, y: float, z: float = 0.0) -> None:
        self.x, self.y, self.z = x, y, z


class _FakeHandLms:
    def __init__(self, landmarks: list[tuple[float, float, float]]) -> None:
        self.landmark = [_FakeLm(*lm) for lm in landmarks]


class _FakeHandedness:
    class _Cls:
        def __init__(self, label: str) -> None:
            self.label = label

    def __init__(self, label: str) -> None:
        self.classification = [self._Cls(label)]


def _fake_result(
    hand_lms_list: list[list[tuple[float, float, float]]] | None,
    labels: list[str] | None = None,
) -> MagicMock:
    result = MagicMock()
    if hand_lms_list is None:
        result.multi_hand_landmarks = None
        result.multi_handedness = None
    else:
        result.multi_hand_landmarks = [_FakeHandLms(lms) for lms in hand_lms_list]
        if labels:
            result.multi_handedness = [_FakeHandedness(lbl) for lbl in labels]
        else:
            result.multi_handedness = None
    return result


def _make_tracker_with_fake_detector(fake_result_obj: Any) -> VisionHandTracker:
    """Return a VisionHandTracker whose internal detector always yields *fake_result_obj*."""
    tracker = VisionHandTracker()
    fake_detector = MagicMock()
    fake_detector.process.return_value = fake_result_obj
    tracker._detector = fake_detector
    return tracker


# ─────────────────────────────────────────────────────────────────────────────
# 1. MediaPipe unavailable
# ─────────────────────────────────────────────────────────────────────────────

def test_analyze_returns_none_when_mediapipe_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import app.services.vision.vision_hand_tracker as m
    monkeypatch.setattr(m, "_MP_AVAILABLE", False)

    tracker = VisionHandTracker()
    assert tracker.analyze(_blank_image()) is None


# ─────────────────────────────────────────────────────────────────────────────
# 2. No hands detected
# ─────────────────────────────────────────────────────────────────────────────

def test_analyze_returns_empty_result_when_no_hands(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import app.services.vision.vision_hand_tracker as m
    monkeypatch.setattr(m, "_MP_AVAILABLE", True)

    tracker = _make_tracker_with_fake_detector(_fake_result(None))
    result = tracker.analyze(_blank_image())

    assert result is not None
    assert isinstance(result, HandTrackingResult)
    assert result.hands == []
    assert result.face_touch_detected is False
    assert result.mouth_touch_detected is False


# ─────────────────────────────────────────────────────────────────────────────
# 3. Hand detected — handedness label
# ─────────────────────────────────────────────────────────────────────────────

def test_analyze_captures_handedness_label(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import app.services.vision.vision_hand_tracker as m
    monkeypatch.setattr(m, "_MP_AVAILABLE", True)

    lms = _make_hand_landmarks(0.5, 0.5)
    tracker = _make_tracker_with_fake_detector(_fake_result([lms], labels=["Right"]))
    result = tracker.analyze(_blank_image())

    assert result is not None
    assert len(result.hands) == 1
    assert result.hands[0].handedness == "Right"


def test_analyze_handedness_unknown_when_absent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import app.services.vision.vision_hand_tracker as m
    monkeypatch.setattr(m, "_MP_AVAILABLE", True)

    lms = _make_hand_landmarks(0.5, 0.5)
    tracker = _make_tracker_with_fake_detector(_fake_result([lms], labels=None))
    result = tracker.analyze(_blank_image())

    assert result is not None
    assert result.hands[0].handedness == "Unknown"


# ─────────────────────────────────────────────────────────────────────────────
# 4. _compute_proximity — unit tests (static method)
# ─────────────────────────────────────────────────────────────────────────────

def test_compute_proximity_returns_false_false_when_face_lm_none() -> None:
    hand_lm = _make_hand_landmarks(0.5, 0.5)
    near_face, near_mouth = VisionHandTracker._compute_proximity(hand_lm, None)
    assert near_face is False
    assert near_mouth is False


def test_compute_proximity_returns_false_false_when_face_lm_too_short() -> None:
    hand_lm = _make_hand_landmarks(0.5, 0.5)
    face_lm_short = [(0.5, 0.5, 0.0)] * 10  # only 10 — below the 15 minimum
    near_face, near_mouth = VisionHandTracker._compute_proximity(hand_lm, face_lm_short)
    assert near_face is False
    assert near_mouth is False


def test_compute_proximity_near_face_true_when_hand_overlaps_face() -> None:
    """Palm centre placed exactly at face centre → distance = 0 → near_face = True."""
    face_lm = _make_face_landmarks(cx=0.5, cy=0.5, spread=0.1)
    # Palm centre = (0.5, 0.5) — coincides with face centre
    hand_lm = _make_hand_landmarks(palm_x=0.5, palm_y=0.5)

    near_face, _ = VisionHandTracker._compute_proximity(hand_lm, face_lm)
    assert near_face is True


def test_compute_proximity_near_face_false_when_hand_far_away() -> None:
    """Palm at (0.9, 0.9), face at (0.2, 0.2) with spread 0.05 → not near."""
    face_lm = _make_face_landmarks(cx=0.2, cy=0.2, spread=0.05)
    hand_lm = _make_hand_landmarks(palm_x=0.9, palm_y=0.9)

    near_face, _ = VisionHandTracker._compute_proximity(hand_lm, face_lm)
    assert near_face is False


def test_compute_proximity_near_mouth_true_when_fingertip_close() -> None:
    """Index tip placed within _MOUTH_PROXIMITY of mouth centre."""
    face_lm = _make_face_landmarks(cx=0.5, cy=0.5, spread=0.1, mouth_y=0.6)
    mouth_cx = (face_lm[13][0] + face_lm[14][0]) / 2  # 0.5
    mouth_cy = (face_lm[13][1] + face_lm[14][1]) / 2  # ~0.605

    # Place all fingertips exactly at mouth centre
    hand_lm = _make_hand_landmarks(
        palm_x=0.5,
        palm_y=0.3,
        fingertip_x=mouth_cx,
        fingertip_y=mouth_cy,
    )
    _, near_mouth = VisionHandTracker._compute_proximity(hand_lm, face_lm)
    assert near_mouth is True


def test_compute_proximity_near_mouth_false_when_fingertip_far() -> None:
    """Fingertips far from mouth (different quadrant)."""
    face_lm = _make_face_landmarks(cx=0.5, cy=0.5, spread=0.1, mouth_y=0.6)
    hand_lm = _make_hand_landmarks(
        palm_x=0.1,
        palm_y=0.1,
        fingertip_x=0.05,
        fingertip_y=0.05,
    )
    _, near_mouth = VisionHandTracker._compute_proximity(hand_lm, face_lm)
    assert near_mouth is False


# ─────────────────────────────────────────────────────────────────────────────
# 5. Aggregated flags propagated through analyze()
# ─────────────────────────────────────────────────────────────────────────────

def test_analyze_face_touch_detected_when_near_face(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import app.services.vision.vision_hand_tracker as m
    monkeypatch.setattr(m, "_MP_AVAILABLE", True)

    face_lm = _make_face_landmarks(cx=0.5, cy=0.5, spread=0.1)
    hand_lm = _make_hand_landmarks(palm_x=0.5, palm_y=0.5)

    tracker = _make_tracker_with_fake_detector(_fake_result([hand_lm]))
    result = tracker.analyze(_blank_image(), face_landmarks=face_lm)

    assert result is not None
    assert result.face_touch_detected is True
    assert result.hands[0].near_face is True


def test_analyze_mouth_touch_detected_when_fingertip_near_mouth(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import app.services.vision.vision_hand_tracker as m
    monkeypatch.setattr(m, "_MP_AVAILABLE", True)

    face_lm = _make_face_landmarks(cx=0.5, cy=0.5, spread=0.1, mouth_y=0.6)
    mouth_cx = (face_lm[13][0] + face_lm[14][0]) / 2
    mouth_cy = (face_lm[13][1] + face_lm[14][1]) / 2

    hand_lm = _make_hand_landmarks(
        palm_x=0.5,
        palm_y=0.3,
        fingertip_x=mouth_cx,
        fingertip_y=mouth_cy,
    )

    tracker = _make_tracker_with_fake_detector(_fake_result([hand_lm]))
    result = tracker.analyze(_blank_image(), face_landmarks=face_lm)

    assert result is not None
    assert result.mouth_touch_detected is True
    assert result.hands[0].near_mouth is True


def test_analyze_no_flags_when_no_face_landmarks_provided(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import app.services.vision.vision_hand_tracker as m
    monkeypatch.setattr(m, "_MP_AVAILABLE", True)

    hand_lm = _make_hand_landmarks(palm_x=0.5, palm_y=0.5)
    tracker = _make_tracker_with_fake_detector(_fake_result([hand_lm]))
    result = tracker.analyze(_blank_image(), face_landmarks=None)

    assert result is not None
    assert result.face_touch_detected is False
    assert result.mouth_touch_detected is False


# ─────────────────────────────────────────────────────────────────────────────
# 6. Two hands — aggregation
# ─────────────────────────────────────────────────────────────────────────────

def test_analyze_two_hands_both_counted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import app.services.vision.vision_hand_tracker as m
    monkeypatch.setattr(m, "_MP_AVAILABLE", True)

    lms_a = _make_hand_landmarks(0.3, 0.3)
    lms_b = _make_hand_landmarks(0.7, 0.7)
    tracker = _make_tracker_with_fake_detector(_fake_result([lms_a, lms_b], labels=["Left", "Right"]))
    result = tracker.analyze(_blank_image())

    assert result is not None
    assert len(result.hands) == 2
    assert result.hands[0].handedness == "Left"
    assert result.hands[1].handedness == "Right"


def test_analyze_face_touch_if_any_hand_is_near(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """face_touch_detected is True when at least one of two hands is near face."""
    import app.services.vision.vision_hand_tracker as m
    monkeypatch.setattr(m, "_MP_AVAILABLE", True)

    face_lm = _make_face_landmarks(cx=0.5, cy=0.5, spread=0.1)

    lms_near = _make_hand_landmarks(0.5, 0.5)   # overlaps face centre
    lms_far  = _make_hand_landmarks(0.9, 0.9)   # far away

    tracker = _make_tracker_with_fake_detector(_fake_result([lms_near, lms_far]))
    result = tracker.analyze(_blank_image(), face_landmarks=face_lm)

    assert result is not None
    assert result.face_touch_detected is True
