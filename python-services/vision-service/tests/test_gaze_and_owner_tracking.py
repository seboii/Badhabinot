"""Tests for Module G: owner face identification, iris gaze tracking, and
the new behavioral events (GAZE_AWAY, OWNER_ABSENT, STRANGER_DETECTED).

These tests avoid heavy ML dependencies (DeepFace, MediaPipe) by monkeypatching
the availability flags and using synthetic data wherever possible.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import numpy as np
import pytest

from app.services.vision.behavior_engine import BehaviorFrameInput, BehaviorStateStore
from app.services.vision.session_state import (
    OwnerTrackingObservation,
    OwnerTrackingStateStore,
)
from app.services.vision.vision_face_auth import OwnerFaceResult, VisionFaceAuth
from app.services.vision.vision_face_mesh import VisionFaceMesh


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _blank_image(h: int = 64, w: int = 64) -> np.ndarray:
    return np.zeros((h, w, 3), dtype=np.uint8)


def _now() -> datetime:
    return datetime.now(tz=timezone.utc)


def _behavior_input(**kwargs: Any) -> BehaviorFrameInput:
    defaults: dict[str, Any] = dict(
        captured_at=_now(),
        session_id="session-test",
        user_id="user-test",
        face_detected=True,
        face_authenticated=True,
        auth_confidence=1.0,
    )
    defaults.update(kwargs)
    return BehaviorFrameInput(**defaults)


# ─────────────────────────────────────────────────────────────────────────────
# 1. Multi-face owner identification (VisionFaceAuth.identify_owner)
# ─────────────────────────────────────────────────────────────────────────────

def test_identify_owner_no_deepface_returns_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    """identify_owner returns owner_found=False gracefully when DeepFace is absent."""
    import app.services.vision.vision_face_auth as auth_module
    monkeypatch.setattr(auth_module, "_DEEPFACE_AVAILABLE", False)

    auth = VisionFaceAuth()
    result = auth.identify_owner("any_user", _blank_image())

    assert isinstance(result, OwnerFaceResult)
    assert result.owner_found is False
    assert result.owner_bbox is None
    assert result.owner_confidence == 0.0
    assert result.total_faces == 0
    assert result.strangers_count == 0


def test_identify_owner_no_profile_returns_not_found(tmp_path: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    """identify_owner returns owner_found=False when no profile exists for the user."""
    import app.services.vision.vision_face_auth as auth_module
    monkeypatch.setattr(auth_module, "_DATA_ROOT", tmp_path)

    auth = VisionFaceAuth()
    result = auth.identify_owner("nonexistent_user", _blank_image())

    assert result.owner_found is False
    assert result.owner_bbox is None


def test_identify_owner_incomplete_profile_returns_not_found(
    tmp_path: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    """identify_owner returns not-found when profile has fewer than MIN_FRAMES embeddings."""
    import app.services.vision.vision_face_auth as auth_module
    monkeypatch.setattr(auth_module, "_DATA_ROOT", tmp_path)
    monkeypatch.setattr(auth_module, "_MIN_FRAMES_TO_REGISTER", 3)

    # Write only 2 embeddings (below minimum)
    user_dir = tmp_path / "partialuser"
    user_dir.mkdir()
    embeddings = np.random.randn(2, 128).astype(np.float32)
    np.save(str(user_dir / "face_embeddings.npy"), embeddings)

    auth = VisionFaceAuth()
    result = auth.identify_owner("partialuser", _blank_image())

    assert result.owner_found is False


def test_identify_owner_stranger_only_frame(
    tmp_path: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    """When the only detected face is a stranger, owner_found=False and strangers_count == total_faces."""
    import app.services.vision.vision_face_auth as auth_module

    monkeypatch.setattr(auth_module, "_DATA_ROOT", tmp_path)
    monkeypatch.setattr(auth_module, "_DEEPFACE_AVAILABLE", True)

    # Register a profile: 5 normalised embeddings pointing in the +x direction
    user_dir = tmp_path / "owner"
    user_dir.mkdir()
    stored = np.zeros((5, 128), dtype=np.float32)
    stored[:, 0] = 1.0  # unit vector in first dimension
    np.save(str(user_dir / "face_embeddings.npy"), stored)

    # Fake DeepFace returns one face whose embedding is the -x direction (maximally dissimilar)
    stranger_emb = np.zeros(128, dtype=np.float32)
    stranger_emb[0] = -1.0  # cosine sim with stored = -1 → mapped similarity = 0.0

    class FakeDeepFace:
        @staticmethod
        def represent(**_kwargs: Any) -> list[dict]:
            return [{"embedding": stranger_emb.tolist(), "facial_area": {"x": 0, "y": 0, "w": 50, "h": 50}}]

    # raising=False creates the attribute even when DeepFace import failed in the module
    monkeypatch.setattr(auth_module, "DeepFace", FakeDeepFace, raising=False)

    auth = VisionFaceAuth()
    result = auth.identify_owner("owner", _blank_image())

    assert result.owner_found is False
    assert result.total_faces == 1
    assert result.strangers_count == 1


# ─────────────────────────────────────────────────────────────────────────────
# 2. Gaze zone classification (VisionFaceMesh._classify_zone — static, no ML)
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("gx,gy,expected", [
    (0.00,  0.00, "center"),
    (0.05,  0.02, "center"),
    (-0.05, 0.08, "center"),
    (-0.25, 0.02, "left"),
    ( 0.25, 0.02, "right"),
    ( 0.02,-0.20, "up"),
    ( 0.02, 0.20, "down"),
    ( 0.20, 0.18, "away"),   # both thresholds exceeded, oblique
    (-0.20,-0.15, "away"),
])
def test_gaze_classify_zone(gx: float, gy: float, expected: str) -> None:
    zone = VisionFaceMesh._classify_zone(gx, gy)
    assert zone == expected, f"classify_zone({gx}, {gy}) = {zone!r}, expected {expected!r}"


def test_extract_owner_gaze_no_mediapipe_returns_none(monkeypatch: pytest.MonkeyPatch) -> None:
    """extract_owner_gaze returns None gracefully when MediaPipe is unavailable."""
    import app.services.vision.vision_face_mesh as mesh_module
    monkeypatch.setattr(mesh_module, "_MP_AVAILABLE", False)

    vm = VisionFaceMesh()
    result = vm.extract_owner_gaze(_blank_image(), (0, 0, 64, 64))
    assert result is None


def test_extract_owner_gaze_zero_size_bbox_returns_none() -> None:
    """extract_owner_gaze returns None for a degenerate zero-size bounding box."""
    vm = VisionFaceMesh()
    assert vm.extract_owner_gaze(_blank_image(), (10, 10, 0, 0)) is None
    assert vm.extract_owner_gaze(_blank_image(), (10, 10, -5, 20)) is None


def test_eye_gaze_degenerate_eye_width_returns_none() -> None:
    """_eye_gaze returns None when the eye outer and inner corners coincide."""
    landmarks = [(0.5, 0.5)] * 480  # fill enough entries
    result = VisionFaceMesh._eye_gaze(
        landmarks,
        iris_center_idx=468,
        eye_outer_idx=33,
        eye_inner_idx=133,
    )
    # outer == inner → eye_width == 0 → should return None
    # Both are (0.5, 0.5), so width = |0.5 - 0.5| = 0.0
    assert result is None


# ─────────────────────────────────────────────────────────────────────────────
# 3. OwnerTrackingStateStore
# ─────────────────────────────────────────────────────────────────────────────

def test_owner_tracking_store_absence_streak_increments() -> None:
    """owner_absence_streak increments by 1 each frame when owner not found."""
    store = OwnerTrackingStateStore()
    obs = OwnerTrackingObservation(
        captured_at=_now(),
        owner_found=False,
        owner_bbox=None,
        owner_gaze=None,
        strangers_in_frame=0,
    )
    for expected_streak in range(1, 4):
        state = store.update("s1", obs)
        assert state.owner_absence_streak == expected_streak


def test_owner_tracking_store_streak_resets_on_owner_found() -> None:
    """owner_absence_streak resets to 0 when owner is detected."""
    store = OwnerTrackingStateStore()
    now = _now()
    obs_absent = OwnerTrackingObservation(
        captured_at=now, owner_found=False, owner_bbox=None,
        owner_gaze=None, strangers_in_frame=0,
    )
    obs_found = OwnerTrackingObservation(
        captured_at=now, owner_found=True, owner_bbox=(10, 10, 80, 80),
        owner_gaze=None, strangers_in_frame=0,
    )
    store.update("s1", obs_absent)
    store.update("s1", obs_absent)
    state = store.update("s1", obs_found)
    assert state.owner_absence_streak == 0


def test_owner_tracking_store_persists_bbox_and_strangers() -> None:
    """State store reflects latest owner_bbox and strangers_in_frame values."""
    store = OwnerTrackingStateStore()
    bbox = (20, 30, 100, 120)
    obs = OwnerTrackingObservation(
        captured_at=_now(), owner_found=True, owner_bbox=bbox,
        owner_gaze=None, strangers_in_frame=3,
    )
    state = store.update("s2", obs)
    assert state.owner_face_bbox == bbox
    assert state.strangers_in_frame == 3


# ─────────────────────────────────────────────────────────────────────────────
# 4. Behavioral events: STRANGER_DETECTED, GAZE_AWAY, OWNER_ABSENT
# ─────────────────────────────────────────────────────────────────────────────

def test_stranger_detected_not_emitted_when_no_strangers() -> None:
    store = BehaviorStateStore()
    events = store.evaluate(_behavior_input(strangers_in_frame=0, owner_tracked=True))
    assert not any(e.event_type == "STRANGER_DETECTED" for e in events)


def test_stranger_detected_fires_immediately_with_one_stranger() -> None:
    """STRANGER_DETECTED is emitted on the very first frame with strangers."""
    store = BehaviorStateStore()
    events = store.evaluate(_behavior_input(strangers_in_frame=1, owner_tracked=True))
    assert any(e.event_type == "STRANGER_DETECTED" for e in events)


def test_stranger_detected_confidence_scales_with_count() -> None:
    """More strangers → higher confidence on the STRANGER_DETECTED event."""
    store_1 = BehaviorStateStore()
    store_3 = BehaviorStateStore()
    events_1 = store_1.evaluate(_behavior_input(strangers_in_frame=1, owner_tracked=True))
    events_3 = store_3.evaluate(_behavior_input(strangers_in_frame=3, owner_tracked=True))

    conf_1 = next(e.confidence for e in events_1 if e.event_type == "STRANGER_DETECTED")
    conf_3 = next(e.confidence for e in events_3 if e.event_type == "STRANGER_DETECTED")
    assert conf_3 > conf_1


def test_gaze_away_not_emitted_before_threshold() -> None:
    """GAZE_AWAY must not fire if the owner has been looking away for < 3 s."""
    store = BehaviorStateStore()
    t0 = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)

    # 2 seconds of gaze away
    for delta in (0, 1, 2):
        events = store.evaluate(_behavior_input(
            captured_at=t0 + timedelta(seconds=delta),
            session_id="gaze-session",
            owner_tracked=True,
            owner_gaze_looking_at_screen=False,
        ))
        assert not any(e.event_type == "GAZE_AWAY" for e in events), \
            f"GAZE_AWAY fired prematurely at t+{delta}s"


def test_gaze_away_fires_after_threshold() -> None:
    """GAZE_AWAY fires when owner is looking away for >= 3 consecutive seconds."""
    store = BehaviorStateStore()
    t0 = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)

    # Prime the timer — 3 frames of looking away
    for delta in (0, 1):
        store.evaluate(_behavior_input(
            captured_at=t0 + timedelta(seconds=delta),
            session_id="gaze-session",
            owner_tracked=True,
            owner_gaze_looking_at_screen=False,
        ))

    # At t+4 the threshold (3 s) is exceeded
    events = store.evaluate(_behavior_input(
        captured_at=t0 + timedelta(seconds=4),
        session_id="gaze-session",
        owner_tracked=True,
        owner_gaze_looking_at_screen=False,
    ))
    assert any(e.event_type == "GAZE_AWAY" for e in events)


def test_gaze_away_resets_when_owner_looks_at_screen() -> None:
    """GAZE_AWAY timer resets when owner looks back at the screen."""
    store = BehaviorStateStore()
    t0 = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)

    # 4 s looking away → GAZE_AWAY fires
    for delta in range(5):
        store.evaluate(_behavior_input(
            captured_at=t0 + timedelta(seconds=delta),
            session_id="gaze-reset",
            owner_tracked=True,
            owner_gaze_looking_at_screen=False,
        ))

    # Owner looks back → timer resets
    store.evaluate(_behavior_input(
        captured_at=t0 + timedelta(seconds=5),
        session_id="gaze-reset",
        owner_tracked=True,
        owner_gaze_looking_at_screen=True,
    ))

    # One frame later with gaze away again — not yet past 3 s
    events = store.evaluate(_behavior_input(
        captured_at=t0 + timedelta(seconds=6),
        session_id="gaze-reset",
        owner_tracked=True,
        owner_gaze_looking_at_screen=False,
    ))
    assert not any(e.event_type == "GAZE_AWAY" for e in events)


def test_owner_absent_not_emitted_before_threshold() -> None:
    """OWNER_ABSENT must not fire if owner has been absent for < 5 s."""
    store = BehaviorStateStore()
    t0 = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)

    for delta in (0, 2, 4):
        events = store.evaluate(_behavior_input(
            captured_at=t0 + timedelta(seconds=delta),
            session_id="absent-session",
            owner_tracked=False,
            face_detected=False,
            face_authenticated=False,
        ))
        assert not any(e.event_type == "OWNER_ABSENT" for e in events), \
            f"OWNER_ABSENT fired prematurely at t+{delta}s"


def test_owner_absent_fires_after_threshold() -> None:
    """OWNER_ABSENT fires when owner has not been identified for >= 5 s."""
    store = BehaviorStateStore()
    t0 = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)

    for delta in (0, 2):
        store.evaluate(_behavior_input(
            captured_at=t0 + timedelta(seconds=delta),
            session_id="absent-session",
            owner_tracked=False,
            face_detected=False,
            face_authenticated=False,
        ))

    events = store.evaluate(_behavior_input(
        captured_at=t0 + timedelta(seconds=6),
        session_id="absent-session",
        owner_tracked=False,
        face_detected=False,
        face_authenticated=False,
    ))
    assert any(e.event_type == "OWNER_ABSENT" for e in events)


def test_owner_absent_and_stranger_can_coexist() -> None:
    """OWNER_ABSENT and STRANGER_DETECTED can fire in the same frame."""
    store = BehaviorStateStore()
    t0 = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)

    # Prime absence timer
    store.evaluate(_behavior_input(
        captured_at=t0,
        session_id="both-session",
        owner_tracked=False,
        face_detected=False,
        strangers_in_frame=0,
    ))

    # 6 s later: still no owner, but a stranger appeared
    events = store.evaluate(_behavior_input(
        captured_at=t0 + timedelta(seconds=6),
        session_id="both-session",
        owner_tracked=False,
        face_detected=True,
        strangers_in_frame=1,
    ))
    event_types = {e.event_type for e in events}
    assert "STRANGER_DETECTED" in event_types
    assert "OWNER_ABSENT" in event_types


def test_owner_absent_not_fired_when_owner_present() -> None:
    """OWNER_ABSENT is never emitted when owner_tracked=True."""
    store = BehaviorStateStore()
    for _ in range(10):
        events = store.evaluate(_behavior_input(
            owner_tracked=True,
            face_detected=True,
            face_authenticated=True,
        ))
        assert not any(e.event_type == "OWNER_ABSENT" for e in events)
