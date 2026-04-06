from datetime import datetime
from typing import Dict, Literal

from pydantic import BaseModel, ConfigDict, Field


class VisionSettings(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    sensitivity: Literal["LOW", "MEDIUM", "HIGH"]
    model_mode: Literal["LOCAL", "API"]
    remote_inference_accepted: bool


class VisionAnalysisRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    request_id: str
    user_id: str
    session_id: str
    frame_id: str
    captured_at: datetime
    image_base64: str
    image_content_type: str
    settings: VisionSettings


class ProcessingDetails(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    frame_width: int
    frame_height: int
    brightness_mean: float
    edge_density: float
    vision_latency_ms: int
    ai_latency_ms: int


class InferenceResult(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    behavior_type: str
    confidence: float
    scores: Dict[str, float]


class VisionAnalysisResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    request_id: str
    subject_present: bool
    posture_state: str
    inference: InferenceResult
    processing: ProcessingDetails
