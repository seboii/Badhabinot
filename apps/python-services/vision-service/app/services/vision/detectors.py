from __future__ import annotations

from app.services.vision.models import DetectionResult, FrameFeatures, TemporalFeatures


class VisionDetectors:
    def detect(
        self,
        features: FrameFeatures,
        temporal: TemporalFeatures,
    ) -> tuple[str, float, list[DetectionResult], dict[str, float]]:
        posture_risk_score = max(features.posture_alignment_score, 0.15 if features.subject_present else 0.0)
        hand_movement_score = self._clamp(
            (temporal.hand_motion_score * 0.45)
            + (temporal.repetitive_motion_score * 0.35)
            + (features.hand_face_proximity_score * 0.20)
        )
        smoking_gesture_score = self._clamp(
            (temporal.repeated_hand_to_face_score * 0.45)
            + (features.elongated_object_score * 0.35)
            + (features.hand_face_proximity_score * 0.20)
        )

        detections: list[DetectionResult] = []

        posture_state = "unknown"
        posture_confidence = 0.0
        if features.subject_present:
            posture_state = "poor" if posture_risk_score >= 0.58 else "good"
            posture_confidence = self._clamp(max(posture_risk_score, 1.0 - posture_risk_score))

        if features.subject_present and posture_state == "poor":
            detections.append(
                DetectionResult(
                    event_type="poor_posture",
                    confidence=round(posture_risk_score, 4),
                    severity=self._severity(posture_risk_score),
                    recommendation_hint="Roll the shoulders back and bring the head above the spine.",
                    evidence={
                        "face_detected": features.face_region is not None,
                        "upper_body_detected": features.upper_body_region is not None,
                        "hand_count": len(features.hand_regions),
                        "posture_alignment_score": round(features.posture_alignment_score, 4),
                        "hand_face_proximity_score": round(features.hand_face_proximity_score, 4),
                    },
                )
            )

        if features.subject_present and hand_movement_score >= 0.48:
            detections.append(
                DetectionResult(
                    event_type="hand_movement_pattern",
                    confidence=round(hand_movement_score, 4),
                    severity=self._severity(hand_movement_score),
                    recommendation_hint="Pause briefly and rest the hands away from the face.",
                    evidence={
                        "face_detected": features.face_region is not None,
                        "hand_count": len(features.hand_regions),
                        "hand_motion_score": round(temporal.hand_motion_score, 4),
                        "repetitive_motion_score": round(temporal.repetitive_motion_score, 4),
                        "hand_face_proximity_score": round(features.hand_face_proximity_score, 4),
                    },
                )
            )

        if (
            features.subject_present
            and features.face_region is not None
            and smoking_gesture_score >= 0.55
            and features.hand_face_proximity_score >= 0.45
        ):
            detections.append(
                DetectionResult(
                    event_type="smoking_like_gesture",
                    confidence=round(smoking_gesture_score, 4),
                    severity=self._severity(smoking_gesture_score),
                    recommendation_hint="Treat this as a smoking-like cue and confirm with more frames before acting strongly.",
                    evidence={
                        "face_detected": True,
                        "hand_count": len(features.hand_regions),
                        "elongated_object_score": round(features.elongated_object_score, 4),
                        "repeated_hand_to_face_score": round(temporal.repeated_hand_to_face_score, 4),
                        "hand_face_proximity_score": round(features.hand_face_proximity_score, 4),
                    },
                )
            )

        signals = {
            "brightness_mean": features.brightness_mean,
            "edge_density": features.edge_density,
            "center_edge_density": features.center_edge_density,
            "posture_risk_score": round(posture_risk_score, 4),
            "hand_face_proximity_score": features.hand_face_proximity_score,
            "elongated_object_score": features.elongated_object_score,
            "focus_score": features.focus_score,
            "posture_confidence": round(posture_confidence, 4),
            "posture_alignment_score": round(features.posture_alignment_score, 4),
            "hand_motion_score": round(temporal.hand_motion_score, 4),
            "repetitive_motion_score": round(temporal.repetitive_motion_score, 4),
            "smoking_gesture_score": round(smoking_gesture_score, 4),
            "face_size_ratio": round(features.face_size_ratio, 4),
        }
        return posture_state, round(posture_confidence, 4), detections, signals

    def _severity(self, confidence: float) -> str:
        if confidence >= 0.8:
            return "high"
        if confidence >= 0.62:
            return "medium"
        return "low"

    def _clamp(self, value: float) -> float:
        return max(0.0, min(1.0, value))
