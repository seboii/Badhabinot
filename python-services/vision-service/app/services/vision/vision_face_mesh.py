"""Module C — Face Mesh & Landmark Overlay.

Uses MediaPipe FaceMesh (468 landmarks) to compute:
- Normalized landmark positions for frontend overlay rendering
- Eye Aspect Ratio (EAR) for drowsiness detection
- Mouth Aspect Ratio (MAR) for yawning detection
- Head pose angles (yaw, pitch, roll) via solvePnP
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
    _mp_face_mesh = mp.solutions.face_mesh  # type: ignore[attr-defined]
    _MP_AVAILABLE = True
except (ImportError, AttributeError):  # pragma: no cover
    _MP_AVAILABLE = False
    logger.warning("mediapipe not installed or solutions API unavailable — face mesh disabled")


# ─── MediaPipe FaceMesh landmark indices ───────────────────────────────────
# Eye landmarks for EAR (6 points per eye)
_RIGHT_EYE = [33, 160, 158, 133, 153, 144]
_LEFT_EYE = [362, 385, 387, 263, 373, 380]

# Mouth landmarks for MAR
_MOUTH_TOP = 13
_MOUTH_BOTTOM = 14
_MOUTH_LEFT = 78
_MOUTH_RIGHT = 308

# Head pose reference landmarks (nose tip, chin, eye corners, mouth corners)
_POSE_LM_IDS = [4, 152, 263, 33, 291, 61]
# Corresponding 3-D model points (canonical face, mm units)
_POSE_3D_POINTS = np.array([
    [0.0,    0.0,    0.0],    # nose tip
    [0.0,  -63.6,  -12.5],   # chin
    [-43.3,  32.7, -26.0],   # left eye corner
    [43.3,  32.7, -26.0],    # right eye corner
    [-28.9, -28.9, -24.1],   # left mouth corner
    [28.9, -28.9, -24.1],    # right mouth corner
], dtype=np.float64)

_EAR_DROWSY_THRESHOLD = 0.25
_MAR_YAWN_THRESHOLD = 0.60


@dataclass
class FaceMeshResult:
    """All face-mesh outputs for one frame."""

    # 468 normalized (x, y, z) tuples, values in [0,1] relative to frame size
    landmarks: list[tuple[float, float, float]] = field(default_factory=list)

    # Per-eye and combined EAR
    ear_left: float = 0.0
    ear_right: float = 0.0
    ear: float = 0.0            # average of both eyes
    is_drowsy: bool = False     # EAR < threshold

    # Mouth openness
    mar: float = 0.0
    is_yawning: bool = False    # MAR > threshold

    # Head pose in degrees
    yaw: float = 0.0            # left/right rotation
    pitch: float = 0.0          # up/down tilt
    roll: float = 0.0           # head tilt (ear to shoulder)

    # Gaze direction approximation (simple: is face looking forward?)
    gaze_off_screen: bool = False  # True if |yaw| > 30° or |pitch| > 25°


class VisionFaceMesh:
    """Singleton-style MediaPipe FaceMesh wrapper.

    Thread-safe: each call creates a short-lived context; initialization
    happens once via lazy loading.
    """

    _instance: mp.solutions.face_mesh.FaceMesh | None = None  # type: ignore[name-defined]

    def __init__(self) -> None:
        self._mesh: object | None = None

    # ------------------------------------------------------------------ #
    # Public API                                                           #
    # ------------------------------------------------------------------ #

    def analyze(self, image: np.ndarray) -> FaceMeshResult | None:
        """Run face mesh analysis on *image* (BGR, uint8).

        Returns None if MediaPipe is not available or no face is found.
        """
        if not _MP_AVAILABLE:
            return None

        mesh = self._get_mesh()
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = mesh.process(rgb)

        if not results.multi_face_landmarks:
            return None

        # Use first detected face
        face_lm = results.multi_face_landmarks[0]
        h, w = image.shape[:2]

        landmarks = [
            (round(lm.x, 5), round(lm.y, 5), round(lm.z, 5))
            for lm in face_lm.landmark
        ]

        ear_left = self._ear(landmarks, _LEFT_EYE)
        ear_right = self._ear(landmarks, _RIGHT_EYE)
        ear = (ear_left + ear_right) / 2.0

        mar = self._mar(landmarks)
        yaw, pitch, roll = self._head_pose(landmarks, w, h)
        gaze_off = abs(yaw) > 30.0 or abs(pitch) > 25.0

        return FaceMeshResult(
            landmarks=landmarks,
            ear_left=round(ear_left, 4),
            ear_right=round(ear_right, 4),
            ear=round(ear, 4),
            is_drowsy=ear < _EAR_DROWSY_THRESHOLD,
            mar=round(mar, 4),
            is_yawning=mar > _MAR_YAWN_THRESHOLD,
            yaw=round(yaw, 2),
            pitch=round(pitch, 2),
            roll=round(roll, 2),
            gaze_off_screen=gaze_off,
        )

    # ------------------------------------------------------------------ #
    # Private helpers                                                      #
    # ------------------------------------------------------------------ #

    def _get_mesh(self) -> object:
        if self._mesh is None:
            self._mesh = _mp_face_mesh.FaceMesh(
                static_image_mode=False,
                max_num_faces=1,
                refine_landmarks=True,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5,
            )
        return self._mesh

    @staticmethod
    def _dist(p1: tuple[float, float, float], p2: tuple[float, float, float]) -> float:
        return math.hypot(p1[0] - p2[0], p1[1] - p2[1])

    def _ear(self, lm: list[tuple[float, float, float]], ids: list[int]) -> float:
        """Eye Aspect Ratio — uses 6 landmark indices."""
        p = [lm[i] for i in ids]
        # EAR = (||p2-p6|| + ||p3-p5||) / (2 * ||p1-p4||)
        vertical1 = self._dist(p[1], p[5])
        vertical2 = self._dist(p[2], p[4])
        horizontal = self._dist(p[0], p[3])
        if horizontal < 1e-6:
            return 0.0
        return (vertical1 + vertical2) / (2.0 * horizontal)

    def _mar(self, lm: list[tuple[float, float, float]]) -> float:
        """Mouth Aspect Ratio — vertical / horizontal opening."""
        top = lm[_MOUTH_TOP]
        bottom = lm[_MOUTH_BOTTOM]
        left = lm[_MOUTH_LEFT]
        right = lm[_MOUTH_RIGHT]
        vertical = self._dist(top, bottom)
        horizontal = self._dist(left, right)
        if horizontal < 1e-6:
            return 0.0
        return vertical / horizontal

    @staticmethod
    def _head_pose(
        lm: list[tuple[float, float, float]],
        w: int,
        h: int,
    ) -> tuple[float, float, float]:
        """Estimate yaw / pitch / roll via solvePnP.

        Returns angles in degrees. (0, 0, 0) = facing directly at camera.
        """
        image_points = np.array(
            [(lm[i][0] * w, lm[i][1] * h) for i in _POSE_LM_IDS],
            dtype=np.float64,
        )
        focal = w  # rough approximation
        camera_matrix = np.array(
            [[focal, 0, w / 2], [0, focal, h / 2], [0, 0, 1]],
            dtype=np.float64,
        )
        dist_coeffs = np.zeros((4, 1), dtype=np.float64)

        ok, rvec, _ = cv2.solvePnP(
            _POSE_3D_POINTS,
            image_points,
            camera_matrix,
            dist_coeffs,
            flags=cv2.SOLVEPNP_ITERATIVE,
        )
        if not ok:
            return 0.0, 0.0, 0.0

        rmat, _ = cv2.Rodrigues(rvec)
        # Decompose rotation matrix to Euler angles
        sy = math.sqrt(rmat[0, 0] ** 2 + rmat[1, 0] ** 2)
        singular = sy < 1e-6
        if not singular:
            pitch = math.atan2(-rmat[2, 0], sy)
            yaw = math.atan2(rmat[1, 0], rmat[0, 0])
            roll = math.atan2(rmat[2, 1], rmat[2, 2])
        else:
            pitch = math.atan2(-rmat[2, 0], sy)
            yaw = 0.0
            roll = math.atan2(-rmat[1, 2], rmat[1, 1])

        return (
            math.degrees(yaw),
            math.degrees(pitch),
            math.degrees(roll),
        )
