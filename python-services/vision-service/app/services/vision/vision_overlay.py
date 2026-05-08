"""Phase 8 — Camera Overlay & HUD drawing utilities.

Provides a single entry point `render_annotated_frame(frame, analysis_data)`
that composites all overlay layers onto a copy of the input frame and returns
an annotated BGR image (numpy ndarray).

Layer order (bottom → top):
  1. YOLOv8 bounding boxes (filtered classes only)
  2. MediaPipe face mesh tessellation (thin cyan)
  3. Key landmark clusters (eyes/nose/lips/jaw dots)
  4. MediaPipe hand skeleton
  5. Pose skeleton (upper body)
  6. Head pose axes
  7. HUD text layer
  8. Alert flash overlay (semi-transparent colored rect)
  9. Active event badges (bottom-right)

All inputs are optional — missing data simply skips that layer.
"""

from __future__ import annotations

import base64
import logging
import math
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import cv2
import numpy as np

if TYPE_CHECKING:
    from app.services.vision.behavior_engine import BehaviorEvent
    from app.services.vision.vision_face_mesh import FaceMeshResult
    from app.services.vision.vision_hand_tracker import HandTrackingResult
    from app.services.vision.vision_pose_estimator import PoseResult
    from app.services.vision.vision_yolo_detector import YoloDetectionResult

logger = logging.getLogger(__name__)

# ── Color palette (BGR) ───────────────────────────────────────────────────────
_CYAN = (255, 220, 0)
_GREEN = (50, 220, 50)
_RED = (40, 40, 220)
_ORANGE = (30, 140, 255)
_BLUE = (220, 160, 0)
_GRAY = (160, 160, 160)
_WHITE = (230, 230, 230)
_YELLOW = (0, 220, 220)
_BLACK = (0, 0, 0)
_DARK = (20, 20, 20)

# Severity → (BGR color, alpha)
_SEVERITY_FLASH: dict[str, tuple[tuple[int, int, int], float]] = {
    "critical": (_RED, 0.30),
    "high":     (_RED, 0.25),
    "medium":   (_ORANGE, 0.20),
    "low":      (_BLUE, 0.15),
    "info":     (_BLUE, 0.10),
}

# Face mesh landmark clusters for colored dot rendering
_LEFT_EYE = [33, 160, 158, 133, 153, 144]
_RIGHT_EYE = [362, 385, 387, 263, 373, 380]
_NOSE_TIP = [1, 2, 98, 327]
_LIPS = [61, 291, 39, 181, 0, 17, 269, 405]
_JAW = [10, 338, 297, 332, 284, 251, 389]

# MediaPipe hand connections (21 landmarks)
_HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),           # thumb
    (0, 5), (5, 6), (6, 7), (7, 8),           # index
    (0, 9), (9, 10), (10, 11), (11, 12),      # middle
    (0, 13), (13, 14), (14, 15), (15, 16),    # ring
    (0, 17), (17, 18), (18, 19), (19, 20),    # pinky
    (5, 9), (9, 13), (13, 17),                # palm
]

# COCO pose upper-body connections
_POSE_CONNECTIONS = [
    (0, 1), (0, 2), (1, 3), (2, 4),           # nose to eyes/ears
    (5, 6),                                    # shoulder line
    (5, 7), (7, 9),                            # left arm
    (6, 8), (8, 10),                           # right arm
]


@dataclass
class OverlayData:
    """All analysis data bundled for overlay rendering."""

    # Vision module outputs (all optional)
    mesh_result: object | None = None         # FaceMeshResult
    hand_result: object | None = None         # HandTrackingResult
    pose_result: object | None = None         # PoseResult
    yolo_result: object | None = None         # YoloDetectionResult
    behavior_events: list = field(default_factory=list)  # list[BehaviorEvent]

    # Session HUD data
    username: str | None = None
    authenticated: bool = False
    posture_score: int = 100
    fps: float = 0.0


# ── Public entry point ────────────────────────────────────────────────────────

