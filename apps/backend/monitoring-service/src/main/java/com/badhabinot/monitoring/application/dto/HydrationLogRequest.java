package com.badhabinot.monitoring.application.dto;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import java.time.Instant;

public record HydrationLogRequest(
        @Min(50) @Max(2000) int amountMl,
        @NotBlank @Size(max = 32) String source,
        String sessionId,
        Instant occurredAt
) {
}

