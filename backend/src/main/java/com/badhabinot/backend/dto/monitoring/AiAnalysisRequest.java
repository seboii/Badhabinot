package com.badhabinot.backend.dto.monitoring;

import java.time.Instant;
import java.util.List;

public record AiAnalysisRequest(
        String requestId,
        String userId,
        String sessionId,
        String frameId,
        Instant capturedAt,
        String timezone,
        String imageBase64,
        String imageContentType,
        AnalysisSettings settings,
        VisionContext vision
) {
    public record AnalysisSettings(
            String sensitivity,
            String modelMode,
            boolean remoteInferenceAccepted
    ) {
    }

    public record VisionContext(
            boolean subjectPresent,
            String postureState,
            int frameWidth,
            int frameHeight,
            List<VisionDetection> detections,
            VisionSignals signals
    ) {
    }

    public record VisionDetection(
            String eventType,
            double confidence,
            String severity,
            String recommendationHint,
            VisionEvidence evidence
    ) {
    }

    public record VisionEvidence(
            boolean faceDetected,
            boolean upperBodyDetected,
            int handCount,
            Double postureAlignmentScore,
            Double handFaceProximityScore,
            Double handMotionScore,
            Double repetitiveMotionScore,
            Double repeatedHandToFaceScore,
            Double elongatedObjectScore
    ) {
    }

    public record VisionSignals(
            double brightnessMean,
            double edgeDensity,
            double centerEdgeDensity,
            double postureRiskScore,
            double handFaceProximityScore,
            double elongatedObjectScore,
            double focusScore,
            double postureConfidence,
            double postureAlignmentScore,
            double handMotionScore,
            double repetitiveMotionScore,
            double smokingGestureScore,
            double faceSizeRatio
    ) {
    }
}

