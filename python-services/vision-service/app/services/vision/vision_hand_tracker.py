"""Module D — Hand Tracking.

Uses MediaPipe Hands to detect up to 2 hands and return:
- 21 normalized landmarks per hand for frontend skeleton rendering
- Hand-face proximity score
- Hand-mouth proximity (for EATING / DRINKING / SMOKING events)
- Face-touch detection
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field

import cv2
import numpy as np

logger = logging.getLogger(__name__)

try:
    import mediapipe as mp  # type: ignore[import-untyped]
    _mp_hands = mp.solutions.hands  # type: ignore[attr-defined]
    _MP_AVAILABLE = True
except (ImportError, AttributeError):  # pragma: no cover
    _MP_AVAILABLE = False
    logger.warning("mediapipe not installed or solutions API unavailable — hand tracking disabled")

# MediaPipe wrist and fingertip indices
_WRIST = 0
_INDEX_TIP = 8
_MIDDLE_TIP = 12
_RING_TIP = 16
_PINKY_TIP = 20
_THUMB_TIP = 4
_INDEX_MCP = 5   # knuckle — used for hand center approximation

# Proximity thresholds (normalized [0,1] coordinate space)
_FACE_TOUCH_DISTANCE = 0.18    # hand near any face landmark cluster
_MOUTH_PROXIMITY = 0.12        # fingertip near mouth centre


@dataclass
class HandResult:
    """Tracking result for a single detected hand."""

    # 21 normalized (x, y, z) tuples in [0,1] relative to frame
    landmarks: list[tuple[float, float, float]] = field(default_factory=list)
    handedness: str = "Unknown"   # "Left" | "Right" (mirrored = camera view)

    # Derived signals
    center_x: float = 0.0        # normalized center of palm
    center_y: float = 0.0

    # Proximity flags
    near_face: bool = False       # hand centroid within face bbox
    near_mouth: bool = False      # fingertip near mouth landmark


@dataclass
class HandTrackingResult:
    """All hand-tracking outputs for one frame."""

    hands: list[HandResult] = field(default_factory=list)

    # Aggregated signals
    face_touch_detected: bool = False   # any hand near face
    mouth_touch_detected: bool = False  # any fingertip near mouth


class VisionHandTracker:
    """MediaPipe Hands wrapper."""

    def __init__(self) -> None:
        self._detector: object | None = None

    # ------------------------------------------------------------------ #
    # Public API                                                           #
    # ------------------------------------------------------------------ #

    def analyze(
        self,
        image: np.ndarray,
        face_landmarks: list[tuple[float, float, float]] | None = None,
    ) -> HandTrackingResult | None:
        """Detect hands in *image*.

        *face_landmarks*: optional 468-point list from VisionFaceMesh — used
        to compute accurate hand-face and hand-mouth proximity.
        Returns None if MediaPipe is unavailable.
        """
        if not _MP_AVAILABLE:
            return None

        detector = self._get_detector()
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = detector.process(rgb)

        if not results.multi_hand_landmarks:
            return HandTrackingResult()

        hand_results: list[HandResult] = []
        for idx, hand_lm in enumerate(results.multi_hand_landmarks):
            landmarks = [
                (round(lm.x, 5), round(lm.y, 5), round(lm.z, 5))
                for lm in hand_lm.landmark
            ]

            # Handedness label from MediaPipe (Left/Right from camera's POV)
            label = "Unknown"
            if results.multi_handedness and idx < len(results.multi_handedness):
                label = results.multi_handedness[idx].classification[0].label

            # Palm center ≈ average of wrist + 4 MCP joints
            cx = float(np.mean([landmarks[i][0] for i in [0, 5, 9, 13, 17]]))
            cy = float(np.mean([landmarks[i][1] for i in [0, 5, 9, 13, 17]]))

            near_face, near_mouth = self._compute_proximity(landmarks, face_landmarks)

            hand_results.append(HandResult(
                landmarks=landmarks,
                handedness=label,
                center_x=round(cx, 4),
                center_y=round(cy, 4),
                near_face=near_face,
                near_mouth=near_mouth,
            ))

        face_touch = any(h.near_face for h in hand_results)
        mouth_touch = any(h.near_mouth for h in hand_results)

        return HandTrackingResult(
            hands=hand_results,
            face_touch_detected=face_touch,
            mouth_touch_detected=mouth_touch,
        )

    # ------------------------------------------------------------------ #
    # Private helpers                                                      #
    # ------------------------------------------------------------------ #

    def _get_detector(self) -> object:
        if self._detector is None:
            self._detector = _mp_hands.Hands(
                static_image_mode=False,
                max_num_hands=2,
                model_complexity=0,          # fastest
                min_detection_confidence=0.6,
                min_tracking_confidence=0.5,
            )
        return self._detector

    @staticmethod
    def _compute_proximity(
        hand_lm: list[tuple[float, float, float]],
        face_lm: list[tuple[float, float, float]] | None,
    ) -> tuple[bool, bool]:
        """Return (near_face, near_mouth) flags."""
        if face_lm is None or len(face_lm) < 15:
            return False, False

        # Palm centre
        cx = float(np.mean([hand_lm[i][0] for i in [0, 5, 9, 13, 17]]))
        cy = float(np.mean([hand_lm[i][1] for i in [0, 5, 9, 13, 17]]))

        # Face bounding box from landmarks
        face_xs = [lm[0] for lm in face_lm]
        face_ys = [lm[1] for lm in face_lm]
        face_cx = (min(face_xs) + max(face_xs)) / 2.0
        face_cy = (min(face_ys) + max(face_ys)) / 2.0
        face_diag = math.hypot(max(face_xs) - min(face_xs), max(face_ys) - min(face_ys))

        dist_to_face = math.hypot(cx - face_cx, cy - face_cy)
        near_face = dist_to_face < (face_diag * _FACE_TOUCH_DISTANCE / 0.18)

        # Mouth centre (landmark 13 = top lip, 14 = bottom lip)
        mouth_cx = (face_lm[13][0] + face_lm[14][0]) / 2.0
        mouth_cy = (face_lm[13][1] + face_lm[14][1]) / 2.0

        # Check fingertips proximity to mouth
        near_mouth = False
        for tip_idx in [_INDEX_TIP, _MIDDLE_TIP, _RING_TIP, _THUMB_TIP]:
            tip = hand_lm[tip_idx]
            if math.hypot(tip[0] - mouth_cx, tip[1] - mouth_cy) < _MOUTH_PROXIMITY:
                near_mouth = True
                break

        return near_face, near_mouth
