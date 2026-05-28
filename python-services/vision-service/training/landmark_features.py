"""VisionAnalysisResponse'tan sabit-boyutlu landmark + türev özellik vektörü.

Saf numpy — PyTorch/pipeline gerektirmez, böylece bağımsız test edilebilir.
Eksik modüller (pipeline modülü yüklü değil / tespit yok) sıfır-padded olur, yani
vektör boyutu her zaman sabittir. Özellikler `getattr` ile okunur; hem Pydantic
VisionAnalysisResponse hem de test için SimpleNamespace ile çalışır.
"""

from __future__ import annotations

import numpy as np

# Blok boyutları
_POSE_DIM = 3 + 17 * 2     # posture_score, spine_tilt, shoulder_tilt + 17 keypoint (x, y)
_FACE_DIM = 8              # ear, mar, yaw, pitch, roll, drowsy, yawning, gaze_off
_HAND_DIM = 2 + 2 * 4      # face_touch, mouth_touch + 2 el slotu (cx, cy, near_face, near_mouth)
_OBJ_DIM = 3               # bottle_near_mouth, cup_near_mouth, phone_detected

FEATURE_DIM = _POSE_DIM + _FACE_DIM + _HAND_DIM + _OBJ_DIM   # 58


# Vektörün her boyutunun insan-okunur adı — XAI/kişiselleştirme tarafından kullanılır.
_COCO_KEYPOINT_NAMES = [
    "nose", "left_eye", "right_eye", "left_ear", "right_ear",
    "left_shoulder", "right_shoulder", "left_elbow", "right_elbow",
    "left_wrist", "right_wrist", "left_hip", "right_hip",
    "left_knee", "right_knee", "left_ankle", "right_ankle",
]


def _build_feature_names() -> list[str]:
    names: list[str] = []
    names.extend(["posture_score", "spine_tilt_angle", "shoulder_tilt_angle"])
    for kp in _COCO_KEYPOINT_NAMES:
        names.extend([f"kp_{kp}_x", f"kp_{kp}_y"])
    names.extend(["ear", "mar", "yaw", "pitch", "roll", "is_drowsy", "is_yawning", "gaze_off_screen"])
    names.extend(["face_touch_detected", "mouth_touch_detected"])
    for i in range(2):
        names.extend([f"hand{i}_cx", f"hand{i}_cy", f"hand{i}_near_face", f"hand{i}_near_mouth"])
    names.extend(["bottle_near_mouth", "cup_near_mouth", "phone_detected"])
    assert len(names) == FEATURE_DIM, f"Özellik adı sayısı {len(names)} != FEATURE_DIM {FEATURE_DIM}"
    return names


FEATURE_NAMES: list[str] = _build_feature_names()


def _f(value: object) -> float:
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return 0.0


def _angle_norm(value: object) -> float:
    return max(-1.0, min(1.0, _f(value) / 180.0))


def _pose_features(pose: object | None) -> list[float]:
    if pose is None:
        return [0.0] * _POSE_DIM
    feats = [
        _f(getattr(pose, "posture_score", 0)) / 100.0,
        min(_f(getattr(pose, "spine_tilt_angle", 0)) / 90.0, 1.0),
        min(_f(getattr(pose, "shoulder_tilt_angle", 0)) / 90.0, 1.0),
    ]
    keypoints = getattr(pose, "keypoints", None) or []
    for i in range(17):
        kp = keypoints[i] if i < len(keypoints) else None
        if kp is None:
            feats.extend([0.0, 0.0])
        else:
            feats.extend([_f(getattr(kp, "x", 0)), _f(getattr(kp, "y", 0))])
    return feats


def _face_features(mesh: object | None) -> list[float]:
    if mesh is None:
        return [0.0] * _FACE_DIM
    return [
        _f(getattr(mesh, "ear", 0)),
        _f(getattr(mesh, "mar", 0)),
        _angle_norm(getattr(mesh, "yaw", 0)),
        _angle_norm(getattr(mesh, "pitch", 0)),
        _angle_norm(getattr(mesh, "roll", 0)),
        float(bool(getattr(mesh, "is_drowsy", False))),
        float(bool(getattr(mesh, "is_yawning", False))),
        float(bool(getattr(mesh, "gaze_off_screen", False))),
    ]


def _hand_features(hands: object | None) -> list[float]:
    if hands is None:
        return [0.0] * _HAND_DIM
    feats = [
        float(bool(getattr(hands, "face_touch_detected", False))),
        float(bool(getattr(hands, "mouth_touch_detected", False))),
    ]
    hand_list = getattr(hands, "hands", None) or []
    for i in range(2):
        hand = hand_list[i] if i < len(hand_list) else None
        if hand is None:
            feats.extend([0.0, 0.0, 0.0, 0.0])
        else:
            feats.extend([
                _f(getattr(hand, "center_x", 0)),
                _f(getattr(hand, "center_y", 0)),
                float(bool(getattr(hand, "near_face", False))),
                float(bool(getattr(hand, "near_mouth", False))),
            ])
    return feats


def _object_features(objects: object | None) -> list[float]:
    if objects is None:
        return [0.0] * _OBJ_DIM
    return [
        float(bool(getattr(objects, "bottle_near_mouth", False))),
        float(bool(getattr(objects, "cup_near_mouth", False))),
        float(bool(getattr(objects, "phone_detected", False))),
    ]


def features_from_response(response: object) -> np.ndarray:
    """VisionAnalysisResponse'tan (FEATURE_DIM,) float32 özellik vektörü üretir."""
    feats = (
        _pose_features(getattr(response, "pose", None))
        + _face_features(getattr(response, "face_mesh", None))
        + _hand_features(getattr(response, "hands", None))
        + _object_features(getattr(response, "objects", None))
    )
    vector = np.asarray(feats, dtype=np.float32)
    if vector.shape[0] != FEATURE_DIM:   # iç tutarlılık güvencesi
        raise AssertionError(f"feature boyutu {vector.shape[0]}, beklenen {FEATURE_DIM}")
    return vector
