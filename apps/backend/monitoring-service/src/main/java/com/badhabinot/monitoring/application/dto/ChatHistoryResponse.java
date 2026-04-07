package com.badhabinot.monitoring.application.dto;

import java.util.List;

public record ChatHistoryResponse(
        String conversationId,
        List<ChatMessageResponse> recentMessages
) {
}
