package com.badhabinot.monitoring.application.dto;

import java.util.Map;

public record VisionAnalysisResponse(
        String requestId,
        boolean subjectPresent,
        String postureState,
        Inference inference,
        Processing processing
) {
    public record Inference(
            String behaviorType,
            double confidence,
            Map<String, Double> scores
    ) {
    }

    public record Processing(
            int frameWidth,
            int frameHeight,
            double brightnessMean,
            double edgeDensity,
            long visionLatencyMs,
            long aiLatencyMs
    ) {
    }
}

