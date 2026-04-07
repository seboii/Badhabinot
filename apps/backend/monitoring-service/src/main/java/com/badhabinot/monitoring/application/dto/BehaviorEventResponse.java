package com.badhabinot.monitoring.application.dto;

import java.time.Instant;
import java.util.Map;
import java.util.UUID;

public record BehaviorEventResponse(
        UUID eventId,
        UUID analysisId,
        String sessionId,
        String eventType,
        String detector,
        double confidence,
        String severity,
        String interpretation,
        String recommendationHint,
        Map<String, Object> evidence,
        Instant occurredAt
) {
}
