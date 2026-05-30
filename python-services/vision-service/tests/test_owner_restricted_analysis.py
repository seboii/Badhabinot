"""Faz B — owner-kısıtlı analiz yardımcıları.

Yalnızca hesap sahibinin analiz edilmesini sağlayan seçim/remap mantığını test
eder (ağır ML çalıştırmadan): pose kişi-seçimi, el bölge-filtresi ve face-mesh
owner-crop landmark remap matematiği.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pytest

from app.services.vision.vision_hand_tracker import VisionHandTracker
from app.services.vision.vision_pose_estimator import VisionPoseEstimator


# ── pose: _select_person_index ───────────────────────────────────────────────
def test_select_person_index_picks_box_containing_owner() -> None:
    # Sol kişi ve sağ kişi; owner yüz merkezi sağdakinin içinde.
    boxes = np.array([[0.0, 0.0, 0.4, 1.0], [0.6, 0.0, 1.0, 1.0]])
    assert VisionPoseEstimator._select_person_index(boxes, (0.8, 0.5)) == 1
    assert VisionPoseEstimator._select_person_index(boxes, (0.2, 0.5)) == 0


def test_select_person_index_prefers_smallest_containing_box() -> None:
    # Büyük kutu da küçük kutu da merkezi içeriyor → en spesifik (küçük) seçilir.
    boxes = np.array([[0.0, 0.0, 1.0, 1.0], [0.4, 0.4, 0.6, 0.6]])
    assert VisionPoseEstimator._select_person_index(boxes, (0.5, 0.5)) == 1


def test_select_person_index_falls_back_to_nearest_when_none_contains() -> None:
    boxes = np.array([[0.0, 0.0, 0.2, 0.2], [0.8, 0.8, 1.0, 1.0]])
    # (0.5, 0.1) hiçbirinin içinde değil → kutu merkezine en yakın: index 0.
    assert VisionPoseEstimator._select_person_index(boxes, (0.5, 0.1)) == 0


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
