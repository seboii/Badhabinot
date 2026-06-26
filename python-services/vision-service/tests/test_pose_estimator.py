"""VisionPoseEstimator — MediaPipe Pose tabanlı postür çıkarımı birim testleri.

Gerçek MediaPipe çalıştırmadan, sahte bir Pose nesnesiyle ``analyze()`` uçtan uca
test edilir: COCO-17 eşleme, ``visibility`` güven eşiği, owner-lock (baş-kutu
örtüşmesi) ve kişi-kutusu üretimi.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pytest

import app.services.vision.vision_pose_estimator as pe_mod
from app.services.vision.vision_pose_estimator import VisionPoseEstimator

_FRAME_W = 640
_FRAME_H = 480


# ── Sahte MediaPipe Pose iskeleti ────────────────────────────────────────────
class _LM:
    def __init__(self, x: float, y: float, visibility: float = 0.99, z: float = 0.0) -> None:
        self.x, self.y, self.z, self.visibility = x, y, z, visibility


class _PoseLandmarks:
    def __init__(self, landmark: list[_LM]) -> None:
        self.landmark = landmark


class _Results:
    def __init__(self, landmark: list[_LM] | None) -> None:
        self.pose_landmarks = _PoseLandmarks(landmark) if landmark else None


class _FakePose:
    def __init__(self, landmark: list[_LM] | None) -> None:
        self._landmark = landmark

    def process(self, _rgb: Any) -> _Results:
        return _Results(self._landmark)


def _upright_landmarks(*, nose_vis: float = 0.99) -> list[_LM]:
    """Dik oturan kişi için 33 elemanlı MediaPipe Pose landmark dizisi.

    Piksel hedefleri test_posture'daki dik-oturuş ile aynıdır (640×480):
    omuzlar (220,300)/(420,300), kulaklar (290,180)/(350,180),
    gözler (300,175)/(340,175), burun (320,200).
    """
    lms = [_LM(0.0, 0.0, 0.0) for _ in range(33)]
    lms[0] = _LM(320 / _FRAME_W, 200 / _FRAME_H, nose_vis)   # nose
    lms[2] = _LM(300 / _FRAME_W, 175 / _FRAME_H)             # left eye
    lms[5] = _LM(340 / _FRAME_W, 175 / _FRAME_H)             # right eye
    lms[7] = _LM(290 / _FRAME_W, 180 / _FRAME_H)             # left ear
    lms[8] = _LM(350 / _FRAME_W, 180 / _FRAME_H)             # right ear
    lms[11] = _LM(220 / _FRAME_W, 300 / _FRAME_H)            # left shoulder
    lms[12] = _LM(420 / _FRAME_W, 300 / _FRAME_H)            # right shoulder
    return lms


def _blank_frame() -> np.ndarray:
    return np.zeros((_FRAME_H, _FRAME_W, 3), dtype=np.uint8)


def _estimator_with(monkeypatch: pytest.MonkeyPatch, landmark: list[_LM] | None) -> VisionPoseEstimator:
    monkeypatch.setattr(pe_mod, "_MP_AVAILABLE", True)
    est = VisionPoseEstimator()
    monkeypatch.setattr(est, "_get_pose", lambda: _FakePose(landmark))
    return est


# ── analyze() — temel akış ───────────────────────────────────────────────────
def test_analyze_returns_none_when_mediapipe_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(pe_mod, "_MP_AVAILABLE", False)
    assert VisionPoseEstimator().analyze(_blank_frame()) is None


def test_analyze_returns_none_when_no_person(monkeypatch: pytest.MonkeyPatch) -> None:
    est = _estimator_with(monkeypatch, None)
    assert est.analyze(_blank_frame()) is None


def test_analyze_upright_is_reliable_and_high_score(monkeypatch: pytest.MonkeyPatch) -> None:
    est = _estimator_with(monkeypatch, _upright_landmarks())
    result = est.analyze(_blank_frame())
    assert result is not None
    assert result.metrics is not None and result.metrics.reliable is True
    assert result.forward_head_ratio > 0.5         # baş omuzların belirgin üstünde
    assert abs(result.lateral_offset) < 0.05       # ortalanmış
    assert result.posture_score >= 70              # dik → yüksek taban skoru
    assert result.is_slouching is False
    assert result.posture_category == "good"


# ── COCO-17 eşleme + visibility eşiği ────────────────────────────────────────
def test_coco_mapping_produces_17_keypoints(monkeypatch: pytest.MonkeyPatch) -> None:
    est = _estimator_with(monkeypatch, _upright_landmarks())
    result = est.analyze(_blank_frame())
    assert result is not None
    assert len(result.keypoints) == 17
    # COCO 0=burun görünür ve frame'e normalize edilmiş.
    nose = result.keypoints[0]
    assert nose is not None
    assert abs(nose.x - 320 / _FRAME_W) < 1e-3
    assert abs(nose.y - 200 / _FRAME_H) < 1e-3


def test_low_visibility_landmark_becomes_none(monkeypatch: pytest.MonkeyPatch) -> None:
    # Burun görünürlüğü eşiğin (0.3) altında → COCO[0] None olmalı.
    est = _estimator_with(monkeypatch, _upright_landmarks(nose_vis=0.1))
    result = est.analyze(_blank_frame())
    assert result is not None
    assert result.keypoints[0] is None


# ── owner-lock: baş kutusu örtüşmesi ─────────────────────────────────────────
def test_analyze_keeps_pose_when_head_inside_owner_box(monkeypatch: pytest.MonkeyPatch) -> None:
    est = _estimator_with(monkeypatch, _upright_landmarks())
    # burun pikselde (320,200); merkezi oraya yakın yüz kutusu.
    owner_bbox = (280, 160, 80, 80)
    assert est.analyze(_blank_frame(), owner_bbox) is not None


def test_analyze_suppresses_pose_when_head_outside_owner_box(monkeypatch: pytest.MonkeyPatch) -> None:
    est = _estimator_with(monkeypatch, _upright_landmarks())
    # Sahibin yüzü sol-üst köşede; tespit edilen kişi (burun 320,200) uzak → yabancı.
    owner_bbox = (10, 10, 40, 40)
    assert est.analyze(_blank_frame(), owner_bbox) is None


# ── kişi-kutusu ──────────────────────────────────────────────────────────────
def test_person_bbox_spans_visible_keypoints(monkeypatch: pytest.MonkeyPatch) -> None:
    est = _estimator_with(monkeypatch, _upright_landmarks())
    result = est.analyze(_blank_frame())
    assert result is not None and result.person_bbox is not None
    x1, y1, x2, y2 = result.person_bbox
    # xs: 220..420 → 0.34..0.66 ; ys: 175..300 → 0.36..0.625
    assert abs(x1 - 220 / _FRAME_W) < 1e-3
    assert abs(x2 - 420 / _FRAME_W) < 1e-3
    assert y1 < y2 and x1 < x2