def render_annotated_frame(
    frame: np.ndarray,
    data: OverlayData,
    *,
    show_mesh: bool = True,
    show_landmarks: bool = True,
    show_hands: bool = True,
    show_pose: bool = True,
    show_yolo: bool = True,
    show_hud: bool = True,
    show_alert_flash: bool = True,
) -> np.ndarray:
    """Return an annotated copy of *frame* with all configured overlays."""
    out = frame.copy()
    h, w = out.shape[:2]

    # Layer 1 – YOLO boxes
    if show_yolo and data.yolo_result is not None:
        out = _draw_yolo_boxes(out, data.yolo_result, w, h)

    # Layers 2-3 – Face mesh + landmark dots
    if data.mesh_result is not None:
        if show_mesh:
            out = _draw_face_mesh_lines(out, data.mesh_result, w, h)
        if show_landmarks:
            out = _draw_landmark_clusters(out, data.mesh_result, w, h)

    # Layer 4 – Hand skeleton
    if show_hands and data.hand_result is not None:
        out = _draw_hand_skeleton(out, data.hand_result, w, h)

    # Layer 5 – Pose skeleton + spine indicator
    if show_pose and data.pose_result is not None:
        out = _draw_pose_skeleton(out, data.pose_result, w, h)

    # Layer 6 – Head pose axes (on nose tip)
    if show_landmarks and data.mesh_result is not None:
        out = _draw_head_pose_axes(out, data.mesh_result, w, h)

    # Layer 7 – HUD
    if show_hud:
        out = _draw_hud(out, data, w, h)

    # Layer 8 – Alert flash
    if show_alert_flash and data.behavior_events:
        out = _draw_alert_flash(out, data.behavior_events, w, h)

    # Layer 9 – Event badges
    out = _draw_event_badges(out, data.behavior_events, w, h)

    return out


def frame_to_base64(frame: np.ndarray, quality: int = 82) -> str:
    """Encode a BGR frame as a base64 JPEG string."""
    ok, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, quality])
    if not ok:
        return ""
    return base64.b64encode(buf.tobytes()).decode("ascii")


# ── Layer drawing functions ───────────────────────────────────────────────────

def _draw_yolo_boxes(frame: np.ndarray, yolo_result: object, w: int, h: int) -> np.ndarray:
    for det in yolo_result.detections:  # type: ignore[attr-defined]
        x1, y1, x2, y2 = det.bbox_norm
        px1, py1 = int(x1 * w), int(y1 * h)
        px2, py2 = int(x2 * w), int(y2 * h)
        color = _GREEN if det.class_name == "person" else _ORANGE
        cv2.rectangle(frame, (px1, py1), (px2, py2), color, 2)
        label = f"{det.class_name} {det.confidence:.0%}"
        _text_with_bg(frame, label, (px1 + 4, py1 + 18), 0.5, color)
    return frame


def _draw_face_mesh_lines(frame: np.ndarray, mesh: object, w: int, h: int) -> np.ndarray:
    """Draw a simplified face mesh using key connections."""
    lm = mesh.landmarks  # type: ignore[attr-defined]
    if len(lm) < 470:
        return frame

    def pt(i: int) -> tuple[int, int]:
        return (int(lm[i][0] * w), int(lm[i][1] * h))

    # Draw silhouette oval instead of full tessellation (much faster)
    silhouette = [10, 338, 297, 332, 284, 251, 389, 356, 454,
                  323, 361, 288, 397, 365, 379, 378, 400, 377,
                  152, 148, 176, 149, 150, 136, 172, 58, 132,
                  93, 234, 127, 162, 21, 54, 103, 67, 109]
    pts = [pt(i) for i in silhouette if i < len(lm)]
    if len(pts) > 2:
        cv2.polylines(frame, [np.array(pts, dtype=np.int32)], True, _CYAN, 1, cv2.LINE_AA)
    return frame


def _draw_landmark_clusters(frame: np.ndarray, mesh: object, w: int, h: int) -> np.ndarray:
    lm = mesh.landmarks  # type: ignore[attr-defined]
    if len(lm) < 410:
        return frame

    def pt(i: int) -> tuple[int, int]:
        return (int(lm[i][0] * w), int(lm[i][1] * h))

    for idx in _LEFT_EYE:
        cv2.circle(frame, pt(idx), 2, (255, 100, 0), -1)
    for idx in _RIGHT_EYE:
        cv2.circle(frame, pt(idx), 2, (255, 100, 0), -1)
    for idx in _NOSE_TIP:
        cv2.circle(frame, pt(idx), 2, (0, 200, 80), -1)
    for idx in _LIPS:
        cv2.circle(frame, pt(idx), 2, (0, 80, 255), -1)
    for idx in _JAW:
        if idx < len(lm):
            cv2.circle(frame, pt(idx), 2, _GRAY, -1)
    return frame


