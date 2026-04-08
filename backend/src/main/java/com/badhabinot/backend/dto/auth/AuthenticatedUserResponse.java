package com.badhabinot.backend.dto.auth;

import java.time.Instant;
import java.util.List;
import java.util.UUID;

public record AuthenticatedUserResponse(
        UUID userId,
        String email,
        List<String> roles,
        Instant issuedAt,
        Instant expiresAt
) {
}


