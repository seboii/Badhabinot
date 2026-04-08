package com.badhabinot.backend.dto.monitoring;

import java.time.Instant;
import java.util.Map;
import java.util.UUID;

public record ChatMessageResponse(
        UUID messageId,
        String conversationId,
        String role,
        String content,
        Instant createdAt,
        Map<String, Object> metadata
) {
}

