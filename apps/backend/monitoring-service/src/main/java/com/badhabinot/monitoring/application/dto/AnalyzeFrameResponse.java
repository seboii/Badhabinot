package com.badhabinot.monitoring.application.dto;

import java.time.Instant;
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
        Map<String, Object> processing
) {
}

