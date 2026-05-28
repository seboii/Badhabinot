from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field


# ══════════════════════════════════════════════════════════════════
# Existing / legacy schemas (unchanged — kept for backward compat)
# ══════════════════════════════════════════════════════════════════

class VisionAnalysisRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    request_id: str
    user_id: str
    session_id: str
    frame_id: str
    captured_at: datetime
    image_base64: str
    image_content_type: str


class DetectionEvidence(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    face_detected: bool
    upper_body_detected: bool
    hand_count: int = Field(ge=0)
    posture_alignment_score: float | None = Field(default=None, ge=0.0, le=1.0)
    hand_face_proximity_score: float | None = Field(default=None, ge=0.0, le=1.0)
    hand_motion_score: float | None = Field(default=None, ge=0.0, le=1.0)
    repetitive_motion_score: float | None = Field(default=None, ge=0.0, le=1.0)
    repeated_hand_to_face_score: float | None = Field(default=None, ge=0.0, le=1.0)
    elongated_object_score: float | None = Field(default=None, ge=0.0, le=1.0)


class VisionDetection(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    event_type: Literal["poor_posture", "hand_movement_pattern", "smoking_like_gesture"]
    confidence: float = Field(ge=0.0, le=1.0)
    severity: Literal["low", "medium", "high"]
    recommendation_hint: str
    evidence: DetectionEvidence


class ProcessingDetails(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    frame_width: int = Field(ge=1)
    frame_height: int = Field(ge=1)
    vision_latency_ms: int = Field(ge=0)


# ══════════════════════════════════════════════════════════════════
# New schemas — Module A: Face Authentication
# ══════════════════════════════════════════════════════════════════

class FaceAuthStatus(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    enabled: bool             # True if user has a stored face profile
    authenticated: bool       # True if live face matches stored profile
    confidence: float = Field(ge=0.0, le=1.0)
    frames_enrolled: int = Field(ge=0)
    error: str | None = None


class FaceVerifyRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    image_base64: str
    image_content_type: str = "image/jpeg"


class FaceVerifyResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    verified: bool
    confidence: float = Field(ge=0.0, le=1.0)
    message: str


# ══════════════════════════════════════════════════════════════════
# New schemas — Module C: Face Mesh
# ══════════════════════════════════════════════════════════════════

class FaceMeshData(BaseModel):
    """Normalized (x, y, z) landmark positions for frontend overlay rendering.

    Frontend multiplies x/y by canvas width/height to get pixel coords.
    """
    model_config = ConfigDict(protected_namespaces=())

    # 468 landmarks as flat list of [x, y, z] triples — kept compact for JSON
    landmarks: list[list[float]] = Field(default_factory=list)

    ear: float = Field(default=0.0, ge=0.0)      # Eye Aspect Ratio
    mar: float = Field(default=0.0, ge=0.0)      # Mouth Aspect Ratio
    is_drowsy: bool = False
    is_yawning: bool = False

    yaw: float = 0.0      # head pose degrees
    pitch: float = 0.0
    roll: float = 0.0

    gaze_off_screen: bool = False


# ══════════════════════════════════════════════════════════════════
# New schemas — Module D: Hand Tracking
# ══════════════════════════════════════════════════════════════════

class HandData(BaseModel):
    """Single hand tracking result."""
    model_config = ConfigDict(protected_namespaces=())

    # 21 landmarks as flat list of [x, y, z] triples
    landmarks: list[list[float]] = Field(default_factory=list)
    handedness: str = "Unknown"
    center_x: float = 0.0
    center_y: float = 0.0
    near_face: bool = False
    near_mouth: bool = False


class HandTrackingData(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    hands: list[HandData] = Field(default_factory=list)
    face_touch_detected: bool = False
    mouth_touch_detected: bool = False


# ══════════════════════════════════════════════════════════════════
# New schemas — Module E: Pose Estimation
# ══════════════════════════════════════════════════════════════════

class PoseKeypointData(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    x: float
    y: float
    confidence: float


class PoseData(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    # Up to 17 COCO keypoints (None = not detected)
    keypoints: list[PoseKeypointData | None] = Field(default_factory=list)
    spine_tilt_angle: float = 0.0
    shoulder_tilt_angle: float = 0.0
    posture_score: int = Field(default=100, ge=0, le=100)
    is_slouching: bool = False
    # Normalized person bounding box (x1, y1, x2, y2)
    person_bbox: list[float] | None = None


# ══════════════════════════════════════════════════════════════════
# New schemas — YOLO detections
# ══════════════════════════════════════════════════════════════════

class ObjectDetectionData(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    class_id: int
    class_name: str
    confidence: float = Field(ge=0.0, le=1.0)
    # Normalized (x1, y1, x2, y2)
    bbox_norm: list[float]


class YoloDetectionData(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    detections: list[ObjectDetectionData] = Field(default_factory=list)
    bottle_near_mouth: bool = False
    cup_near_mouth: bool = False
    phone_detected: bool = False


# ══════════════════════════════════════════════════════════════════
# New schemas — Module F: Behavioral Events
# ══════════════════════════════════════════════════════════════════

class BehaviorEventData(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    event_type: str
    severity: Literal["low", "medium", "high"]
    confidence: float = Field(ge=0.0, le=1.0)
    detail: str = ""


# ══════════════════════════════════════════════════════════════════
# New schemas — Module G: Owner Tracking & Iris Gaze
# ══════════════════════════════════════════════════════════════════

class GazeData(BaseModel):
    """Iris-based gaze direction for the authenticated owner's face."""
    model_config = ConfigDict(protected_namespaces=())

    # Normalised iris offset from eye centre: positive x = right, positive y = down
    gaze_vector: list[float] = Field(
        default_factory=list,
        description="[horizontal, vertical] offset, each roughly in [-0.5, 0.5]",
    )
    looking_at_screen: bool
    gaze_zone: Literal["center", "left", "right", "up", "down", "away"]
    confidence: float = Field(ge=0.0, le=1.0)


class OwnerTrackingData(BaseModel):
    """Aggregated owner identification and gaze result for one frame."""
    model_config = ConfigDict(protected_namespaces=())

    owner_tracked: bool            # True = owner face identified in this frame
    owner_gaze: GazeData | None = None
    strangers_in_frame: int = Field(default=0, ge=0)


# ══════════════════════════════════════════════════════════════════
# Face registration endpoints schemas
# ══════════════════════════════════════════════════════════════════

class FaceRegisterRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    user_id: str
    image_base64: str
    image_content_type: str = "image/jpeg"
    pose_hint: str | None = None  # "front", "left", "right" — optional validation hint


class FaceRegisterResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    user_id: str
    success: bool
    frames_enrolled: int
    message: str


class FaceDeleteResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    user_id: str
    deleted: bool


# ══════════════════════════════════════════════════════════════════
# Extended VisionAnalysisResponse (backward-compatible)
# All new fields are Optional so existing callers are unaffected.
# ══════════════════════════════════════════════════════════════════

class VisionAnalysisResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    # ── Existing fields (unchanged) ─────────────────────────────
    request_id: str
    subject_present: bool
    posture_state: Literal["good", "poor", "unknown"]
    posture_confidence: float = Field(ge=0.0, le=1.0)
    detections: list[VisionDetection]
    processing: ProcessingDetails

    # ── New fields (all Optional for backward compat) ───────────
    auth: FaceAuthStatus | None = None                # Module A
    face_mesh: FaceMeshData | None = None             # Module C
    hands: HandTrackingData | None = None             # Module D
    pose: PoseData | None = None                      # Module E
    objects: YoloDetectionData | None = None          # Step 3
    behavior_events: list[BehaviorEventData] = Field(default_factory=list)  # Module F

    # Module G — owner tracking & iris gaze (None when face auth is disabled)
    owner_tracking: OwnerTrackingData | None = None

    # Phase 8 — server-rendered annotated frame (base64 JPEG, no data: prefix)
    # Set only when `render_overlay=True` is passed to the analyze endpoint.
    annotated_frame_base64: str | None = None
