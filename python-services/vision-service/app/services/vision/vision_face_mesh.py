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
from typing import Literal

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

# ─── Iris landmark indices (requires refine_landmarks=True) ────────────────
_RIGHT_IRIS_CENTER = 468   # right iris centre
_LEFT_IRIS_CENTER = 473    # left iris centre

# Eye corner indices used for iris-offset normalisation
_RIGHT_EYE_OUTER = 33
_RIGHT_EYE_INNER = 133
_LEFT_EYE_OUTER = 263
_LEFT_EYE_INNER = 362

# Gaze zone classification thresholds (fraction of eye width)
_GAZE_H_THRESHOLD = 0.15   # horizontal: beyond this → left / right
_GAZE_V_THRESHOLD = 0.10   # vertical:   beyond this → up / down


@dataclass
class GazeResult:
    """Iris-based gaze direction for a single (owner) face."""

    # Normalised offset of iris from eye centre: positive x = looking right,
    # positive y = looking down.  Range roughly [-0.5, 0.5].
    gaze_vector: tuple[float, float]

    looking_at_screen: bool  # True when gaze_zone == "center"
    gaze_zone: Literal["center", "left", "right", "up", "down", "away"]

    # Confidence of the zone classification (higher when iris is clearly displaced)
    confidence: float


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
        self._gaze_mesh: object | None = None  # separate instance for crop-based gaze
        self._owner_mesh: object | None = None  # separate instance for owner-crop analysis

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

    def analyze_in_bbox(
        self,
        frame: np.ndarray,
        owner_bbox: tuple[int, int, int, int],
    ) -> FaceMeshResult | None:
        """Run face mesh ONLY on the owner's face region.

        Crops *frame* to *owner_bbox* (padded), runs MediaPipe on the crop so no
        other face in the frame can be selected, then remaps the landmarks back to
        full-frame normalized coordinates. Downstream consumers (mouth region, hand
        proximity, overlay) therefore keep working unchanged — they always receive
        full-frame coordinates, only now guaranteed to belong to the owner.

        Args:
            frame:      Full BGR frame (uint8).
            owner_bbox: (x, y, w, h) pixel bounding box of the owner's face.

        Returns:
            :class:`FaceMeshResult` or ``None`` when MediaPipe is unavailable, the
            bbox is degenerate, or no face is found in the crop.
        """
        if not _MP_AVAILABLE:
            return None

        x, y, bw, bh = owner_bbox
        if bw <= 0 or bh <= 0:
            return None

        frame_h, frame_w = frame.shape[:2]
        # Expand the crop by 20 % on each side for robust landmark detection
        pad = int(max(bw, bh) * 0.20)
        x1 = max(0, x - pad)
        y1 = max(0, y - pad)
        x2 = min(frame_w, x + bw + pad)
        y2 = min(frame_h, y + bh + pad)
        if x2 <= x1 or y2 <= y1:
            return None

        crop = frame[y1:y2, x1:x2]
        if crop.size == 0:
            return None
        crop_w = x2 - x1
        crop_h = y2 - y1

        rgb = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)
        results = self._get_owner_mesh().process(rgb)
        if not results.multi_face_landmarks:
            return None

        face_lm = results.multi_face_landmarks[0]
        # Crop-relative [0,1] → full-frame [0,1]:  X = (x1 + lx*crop_w) / frame_w
        landmarks = [
            (
                round((x1 + lm.x * crop_w) / frame_w, 5),
                round((y1 + lm.y * crop_h) / frame_h, 5),
                round(lm.z, 5),
            )
            for lm in face_lm.landmark
        ]

        ear_left = self._ear(landmarks, _LEFT_EYE)
        ear_right = self._ear(landmarks, _RIGHT_EYE)
        ear = (ear_left + ear_right) / 2.0
        mar = self._mar(landmarks)
        yaw, pitch, roll = self._head_pose(landmarks, frame_w, frame_h)
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

    def extract_owner_gaze(
        self,
        frame: np.ndarray,
        owner_bbox: tuple[int, int, int, int],
    ) -> GazeResult | None:
        """Compute iris-based gaze direction for the owner's face crop.

        Runs a dedicated FaceMesh instance on the cropped owner region so that
        other faces in the frame never influence the result.

        Args:
            frame:      Full BGR frame (uint8).
            owner_bbox: (x, y, w, h) pixel bounding box of the owner's face.

        Returns:
            :class:`GazeResult` or ``None`` when MediaPipe is not available or
            no face / iris landmarks are found in the crop.
        """
        if not _MP_AVAILABLE:
            return None

        x, y, w, h = owner_bbox
        if w <= 0 or h <= 0:
            return None

        # Expand the crop by 20 % on each side for better landmark detection
        pad = int(max(w, h) * 0.20)
        x1 = max(0, x - pad)
        y1 = max(0, y - pad)
        x2 = min(frame.shape[1], x + w + pad)
        y2 = min(frame.shape[0], y + h + pad)

        if x2 <= x1 or y2 <= y1:
            return None

        crop = frame[y1:y2, x1:x2]
        if crop.size == 0:
            return None

        rgb = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)
        results = self._get_gaze_mesh().process(rgb)

        if not results.multi_face_landmarks:
            return None

        face_lm = results.multi_face_landmarks[0]
        # Need at least landmark 477 (right-most iris point)
        if len(face_lm.landmark) <= _LEFT_IRIS_CENTER:
            return None

        landmarks = [(lm.x, lm.y) for lm in face_lm.landmark]

        right_gaze = self._eye_gaze(
            landmarks,
            iris_center_idx=_RIGHT_IRIS_CENTER,
            eye_outer_idx=_RIGHT_EYE_OUTER,
            eye_inner_idx=_RIGHT_EYE_INNER,
        )
        left_gaze = self._eye_gaze(
            landmarks,
            iris_center_idx=_LEFT_IRIS_CENTER,
            eye_outer_idx=_LEFT_EYE_OUTER,
            eye_inner_idx=_LEFT_EYE_INNER,
        )

        valid = [g for g in (right_gaze, left_gaze) if g is not None]
        if not valid:
            return None

        gaze_x = sum(g[0] for g in valid) / len(valid)
        gaze_y = sum(g[1] for g in valid) / len(valid)

        zone = self._classify_zone(gaze_x, gaze_y)
        looking = zone == "center"

        # Confidence: higher when iris is clearly displaced from eye centre
        magnitude = math.hypot(gaze_x, gaze_y)
        confidence = round(min(1.0, max(0.35, magnitude * 3.5 + 0.25)), 4)

        return GazeResult(
            gaze_vector=(round(gaze_x, 4), round(gaze_y, 4)),
            looking_at_screen=looking,
            gaze_zone=zone,
            confidence=confidence,
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

    def _get_gaze_mesh(self) -> object:
        """Dedicated FaceMesh for crop-based gaze extraction.

        Uses ``static_image_mode=True`` so every crop is treated independently —
        no temporal tracking state bleeds between different crop positions.
        ``refine_landmarks=True`` is mandatory for iris indices 468-477.
        """
        if self._gaze_mesh is None:
            self._gaze_mesh = _mp_face_mesh.FaceMesh(
                static_image_mode=True,
                max_num_faces=1,
                refine_landmarks=True,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5,
            )
        return self._gaze_mesh

    def _get_owner_mesh(self) -> object:
        """Dedicated FaceMesh for the owner-cropped analysis path.

        Separate instance from the full-frame ``_mesh`` and the iris ``_gaze_mesh``
        so their internal tracking states never interfere within a single frame.
        ``refine_landmarks=True`` keeps landmark indexing identical to ``analyze``.
        """
        if self._owner_mesh is None:
            self._owner_mesh = _mp_face_mesh.FaceMesh(
                static_image_mode=False,
                max_num_faces=1,
                refine_landmarks=True,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5,
            )
        return self._owner_mesh

    @staticmethod
    def _eye_gaze(
        landmarks: list[tuple[float, float]],
        iris_center_idx: int,
        eye_outer_idx: int,
        eye_inner_idx: int,
    ) -> tuple[float, float] | None:
        """Compute normalised iris offset from eye centre for one eye.

        Returns (gaze_x, gaze_y) normalised by eye width, or ``None`` when the
        eye width is degenerate.  Positive x = looking right; positive y = down.
        """
        if iris_center_idx >= len(landmarks):
            return None

        iris = landmarks[iris_center_idx]
        outer = landmarks[eye_outer_idx]
        inner = landmarks[eye_inner_idx]

        eye_cx = (outer[0] + inner[0]) / 2.0
        eye_cy = (outer[1] + inner[1]) / 2.0
        eye_width = abs(outer[0] - inner[0])

        if eye_width < 1e-6:
            return None

        return (
            (iris[0] - eye_cx) / eye_width,
            (iris[1] - eye_cy) / eye_width,
        )

    @staticmethod
    def _classify_zone(gx: float, gy: float) -> Literal["center", "left", "right", "up", "down", "away"]:
        """Map a (gaze_x, gaze_y) vector to a named screen zone."""
        horiz = abs(gx) >= _GAZE_H_THRESHOLD
        vert = abs(gy) >= _GAZE_V_THRESHOLD

        if not horiz and not vert:
            return "center"
        if horiz and not vert:
            return "right" if gx > 0 else "left"
        if vert and not horiz:
            return "down" if gy > 0 else "up"
        # Both thresholds exceeded: oblique / ambiguous direction
        return "away"

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
