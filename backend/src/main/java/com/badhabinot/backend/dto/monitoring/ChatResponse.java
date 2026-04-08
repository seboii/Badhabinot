package com.badhabinot.backend.dto.monitoring;

import java.util.List;
import java.util.UUID;

public record ChatResponse(
        String conversationId,
        UUID messageId,
        String answer,
        List<String> groundedFacts,
        List<String> followUpSuggestions,
        List<ChatMessageResponse> recentMessages,
        ModelDetails model
) {
    public record ModelDetails(
            String provider,
            String name,
            String mode
    ) {
    }
}

