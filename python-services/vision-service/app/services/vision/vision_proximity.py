"""Proximity calculation helpers — Phase 9 wiring module.

Provides standalone functions used by VisionAnalysisService to
determine spatial relationships between hands, face, mouth, and detected objects.

All coordinates are assumed to be in normalized [0, 1] space.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.services.vision.vision_face_mesh import FaceMeshResult
    from app.services.vision.vision_hand_tracker import HandTrackingResult
    from app.services.vision.vision_yolo_detector import YoloDetectionResult


# ── Landmark index constants (MediaPipe FaceMesh) ────────────────────────────
_MOUTH_TOP = 13
_MOUTH_BOTTOM = 14
_MOUTH_LEFT = 78
_MOUTH_RIGHT = 308

_FACE_TOUCH_SCALE = 0.55    # fraction of face diagonal = "near face"
_MOUTH_TOUCH_DIST = 0.10    # normalized distance threshold = "near mouth"
_OBJ_MOUTH_DIST = 0.12      # object center to mouth center threshold


def hand_to_face(
    hand_result: HandTrackingResult | None,
    mesh_result: FaceMeshResult | None,
) -> bool:
    """Return True if any detected hand is near the face region.

    Falls back to False if either input is None (module not available).
    """
    if hand_result is None or mesh_result is None:
        return False
    return hand_result.face_touch_detected


def hand_to_mouth(
    hand_result: HandTrackingResult | None,
    mesh_result: FaceMeshResult | None,
) -> bool:
    """Return True if any fingertip is near the mouth landmark area."""
    if hand_result is None or mesh_result is None:
        return False
    return hand_result.mouth_touch_detected


def object_to_mouth(
    yolo_result: YoloDetectionResult | None,
    mesh_result: FaceMeshResult | None,
) -> str | None:
    """Return the class name of the object closest to the mouth, or None.

    Returns one of: "cup", "bottle", or None.
    """
    if yolo_result is None:
        return None

    if yolo_result.cup_near_mouth:
        return "cup"
    if yolo_result.bottle_near_mouth:
        return "bottle"

    # Elongated object near mouth — check YOLO detections
    if mesh_result is None or len(mesh_result.landmarks) < 15:
        return None

    lm = mesh_result.landmarks
    mouth_cx = (lm[_MOUTH_LEFT][0] + lm[_MOUTH_RIGHT][0]) / 2.0
    mouth_cy = (lm[_MOUTH_TOP][1] + lm[_MOUTH_BOTTOM][1]) / 2.0

    for det in yolo_result.detections:
        if det.class_name not in ("cup", "bottle"):
            continue
        dist = math.hypot(det.center_x - mouth_cx, det.center_y - mouth_cy)
        if dist < _OBJ_MOUTH_DIST:
            return det.class_name

    return None


def face_bbox_from_landmarks(
    landmarks: list[tuple[float, float, float]],
) -> tuple[float, float, float, float] | None:
    """Return (x1, y1, x2, y2) bounding box from face mesh landmarks, normalized."""
    if not landmarks:
        return None
    xs = [lm[0] for lm in landmarks]
    ys = [lm[1] for lm in landmarks]
    return (min(xs), min(ys), max(xs), max(ys))


def mouth_bbox_from_landmarks(
    landmarks: list[tuple[float, float, float]],
) -> tuple[float, float, float, float] | None:
    """Return tight mouth bounding box from face mesh landmarks."""
    if len(landmarks) < 310:
        return None
    lm = landmarks
    x1 = min(lm[_MOUTH_LEFT][0], lm[_MOUTH_RIGHT][0]) - 0.02
    x2 = max(lm[_MOUTH_LEFT][0], lm[_MOUTH_RIGHT][0]) + 0.02
    y1 = min(lm[_MOUTH_TOP][1], lm[_MOUTH_BOTTOM][1]) - 0.02
    y2 = max(lm[_MOUTH_TOP][1], lm[_MOUTH_BOTTOM][1]) + 0.02
    return (max(0.0, x1), max(0.0, y1), min(1.0, x2), min(1.0, y2))
