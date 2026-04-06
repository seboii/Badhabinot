from app.core.config import settings
from app.schemas.inference import InferenceRequest, InferenceResponse


class InferenceService:
    def predict(self, request: InferenceRequest) -> InferenceResponse:
        threshold_map = {
            "LOW": 0.45,
            "MEDIUM": 0.60,
            "HIGH": 0.72,
        }
        threshold = threshold_map[request.settings.sensitivity]

        nail_score = min(
            1.0,
            request.metrics.hand_face_proximity_score * 0.6
            + request.metrics.center_edge_density * 0.25
            + request.metrics.edge_density * 0.15,
        )
        smoking_score = min(
            1.0,
            request.metrics.elongated_object_score * 0.65
            + request.metrics.center_edge_density * 0.2
            + request.metrics.edge_density * 0.15,
        )

        behavior_type = "none"
        confidence = max(nail_score, smoking_score)

        if nail_score >= threshold and nail_score >= smoking_score:
            behavior_type = "nail_biting"
            confidence = nail_score
        elif smoking_score >= threshold:
            behavior_type = "smoking"
            confidence = smoking_score

        return InferenceResponse(
            request_id=request.request_id,
            behavior_type=behavior_type,
            confidence=round(confidence, 4),
            scores={
                "nail_biting": round(nail_score, 4),
                "smoking": round(smoking_score, 4),
            },
            model={
                "name": settings.model_name,
                "version": settings.model_version,
                "mode": request.settings.model_mode.lower(),
            },
        )
