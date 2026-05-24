package com.badhabinot.backend.dto.monitoring;

import jakarta.validation.constraints.NotBlank;

public record FaceRegisterRequest(
        @NotBlank String imageBase64,
        String imageContentType,
        String poseHint
) {
}
