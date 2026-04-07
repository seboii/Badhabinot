package com.badhabinot.monitoring.application.dto;

import java.time.Instant;

public record VisionAnalysisRequest(
        String requestId,
        String userId,
        String sessionId,
        String frameId,
        Instant capturedAt,
        String imageBase64,
        String imageContentType
) {
}
