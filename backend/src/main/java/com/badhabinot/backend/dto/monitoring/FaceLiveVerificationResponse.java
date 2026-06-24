package com.badhabinot.backend.dto.monitoring;

/** vision-service /verify-live yanıtı: kimlik + canlılık sonucu. */
public record FaceLiveVerificationResponse(
        boolean verified,
        boolean livenessPassed,
        String actionDetected,
        float confidence,
        String message
) {
}
