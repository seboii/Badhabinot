from datetime import datetime
from typing import Dict, Literal

from pydantic import BaseModel, ConfigDict


class InferenceSettings(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    sensitivity: Literal["LOW", "MEDIUM", "HIGH"]
    model_mode: Literal["LOCAL", "API"]
    remote_inference_accepted: bool


class VisionMetrics(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    brightness_mean: float
    edge_density: float
    center_edge_density: float
    posture_risk_score: float
    hand_face_proximity_score: float
    elongated_object_score: float


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
    behavior_type: str
    confidence: float
    scores: Dict[str, float]
    model: Dict[str, str]
