package com.badhabinot.backend.dto.monitoring;

import java.time.Instant;

public record SessionStartResponse(
        String sessionId,
        String status,
        Instant startedAt
) {
}


