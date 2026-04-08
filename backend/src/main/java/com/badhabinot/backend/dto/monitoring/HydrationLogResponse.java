package com.badhabinot.backend.dto.monitoring;

import java.time.Instant;
import java.util.UUID;

public record HydrationLogResponse(
        UUID hydrationLogId,
        int amountMl,
        String source,
        Instant occurredAt
) {
}


