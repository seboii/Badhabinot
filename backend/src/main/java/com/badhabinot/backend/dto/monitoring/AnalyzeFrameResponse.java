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
        ModelDetails model
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
}

