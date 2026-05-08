package com.badhabinot.backend.dto.monitoring;

import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.UUID;

public record AnalyzeFrameResponse(
        UUID analysisId,
        String sessionId,
        String frameId,
        boolean subjectPresent,
        String postureState,
        String behaviorType,
        double confidence,
        Instant processedAt,
        String summary,
        String recommendation,
        List<BehaviorEventResponse> events,
        List<ReminderEventResponse> generatedReminders,
        ProcessingDetails processing,
        ModelDetails model,
        // Phase 8 — vision overlay pass-through fields (null when not requested)
        String annotatedFrameBase64,
        List<VisionBehaviorEventDetail> visionBehaviorEvents,
        // Module A — face authentication result (null when no profile registered)
        FaceAuthDetail faceAuth
) {
    public record ProcessingDetails(
            int frameWidth,
            int frameHeight,
            double brightnessMean,
            double edgeDensity,
            double focusScore,
            double postureRiskScore,
            long visionLatencyMs,
            long aiLatencyMs,
            Map<String, Double> scores
    ) {
    }

    public record ModelDetails(
            String provider,
            String name,
            String mode
    ) {
    }

    /** Mirrors VisionAnalysisResponse.VisionBehaviorEvent for frontend consumption. */
    public record VisionBehaviorEventDetail(
            String eventType,
            String severity,
            double confidence,
            String detail
    ) {
    }

    /** Face authentication result passed through from vision-service Module A. */
    public record FaceAuthDetail(
            boolean enabled,
            boolean authenticated,
            double confidence,
            int framesEnrolled
    ) {
    }
}
