package com.badhabinot.backend.service.auth;

import java.time.Instant;
import java.util.UUID;

public interface IRefreshTokenService {
    GeneratedRefreshToken generate(UUID userId);
    String hash(String token);

    record GeneratedRefreshToken(String plainTextToken, String tokenHash, Instant expiresAt) {}
}
