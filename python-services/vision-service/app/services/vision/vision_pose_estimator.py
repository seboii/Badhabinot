"""Module E — Posture Analysis via YOLOv8-pose.

Detects upper-body keypoints (COCO pose, indices 0-12: nose through elbows)
and computes:
- Spine tilt angle from vertical
- Shoulder asymmetry
- Posture score 0-100
- Slouching flag (tilt > 20°)

Lazy-loads YOLOv8n-pose on first call.
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field

import numpy as np

logger = logging.getLogger(__name__)

try:
    from ultralytics import YOLO  # type: ignore[import-untyped]
    _ULTRALYTICS_AVAILABLE = True
except ImportError:  # pragma: no cover
    _ULTRALYTICS_AVAILABLE = False
    logger.warning("ultralytics not installed — pose estimation disabled")

# COCO keypoint indices relevant to upper body
_KP_NOSE = 0
_KP_LEFT_EYE = 1
_KP_RIGHT_EYE = 2
_KP_LEFT_SHOULDER = 5
_KP_RIGHT_SHOULDER = 6
_KP_LEFT_ELBOW = 7
_KP_RIGHT_ELBOW = 8
_KP_LEFT_WRIST = 9
_KP_RIGHT_WRIST = 10

_SLOUCH_ANGLE_DEG = 20.0        # spine tilt above this = slouching
_SHOULDER_ASYM_THRESHOLD = 0.12  # |left_y - right_y| / frame_height

_POSE_MODEL_NAME = "yolov8n-pose.pt"
_CONFIDENCE_THRESHOLD = 0.4


@dataclass
class PoseKeypoint:
    x: float       # normalized [0, 1]
    y: float       # normalized [0, 1]
    confidence: float  # detection confidence


@dataclass
class PoseResult:
    """Posture analysis outputs for one frame."""

    # COCO keypoints 0-12, None where not detected
    keypoints: list[PoseKeypoint | None] = field(default_factory=list)

    # Derived metrics
    spine_tilt_angle: float = 0.0       # degrees from vertical (positive = forward lean)
    shoulder_tilt_angle: float = 0.0    # degrees of shoulder line from horizontal
    posture_score: int = 100            # 0–100 (100 = perfect)
    is_slouching: bool = False

    # Raw bbox for the detected person
    person_bbox: tuple[float, float, float, float] | None = None  # (x1,y1,x2,y2) normalized


class VisionPoseEstimator:
    """YOLOv8-pose wrapper for upper-body posture analysis."""

    def __init__(self) -> None:
        self._model: object | None = None

    # ------------------------------------------------------------------ #
    # Public API                                                           #
    # ------------------------------------------------------------------ #

    def analyze(self, image: np.ndarray) -> PoseResult | None:
        """Run pose estimation on *image* (BGR, uint8).

        Returns None if ultralytics is unavailable or no person detected.
        """
        if not _ULTRALYTICS_AVAILABLE:
            return None

        model = self._get_model()
        h, w = image.shape[:2]

        results = model(image, verbose=False, conf=_CONFIDENCE_THRESHOLD)
        if not results or not results[0].keypoints:
            return None

        kps = results[0].keypoints
        boxes = results[0].boxes

        if kps is None or len(kps.xy) == 0:
            return None

        # Take the most confident person (first result from YOLO, already sorted)
        kp_xy = kps.xy[0].cpu().numpy()   # (17, 2) pixel coords
        kp_conf = kps.conf[0].cpu().numpy() if kps.conf is not None else np.ones(17)

        # Normalize to [0, 1]
        keypoints: list[PoseKeypoint | None] = []
        for i in range(min(17, len(kp_xy))):
            conf = float(kp_conf[i]) if i < len(kp_conf) else 0.0
            if conf < 0.3:
                keypoints.append(None)
            else:
                keypoints.append(PoseKeypoint(
                    x=round(float(kp_xy[i][0]) / w, 4),
                    y=round(float(kp_xy[i][1]) / h, 4),
                    confidence=round(conf, 3),
                ))

        # Pad to 17 if fewer returned
        while len(keypoints) < 17:
            keypoints.append(None)

        spine_tilt, shoulder_tilt = self._compute_angles(keypoints)
        posture_score = self._posture_score(spine_tilt, shoulder_tilt)
        is_slouching = spine_tilt > _SLOUCH_ANGLE_DEG

        # Person bounding box (normalized)
        person_bbox = None
        if boxes is not None and len(boxes.xyxyn) > 0:
            b = boxes.xyxyn[0].cpu().numpy()
            person_bbox = (round(float(b[0]), 4), round(float(b[1]), 4),
                           round(float(b[2]), 4), round(float(b[3]), 4))

        return PoseResult(
            keypoints=keypoints,
            spine_tilt_angle=round(spine_tilt, 2),
            shoulder_tilt_angle=round(shoulder_tilt, 2),
            posture_score=posture_score,
            is_slouching=is_slouching,
            person_bbox=person_bbox,
        )

    # ------------------------------------------------------------------ #
    # Private helpers                                                      #
    # ------------------------------------------------------------------ #

    def _get_model(self) -> object:
        if self._model is None:
            logger.info("Loading YOLOv8-pose model (%s)…", _POSE_MODEL_NAME)
            self._model = YOLO(_POSE_MODEL_NAME)
        return self._model

    @staticmethod
    def _compute_angles(kps: list[PoseKeypoint | None]) -> tuple[float, float]:
        """Return (spine_tilt_deg, shoulder_tilt_deg)."""
        nose = kps[_KP_NOSE]
        ls = kps[_KP_LEFT_SHOULDER]
        rs = kps[_KP_RIGHT_SHOULDER]

        shoulder_tilt = 0.0
        if ls is not None and rs is not None:
            dx = rs.x - ls.x
            dy = rs.y - ls.y
            shoulder_tilt = abs(math.degrees(math.atan2(dy, dx)))
            if shoulder_tilt > 90:
                shoulder_tilt = 180.0 - shoulder_tilt

        spine_tilt = 0.0
        if nose is not None and ls is not None and rs is not None:
            # Shoulder midpoint → nose = "spine" direction
            mid_x = (ls.x + rs.x) / 2.0
            mid_y = (ls.y + rs.y) / 2.0
            # Vector from shoulder mid to nose (positive y is down in image)
            dx = nose.x - mid_x
            dy = mid_y - nose.y  # flip y so up = positive
            # Angle from vertical (0° = nose directly above shoulders)
            spine_tilt = abs(math.degrees(math.atan2(abs(dx), max(dy, 0.01))))

        return spine_tilt, shoulder_tilt

    @staticmethod
    def _posture_score(spine_tilt: float, shoulder_tilt: float) -> int:
        """Map tilt angles to a 0-100 score (100 = perfect)."""
        # Penalise spine tilt: 0° = 0 penalty, 45° = 60 penalty
        spine_penalty = min(60, spine_tilt * (60.0 / 45.0))
        # Penalise shoulder asymmetry: 0° = 0, 15° = 40 penalty
        shoulder_penalty = min(40, shoulder_tilt * (40.0 / 15.0))
        score = 100 - spine_penalty - shoulder_penalty
        return max(0, int(round(score)))
