import base64
import time

import cv2
import numpy as np
from fastapi import HTTPException

from app.clients.ai_client import AiClient
from app.schemas.inference import InferenceRequest, InferenceSettings, VisionMetrics
from app.schemas.vision import (
    InferenceResult,
    ProcessingDetails,
    VisionAnalysisRequest,
    VisionAnalysisResponse,
)


class VisionAnalysisService:
    def __init__(self) -> None:
        self.ai_client = AiClient()

    async def analyze(self, request: VisionAnalysisRequest) -> VisionAnalysisResponse:
        started = time.perf_counter()
        image = self._decode_image(request.image_base64)

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        height, width = gray.shape
        edges = cv2.Canny(gray, 50, 150)

        brightness_mean = float(gray.mean())
        edge_density = float(edges.mean() / 255.0)

        center_crop = edges[height // 4 : (3 * height) // 4, width // 4 : (3 * width) // 4]
        center_edge_density = float(center_crop.mean() / 255.0) if center_crop.size else 0.0

        upper = gray[: height // 2, :]
        lower = gray[height // 2 :, :]
        upper_std = float(upper.std()) if upper.size else 0.0
        lower_std = float(lower.std()) if lower.size else 0.0

        posture_risk_score = self._clamp(abs(upper_std - lower_std) / 128.0)
        hand_face_proximity_score = self._clamp((center_edge_density * 0.7) + (brightness_mean / 255.0 * 0.3))
        elongated_object_score = self._clamp((edge_density * 0.8) + (lower_std / 255.0 * 0.2))
        subject_present = width >= 64 and height >= 64 and brightness_mean > 5.0

        if not subject_present:
            vision_latency_ms = int((time.perf_counter() - started) * 1000)
            return VisionAnalysisResponse(
                request_id=request.request_id,
                subject_present=False,
                posture_state="unknown",
                inference=InferenceResult(
                    behavior_type="none",
                    confidence=0.0,
                    scores={"nail_biting": 0.0, "smoking": 0.0},
                ),
                processing=ProcessingDetails(
                    frame_width=width,
                    frame_height=height,
                    brightness_mean=round(brightness_mean, 4),
                    edge_density=round(edge_density, 4),
                    vision_latency_ms=vision_latency_ms,
                    ai_latency_ms=0,
                ),
            )

        inference_request = InferenceRequest(
            request_id=request.request_id,
            user_id=request.user_id,
            session_id=request.session_id,
            frame_id=request.frame_id,
            captured_at=request.captured_at,
            metrics=VisionMetrics(
                brightness_mean=brightness_mean,
                edge_density=edge_density,
                center_edge_density=center_edge_density,
                posture_risk_score=posture_risk_score,
                hand_face_proximity_score=hand_face_proximity_score,
                elongated_object_score=elongated_object_score,
            ),
            settings=InferenceSettings(
                sensitivity=request.settings.sensitivity,
                model_mode=request.settings.model_mode,
                remote_inference_accepted=request.settings.remote_inference_accepted,
            ),
        )

        inference_response, ai_latency_ms = await self.ai_client.predict(inference_request)
        vision_latency_ms = int((time.perf_counter() - started) * 1000)

        posture_state = "poor" if posture_risk_score >= 0.6 else "good"

        return VisionAnalysisResponse(
            request_id=request.request_id,
            subject_present=subject_present,
            posture_state=posture_state,
            inference=InferenceResult(
                behavior_type=inference_response.behavior_type,
                confidence=inference_response.confidence,
                scores=inference_response.scores,
            ),
            processing=ProcessingDetails(
                frame_width=width,
                frame_height=height,
                brightness_mean=round(brightness_mean, 4),
                edge_density=round(edge_density, 4),
                vision_latency_ms=vision_latency_ms,
                ai_latency_ms=ai_latency_ms,
            ),
        )

    def _decode_image(self, image_base64: str) -> np.ndarray:
        try:
            raw = base64.b64decode(image_base64)
            array = np.frombuffer(raw, dtype=np.uint8)
            image = cv2.imdecode(array, cv2.IMREAD_COLOR)
        except Exception as exc:
            raise HTTPException(status_code=400, detail="invalid base64 image payload") from exc

        if image is None:
            raise HTTPException(status_code=400, detail="image payload could not be decoded")
        return image

    def _clamp(self, value: float) -> float:
        return max(0.0, min(1.0, value))
