package com.badhabinot.monitoring.application.dto;

import java.time.Instant;
import java.util.Map;
import java.util.UUID;

public record AnalysisJobStatusResponse(
        UUID analysisId,
        String status,
        String sessionId,
        String frameId,
        Boolean subjectPresent,
        String postureState,
        String behaviorType,
        Double confidence,
        Instant createdAt,
        Instant updatedAt,
        Instant expiresAt,
        Map<String, Object> processing,
        String failureCode,
        String failureMessage
) {
}
