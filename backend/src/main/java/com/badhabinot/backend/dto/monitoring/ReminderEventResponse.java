package com.badhabinot.backend.dto.monitoring;

import java.time.Instant;
import java.util.Map;
import java.util.UUID;

public record ReminderEventResponse(
        UUID reminderId,
        String sessionId,
        String reminderType,
        String source,
        String severity,
        String message,
        String triggerReason,
        Map<String, Object> metadata,
        Instant occurredAt
) {
}

