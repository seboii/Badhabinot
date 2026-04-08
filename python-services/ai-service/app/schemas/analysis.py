from datetime import datetime
from typing import Dict, Literal

from pydantic import BaseModel, ConfigDict, Field


AllowedBehavior = Literal["none", "hand_movement_pattern", "smoking_like_gesture"]


class AnalysisSettings(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    sensitivity: Literal["LOW", "MEDIUM", "HIGH"]
    model_mode: Literal["API"] = "API"
    remote_inference_accepted: bool


class VisionEvidence(BaseModel):
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
    evidence: VisionEvidence


class VisionSignals(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    brightness_mean: float = Field(ge=0.0, le=255.0)
    edge_density: float = Field(ge=0.0, le=1.0)
    center_edge_density: float = Field(ge=0.0, le=1.0)
    posture_risk_score: float = Field(ge=0.0, le=1.0)
    hand_face_proximity_score: float = Field(ge=0.0, le=1.0)
    elongated_object_score: float = Field(ge=0.0, le=1.0)
    focus_score: float = Field(ge=0.0)
    posture_confidence: float = Field(ge=0.0, le=1.0)
    posture_alignment_score: float = Field(ge=0.0, le=1.0)
    hand_motion_score: float = Field(ge=0.0, le=1.0)
    repetitive_motion_score: float = Field(ge=0.0, le=1.0)
    smoking_gesture_score: float = Field(ge=0.0, le=1.0)
    face_size_ratio: float = Field(ge=0.0, le=1.0)


class VisionContext(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    subject_present: bool
    posture_state: Literal["good", "poor", "unknown"]
    frame_width: int = Field(ge=1)
    frame_height: int = Field(ge=1)
    detections: list[VisionDetection]
    signals: VisionSignals


class AnalysisRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    request_id: str
    user_id: str
    session_id: str
    frame_id: str
    captured_at: datetime
    timezone: str | None = None
    image_base64: str | None = None
    image_content_type: str | None = None
    settings: AnalysisSettings
    vision: VisionContext


class ModelDescriptor(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    provider: str
    name: str
    mode: Literal["external_api", "mock", "not_invoked"]


class AnalysisResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    request_id: str
    behavior_type: AllowedBehavior
    confidence: float = Field(ge=0.0, le=1.0)
    scores: Dict[str, float]
    summary: str
    recommendation: str
    grounded_facts: list[str]
    model: ModelDescriptor
