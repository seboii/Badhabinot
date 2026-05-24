package com.badhabinot.backend.dto.monitoring;

public record FaceVerificationResponse(
        boolean verified,
        float confidence,
        String message
) {
}
