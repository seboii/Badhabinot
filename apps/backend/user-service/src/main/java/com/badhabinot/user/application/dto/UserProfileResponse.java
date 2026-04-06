package com.badhabinot.user.application.dto;

import java.time.Instant;
import java.util.UUID;

public record UserProfileResponse(
        UUID userId,
        String email,
        String displayName,
        String timezone,
        String locale,
        Instant updatedAt
) {
}

