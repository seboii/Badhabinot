package com.badhabinot.auth.application.dto;

import java.time.Instant;
import java.util.UUID;

public record TokenResponse(
        String accessToken,
        Instant accessTokenExpiresAt,
        String refreshToken,
        Instant refreshTokenExpiresAt,
        UserSummary user
) {

    public record UserSummary(
            UUID id,
            String email,
            String role
    ) {
    }
}

