package com.badhabinot.backend.dto.monitoring;

import java.time.Instant;

public record SessionStopResponse(
        String sessionId,
        String status,
        Instant endedAt
) {
}


