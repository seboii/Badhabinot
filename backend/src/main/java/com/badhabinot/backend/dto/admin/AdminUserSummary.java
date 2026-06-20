package com.badhabinot.backend.dto.admin;

import java.time.Instant;
import java.util.UUID;

/** Admin kullanıcı listesi satırı. */
public record AdminUserSummary(
        UUID id,
        String email,
        String displayName,
        String role,
        String status,
        Instant createdAt,
        Instant lastLoginAt
) {
}
