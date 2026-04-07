package com.badhabinot.monitoring.application.dto;

import java.util.Map;

public record AiAnalysisResponse(
        String requestId,
        String behaviorType,
        double confidence,
        Map<String, Double> scores,
        String summary,
        String recommendation,
        java.util.List<String> groundedFacts,
        ModelDetails model
) {
    public record ModelDetails(
            String provider,
            String name,
            String mode
    ) {
    }
}