def _draw_head_pose_axes(frame: np.ndarray, mesh: object, w: int, h: int) -> np.ndarray:
    """Draw X/Y/Z axes at nose tip based on head pose angles."""
    lm = mesh.landmarks  # type: ignore[attr-defined]
    if len(lm) < 5:
        return frame

    yaw = math.radians(mesh.yaw)  # type: ignore[attr-defined]
    pitch = math.radians(mesh.pitch)  # type: ignore[attr-defined]
    roll = math.radians(mesh.roll)  # type: ignore[attr-defined]

    nose = (int(lm[4][0] * w), int(lm[4][1] * h))
    scale = max(40, int(min(w, h) * 0.08))

    # X-axis (roll, red)
    ex = int(nose[0] + scale * math.cos(roll))
    ey = int(nose[1] + scale * math.sin(roll))
    cv2.arrowedLine(frame, nose, (ex, ey), _RED, 2, tipLength=0.3)

    # Y-axis (pitch, green)
    px = int(nose[0] - scale * math.sin(pitch))
    py = int(nose[1] - scale * math.cos(pitch))
    cv2.arrowedLine(frame, nose, (px, py), _GREEN, 2, tipLength=0.3)

    # Z-axis (yaw, blue)
    zx = int(nose[0] + scale * math.sin(yaw))
    zy = int(nose[1] - scale * math.cos(yaw))
    cv2.arrowedLine(frame, nose, (zx, zy), _BLUE, 2, tipLength=0.3)

    return frame


def _draw_hand_skeleton(frame: np.ndarray, hand_result: object, w: int, h: int) -> np.ndarray:
    for hand in hand_result.hands:  # type: ignore[attr-defined]
        lm = hand.landmarks
        if len(lm) < 21:
            continue

        def pt(i: int) -> tuple[int, int]:
            return (int(lm[i][0] * w), int(lm[i][1] * h))

        for a, b in _HAND_CONNECTIONS:
            cv2.line(frame, pt(a), pt(b), _YELLOW, 2, cv2.LINE_AA)
        for i in range(21):
            cv2.circle(frame, pt(i), 4, _WHITE, -1)
            cv2.circle(frame, pt(i), 4, _YELLOW, 1)
    return frame


def _draw_pose_skeleton(frame: np.ndarray, pose: object, w: int, h: int) -> np.ndarray:
    kps = pose.keypoints  # type: ignore[attr-defined]
    if len(kps) < 11:
        return frame

    def pt(i: int) -> tuple[int, int] | None:
        if i >= len(kps) or kps[i] is None:
            return None
        return (int(kps[i].x * w), int(kps[i].y * h))

    for a, b in _POSE_CONNECTIONS:
        pa, pb = pt(a), pt(b)
        if pa and pb:
            cv2.line(frame, pa, pb, _GREEN, 2, cv2.LINE_AA)

    for i in range(min(11, len(kps))):
        p = pt(i)
        if p:
            color = _GREEN if pose.posture_score >= 80 else _ORANGE if pose.posture_score >= 50 else _RED  # type: ignore[attr-defined]
            cv2.circle(frame, p, 5, color, -1)
    return frame


