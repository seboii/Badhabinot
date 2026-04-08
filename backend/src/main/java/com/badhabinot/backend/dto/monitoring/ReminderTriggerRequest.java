package com.badhabinot.backend.dto.monitoring;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import java.time.Instant;

public record ReminderTriggerRequest(
        @NotBlank @Size(max = 32) String reminderType,
        @Size(max = 255) String message,
        String sessionId,
        Instant occurredAt
) {
}


