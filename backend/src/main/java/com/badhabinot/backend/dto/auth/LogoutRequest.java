package com.badhabinot.backend.dto.auth;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public record LogoutRequest(
        @NotBlank @Size(min = 32, max = 512) String refreshToken
) {
}

