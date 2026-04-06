package com.badhabinot.monitoring.application.dto;

import java.time.Instant;

public record SessionStartResponse(
        String sessionId,
        String status,
        Instant startedAt
) {
}

