package com.badhabinot.backend.dto.monitoring;

import java.util.List;

public record ChatHistoryResponse(
        String conversationId,
        List<ChatMessageResponse> recentMessages
) {
}