def _draw_hud(frame: np.ndarray, data: OverlayData, w: int, h: int) -> np.ndarray:
    """Draw semi-transparent HUD panel with user info, FPS, and posture bar."""
    # Top bar background
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (w, 38), _DARK, -1)
    cv2.addWeighted(overlay, 0.65, frame, 0.35, 0, frame)

    # Top-left: user + auth status
    user_label = data.username or "No user"
    auth_indicator = " ✓" if data.authenticated else " ✗"
    _text_cv2(frame, f"User: {user_label}{auth_indicator}", (8, 26),
              color=_GREEN if data.authenticated else _RED)

    # Top-right: FPS
    if data.fps > 0:
        fps_text = f"FPS: {data.fps:.0f}"
        tw, _ = _text_size(fps_text)
        _text_cv2(frame, fps_text, (w - tw - 8, 26), color=_WHITE)

    # Head pose angles (if face mesh available)
    if data.mesh_result is not None:
        mesh = data.mesh_result
        pose_text = f"Yaw:{mesh.yaw:+.0f}°  Pitch:{mesh.pitch:+.0f}°  Roll:{mesh.roll:+.0f}°"  # type: ignore[attr-defined]
        _text_cv2(frame, pose_text, (8, h - 50), color=_CYAN, scale=0.45)

    # Bottom-left: posture score bar
    bar_x, bar_y = 8, h - 28
    bar_w = min(160, w // 3)
    bar_h = 10
    fill = int(bar_w * data.posture_score / 100)
    bar_color = _GREEN if data.posture_score >= 80 else _ORANGE if data.posture_score >= 50 else _RED

    cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h), (60, 60, 60), -1)
    cv2.rectangle(frame, (bar_x, bar_y), (bar_x + fill, bar_y + bar_h), bar_color, -1)
    _text_cv2(frame, f"Posture: {data.posture_score}%", (bar_x, bar_y - 5),
              color=bar_color, scale=0.4)

    # EAR / MAR indicators (if face mesh available)
    if data.mesh_result is not None:
        mesh = data.mesh_result
        ear_color = _RED if mesh.is_drowsy else _WHITE  # type: ignore[attr-defined]
        mar_color = _ORANGE if mesh.is_yawning else _WHITE  # type: ignore[attr-defined]
        _text_cv2(frame, f"EAR:{mesh.ear:.2f}", (bar_x + bar_w + 12, h - 28), color=ear_color, scale=0.4)  # type: ignore[attr-defined]
        _text_cv2(frame, f"MAR:{mesh.mar:.2f}", (bar_x + bar_w + 12, h - 14), color=mar_color, scale=0.4)  # type: ignore[attr-defined]

    return frame


def _draw_alert_flash(frame: np.ndarray, events: list, w: int, h: int) -> np.ndarray:
    """Flash a semi-transparent colored rect over the frame for active events."""
    if not events:
        return frame

    # Pick highest severity
    priority_order = ["critical", "high", "medium", "low", "info"]
    highest = "info"
    for sev in priority_order:
        if any(e.severity == sev for e in events):
            highest = sev
            break

    color, alpha = _SEVERITY_FLASH.get(highest, (_RED, 0.20))
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (w, h), color, -1)
    cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)

    # Border flash
    border = 3
    cv2.rectangle(frame, (border, border), (w - border, h - border), color, border * 2)
    return frame


def _draw_event_badges(frame: np.ndarray, events: list, w: int, h: int) -> np.ndarray:
    """Draw active event badges in the bottom-right corner."""
    if not events:
        return frame

    badge_h = 22
    pad = 6
    x_right = w - 8
    y_start = h - 8

    for event in events[:5]:   # max 5 badges
        sev = event.severity
        color, _ = _SEVERITY_FLASH.get(sev, (_ORANGE, 0.20))
        label = f"⚑ {event.event_type}"
        tw, _ = _text_size(label, scale=0.45)
        bx1 = x_right - tw - pad * 2
        by1 = y_start - badge_h
        by2 = y_start

        overlay = frame.copy()
        cv2.rectangle(overlay, (bx1 - 2, by1 - 2), (x_right + 2, by2 + 2), color, -1)
        cv2.addWeighted(overlay, 0.70, frame, 0.30, 0, frame)
        cv2.rectangle(frame, (bx1 - 2, by1 - 2), (x_right + 2, by2 + 2), color, 1)
        _text_cv2(frame, label, (bx1 + pad, by2 - 5), color=_WHITE, scale=0.45)
        y_start -= badge_h + pad

    return frame


# ── Text helpers ──────────────────────────────────────────────────────────────

def _text_cv2(
    frame: np.ndarray,
    text: str,
    origin: tuple[int, int],
    color: tuple[int, int, int] = _WHITE,
    scale: float = 0.55,
    thickness: int = 1,
) -> None:
    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(frame, text, origin, font, scale, _BLACK, thickness + 2, cv2.LINE_AA)
    cv2.putText(frame, text, origin, font, scale, color, thickness, cv2.LINE_AA)


def _text_with_bg(
    frame: np.ndarray,
    text: str,
    origin: tuple[int, int],
    scale: float,
    color: tuple[int, int, int],
) -> None:
    tw, th = _text_size(text, scale)
    x, y = origin
    cv2.rectangle(frame, (x - 2, y - th - 2), (x + tw + 2, y + 2), _DARK, -1)
    _text_cv2(frame, text, (x, y), color, scale)


def _text_size(text: str, scale: float = 0.55) -> tuple[int, int]:
    (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, scale, 1)
    return tw, th
