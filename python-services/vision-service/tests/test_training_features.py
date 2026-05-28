"""training.landmark_features — saf numpy, ML gerektirmez."""

from __future__ import annotations

from types import SimpleNamespace

import numpy as np

from training.landmark_features import FEATURE_DIM, features_from_response


def _empty_response() -> SimpleNamespace:
    return SimpleNamespace(pose=None, face_mesh=None, hands=None, objects=None)


def test_feature_dimension_is_fixed() -> None:
    vector = features_from_response(_empty_response())
    assert vector.shape == (FEATURE_DIM,)
    assert vector.dtype == np.float32


def test_empty_response_is_all_zero() -> None:
    vector = features_from_response(_empty_response())
    assert np.allclose(vector, 0.0)


def test_partial_modules_still_fixed_dim() -> None:
    # Sadece pose mevcut — diğer bloklar sıfır-padded olmalı, boyut sabit kalmalı.
    pose = SimpleNamespace(
        posture_score=50,
        spine_tilt_angle=45.0,
        shoulder_tilt_angle=0.0,
        keypoints=[SimpleNamespace(x=0.5, y=0.5) for _ in range(17)],
    )
    response = SimpleNamespace(pose=pose, face_mesh=None, hands=None, objects=None)
    vector = features_from_response(response)
    assert vector.shape == (FEATURE_DIM,)
    assert vector[0] == np.float32(0.5)          # posture_score 50/100
    assert vector[1] == np.float32(0.5)          # spine_tilt 45/90


def test_populated_response_is_deterministic() -> None:
    mesh = SimpleNamespace(
        ear=0.3, mar=0.7, yaw=0.0, pitch=0.0, roll=0.0,
        is_drowsy=False, is_yawning=True, gaze_off_screen=False,
    )
    hands = SimpleNamespace(
        face_touch_detected=True, mouth_touch_detected=False,
        hands=[SimpleNamespace(center_x=0.4, center_y=0.6, near_face=True, near_mouth=False)],
    )
    objects = SimpleNamespace(bottle_near_mouth=False, cup_near_mouth=False, phone_detected=True)
    response = SimpleNamespace(pose=None, face_mesh=mesh, hands=hands, objects=objects)

    first = features_from_response(response)
    second = features_from_response(response)
    assert np.array_equal(first, second)
    assert first.shape == (FEATURE_DIM,)
    assert not np.allclose(first, 0.0)           # bazı değerler set edilmiş olmalı
