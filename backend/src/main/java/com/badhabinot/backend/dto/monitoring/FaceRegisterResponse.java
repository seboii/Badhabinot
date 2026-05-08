package com.badhabinot.backend.dto.monitoring;

public record FaceRegisterResponse(
        String userId,
        boolean success,
        int framesEnrolled,
        String message
) {
}
