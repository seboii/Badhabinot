package com.badhabinot.monitoring.application.dto;

import java.time.Instant;

public record SessionStopResponse(
        String sessionId,
        String status,
        Instant endedAt
) {
}

