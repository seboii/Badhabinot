package com.badhabinot.backend.dto.monitoring;

import java.util.List;

public record AiChatResponse(
        String conversationId,
        String answer,
        List<String> groundedFacts,
        List<String> followUpSuggestions,
        ModelDetails model
) {
    public record ModelDetails(
            String provider,
            String name,
            String mode
    ) {
    }
}

