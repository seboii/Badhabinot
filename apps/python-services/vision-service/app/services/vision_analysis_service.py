from __future__ import annotations

import base64
import time
from math import hypot

import cv2
import numpy as np
from fastapi import HTTPException

from app.schemas.vision import (
    DetectionEvidence,
    ProcessingDetails,
    VisionAnalysisRequest,
    VisionAnalysisResponse,
    VisionDetection,
    VisionSignals,
)
from app.services.vision import SessionStateStore, VisionDetectors, VisionFeatureExtractor
from app.services.vision.session_state import SessionObservation


class VisionAnalysisService:
    def __init__(self) -> None:
        self.feature_extractor = VisionFeatureExtractor()
        self.detectors = VisionDetectors()
        self.session_state = SessionStateStore()

    async def analyze(self, request: VisionAnalysisRequest) -> VisionAnalysisResponse:
        started = time.perf_counter()
        image = self._decode_image(request.image_base64)
        features, _, _ = self.feature_extractor.extract(image)

        frame_diagonal = hypot(features.frame_width, features.frame_height)
        dominant_hand = features.dominant_hand_region
        temporal = self.session_state.update(
            request.session_id,
            SessionObservation(
                captured_at=request.captured_at,
                hand_centroid_x=None if dominant_hand is None else dominant_hand.center_x,
                hand_centroid_y=None if dominant_hand is None else dominant_hand.center_y,
                hand_face_proximity_score=features.hand_face_proximity_score,
                elongated_object_score=features.elongated_object_score,
                frame_diagonal=frame_diagonal,
            ),
        )

        posture_state, posture_confidence, detections, signals = self.detectors.detect(features, temporal)
        vision_latency_ms = int((time.perf_counter() - started) * 1000)

        response_detections = [
            VisionDetection(
                event_type=detection.event_type,
                confidence=detection.confidence,
                severity=detection.severity,
                recommendation_hint=detection.recommendation_hint,
                evidence=DetectionEvidence(
                    face_detected=bool(detection.evidence.get("face_detected", False)),
                    upper_body_detected=bool(detection.evidence.get("upper_body_detected", False)),
                    hand_count=int(detection.evidence.get("hand_count", 0)),
                    posture_alignment_score=self._optional_float(detection.evidence.get("posture_alignment_score")),
                    hand_face_proximity_score=self._optional_float(detection.evidence.get("hand_face_proximity_score")),
                    hand_motion_score=self._optional_float(detection.evidence.get("hand_motion_score")),
                    repetitive_motion_score=self._optional_float(detection.evidence.get("repetitive_motion_score")),
                    repeated_hand_to_face_score=self._optional_float(detection.evidence.get("repeated_hand_to_face_score")),
                    elongated_object_score=self._optional_float(detection.evidence.get("elongated_object_score")),
                ),
            )
            for detection in detections
        ]

        return VisionAnalysisResponse(
            request_id=request.request_id,
            subject_present=features.subject_present,
            posture_state=posture_state,
            posture_confidence=posture_confidence,
            detections=response_detections,
            signals=VisionSignals(
                brightness_mean=signals["brightness_mean"],
                edge_density=signals["edge_density"],
                center_edge_density=signals["center_edge_density"],
                posture_risk_score=signals["posture_risk_score"],
                hand_face_proximity_score=signals["hand_face_proximity_score"],
                elongated_object_score=signals["elongated_object_score"],
                focus_score=signals["focus_score"],
                posture_confidence=signals["posture_confidence"],
                posture_alignment_score=signals["posture_alignment_score"],
                hand_motion_score=signals["hand_motion_score"],
                repetitive_motion_score=signals["repetitive_motion_score"],
                smoking_gesture_score=signals["smoking_gesture_score"],
                face_size_ratio=signals["face_size_ratio"],
            ),
            processing=ProcessingDetails(
                frame_width=features.frame_width,
                frame_height=features.frame_height,
                brightness_mean=features.brightness_mean,
                edge_density=features.edge_density,
                focus_score=features.focus_score,
                vision_latency_ms=vision_latency_ms,
            ),
        )

    def _decode_image(self, image_base64: str) -> np.ndarray:
        try:
            normalized = image_base64.split(",", maxsplit=1)[-1]
            raw = base64.b64decode(normalized)
            array = np.frombuffer(raw, dtype=np.uint8)
            image = cv2.imdecode(array, cv2.IMREAD_COLOR)
        except Exception as exc:
            raise HTTPException(status_code=400, detail="invalid base64 image payload") from exc

        if image is None:
            raise HTTPException(status_code=400, detail="image payload could not be decoded")
        return image

    def _optional_float(self, value: object) -> float | None:
        if value is None:
            return None
        try:
            return round(float(value), 4)
        except (TypeError, ValueError):
            return None
