"""Faz B — owner-kısıtlı analiz yardımcıları.

Yalnızca hesap sahibinin analiz edilmesini sağlayan seçim/remap mantığını test
eder (ağır ML çalıştırmadan): MediaPipe pose owner-lock (baş-kutu örtüşmesi) +
kişi-kutusu üretimi, el bölge-filtresi ve face-mesh owner-crop landmark remap.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pytest

from app.services.vision.vision_hand_tracker import VisionHandTracker
from app.services.vision.vision_pose_estimator import VisionPoseEstimator


# ── pose: MediaPipe owner-lock (_head_matches_owner) ─────────────────────────
def _pose_pts(
    *,
    nose: tuple[float, float] | None = None,
    eyes: tuple[tuple[float, float], tuple[float, float]] | None = None,
    shoulders: tuple[tuple[float, float], tuple[float, float]] | None = None,
) -> list[tuple[float, float] | None]:
    """17 elemanlı COCO piksel-nokta listesi (kullanılmayanlar None)."""
    pts: list[tuple[float, float] | None] = [None] * 17
    pts[0] = nose
    if eyes:
        pts[1], pts[2] = eyes
    if shoulders:
        pts[5], pts[6] = shoulders
    return pts


# owner yüz kutusu (300,140,80,80) → merkez (340,180); pad_x=pad_y=120.
_OWNER_BBOX = (300, 140, 80, 80)


def test_head_matches_owner_true_when_nose_inside_box() -> None:
    assert VisionPoseEstimator._head_matches_owner(_pose_pts(nose=(340, 180)), _OWNER_BBOX) is True


def test_head_matches_owner_false_when_nose_far() -> None:
    # |600-340| = 260 > 120 → sahip değil (yabancı baskılanır).
    assert VisionPoseEstimator._head_matches_owner(_pose_pts(nose=(600, 180)), _OWNER_BBOX) is False


def test_head_matches_owner_uses_eye_mid_when_no_nose() -> None:
    pts = _pose_pts(eyes=((330, 175), (350, 175)))  # orta (340,175) kutu içinde
    assert VisionPoseEstimator._head_matches_owner(pts, _OWNER_BBOX) is True


def test_head_matches_owner_true_when_no_head_reference() -> None:
    # Baş referansı yok → doğrulanamaz → aşırı baskılamayı önlemek için True.
    assert VisionPoseEstimator._head_matches_owner([None] * 17, _OWNER_BBOX) is True


def test_head_matches_owner_degenerate_box_returns_true() -> None:
    assert VisionPoseEstimator._head_matches_owner(_pose_pts(nose=(0, 0)), (300, 140, 0, 0)) is True


# ── pose: kişi-kutusu üretimi (_bbox_from_points) ────────────────────────────
def test_bbox_from_points_spans_visible_keypoints() -> None:
    pts = _pose_pts(nose=(320, 100), shoulders=((220, 300), (420, 300)))
    bbox = VisionPoseEstimator._bbox_from_points(pts, 640, 480)
    assert bbox == (round(220 / 640, 4), round(100 / 480, 4),
                    round(420 / 640, 4), round(300 / 480, 4))


def test_bbox_from_points_none_when_no_visible_points() -> None:
    assert VisionPoseEstimator._bbox_from_points([None] * 17, 640, 480) is None


# ── hand: _hand_in_region ────────────────────────────────────────────────────
def test_hand_in_region_inside_true_outside_false() -> None:
    bbox = (0.3, 0.3, 0.7, 0.7)
    assert VisionHandTracker._hand_in_region(0.5, 0.5, bbox) is True
    assert VisionHandTracker._hand_in_region(0.95, 0.5, bbox) is False  # 0.95 > 0.7+0.1


def test_hand_in_region_respects_padding() -> None:
    bbox = (0.3, 0.3, 0.7, 0.7)  # pad=0.1 → izinli üst sınır 0.8
    assert VisionHandTracker._hand_in_region(0.79, 0.5, bbox) is True
    assert VisionHandTracker._hand_in_region(0.81, 0.5, bbox) is False


# ── face mesh: analyze_in_bbox landmark remap (crop → full-frame) ─────────────
def test_analyze_in_bbox_remaps_landmarks_to_full_frame(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import app.services.vision.vision_face_mesh as fm_mod

    monkeypatch.setattr(fm_mod, "_MP_AVAILABLE", True)

    class _LM:
        def __init__(self, x: float, y: float, z: float) -> None:
            self.x, self.y, self.z = x, y, z

    class _Face:
        def __init__(self, lms: list[_LM]) -> None:
            self.landmark = lms

    class _Results:
        def __init__(self, faces: list[_Face]) -> None:
            self.multi_face_landmarks = faces

    class _FakeMesh:
        def process(self, _rgb: Any) -> _Results:
            # Tüm landmark'lar crop-merkezinde (0.5, 0.5)
            return _Results([_Face([_LM(0.5, 0.5, 0.0) for _ in range(478)])])

    fm = fm_mod.VisionFaceMesh()
    monkeypatch.setattr(fm, "_get_owner_mesh", lambda: _FakeMesh())

    frame = np.zeros((200, 400, 3), dtype=np.uint8)  # H=200, W=400
    owner_bbox = (100, 50, 80, 80)                    # x, y, w, h
    result = fm.analyze_in_bbox(frame, owner_bbox)

    assert result is not None
    # pad = 80*0.2 = 16 → x1=84, y1=34, x2=196, y2=146 → crop_w=crop_h=112
    # crop (0.5,0.5) → full: x=(84+56)/400=0.35 ; y=(34+56)/200=0.45
    lx, ly, _ = result.landmarks[0]
    assert abs(lx - 0.35) < 1e-3
    assert abs(ly - 0.45) < 1e-3


def test_analyze_in_bbox_rejects_degenerate_bbox(monkeypatch: pytest.MonkeyPatch) -> None:
    import app.services.vision.vision_face_mesh as fm_mod

    monkeypatch.setattr(fm_mod, "_MP_AVAILABLE", True)
    fm = fm_mod.VisionFaceMesh()
    frame = np.zeros((100, 100, 3), dtype=np.uint8)
    assert fm.analyze_in_bbox(frame, (10, 10, 0, 0)) is None
