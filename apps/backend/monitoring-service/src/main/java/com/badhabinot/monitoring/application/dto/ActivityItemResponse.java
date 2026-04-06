package com.badhabinot.monitoring.application.dto;

import java.time.Instant;
import java.util.UUID;

public record ActivityItemResponse(
        UUID id,
        String activityType,
        String category,
        String title,
        String message,
        Double confidence,
        Instant occurredAt
) {
}

