package com.badhabinot.backend.dto.auth;

import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;

public record FaceLoginRequest(
        @Email @NotBlank String email,
        @NotBlank String faceImageBase64,
        @NotBlank String imageContentType
) {
}
