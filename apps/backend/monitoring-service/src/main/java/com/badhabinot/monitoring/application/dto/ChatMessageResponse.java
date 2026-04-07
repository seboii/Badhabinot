package com.badhabinot.monitoring.application.dto;

import java.time.Instant;
import java.util.UUID;

public record ChatMessageResponse(
        UUID messageId,
        String conversationId,
        String role,
        String content,
        Instant createdAt
) {
}
