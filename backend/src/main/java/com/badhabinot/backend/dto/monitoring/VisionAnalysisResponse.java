package com.badhabinot.backend.dto.monitoring;

import java.util.List;

public record VisionAnalysisResponse(
        String requestId,
        boolean subjectPresent,
        String postureState,
        double postureConfidence,
        List<Detection> detections,
        Signals signals,
        Processing processing,
        // Phase 8 — new optional fields (null when not requested or deps unavailable)
        String annotatedFrameBase64,
        List<VisionBehaviorEvent> behaviorEvents,
        // Module A — face authentication result (null when no profile registered)
        AuthStatus auth
) {
    public record Detection(
            String eventType,
            double confidence,
            String severity,
            String recommendationHint,
            Evidence evidence
    ) {
    }

    public record Evidence(
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

    public record Signals(
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

    public record Processing(
            int frameWidth,
            int frameHeight,
            double brightnessMean,
            double edgeDensity,
            double focusScore,
            long visionLatencyMs
    ) {
    }

    /** Mirrors the Python BehaviorEventData schema. */
    public record VisionBehaviorEvent(
            String eventType,
            String severity,
            double confidence,
            String detail
    ) {
    }

    /** Mirrors the Python FaceAuthStatus schema (Module A). */
    public record AuthStatus(
            boolean enabled,
            boolean authenticated,
            double confidence,
            int framesEnrolled,
            String error
    ) {
    }
}
