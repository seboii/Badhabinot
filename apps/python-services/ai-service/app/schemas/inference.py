from datetime import datetime
from typing import Dict, Literal

from pydantic import BaseModel, ConfigDict, Field


class InferenceSettings(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    sensitivity: Literal["LOW", "MEDIUM", "HIGH"]
    model_mode: Literal["LOCAL", "API"]
    remote_inference_accepted: bool


class VisionMetrics(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    brightness_mean: float = Field(ge=0.0, le=255.0)
    edge_density: float = Field(ge=0.0, le=1.0)
    center_edge_density: float = Field(ge=0.0, le=1.0)
    posture_risk_score: float = Field(ge=0.0, le=1.0)
    hand_face_proximity_score: float = Field(ge=0.0, le=1.0)
    elongated_object_score: float = Field(ge=0.0, le=1.0)


class InferenceRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    request_id: str
    user_id: str
    session_id: str
    frame_id: str
    captured_at: datetime
    metrics: VisionMetrics
    settings: InferenceSettings


class InferenceResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    request_id: str
    behavior_type: Literal["none", "nail_biting", "smoking"]
    confidence: float = Field(ge=0.0, le=1.0)
    scores: Dict[str, float]
    model: Dict[str, str]
