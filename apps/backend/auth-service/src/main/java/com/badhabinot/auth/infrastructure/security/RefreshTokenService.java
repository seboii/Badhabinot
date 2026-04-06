package com.badhabinot.auth.infrastructure.security;

import com.badhabinot.auth.infrastructure.config.JwtProperties;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.Instant;
import java.util.Base64;
import java.util.HexFormat;
import java.util.UUID;
import org.springframework.stereotype.Component;

@Component
public class RefreshTokenService {

    private final JwtProperties jwtProperties;

    public RefreshTokenService(JwtProperties jwtProperties) {
        this.jwtProperties = jwtProperties;
    }

    public GeneratedRefreshToken generate(UUID userId) {
        String token = Base64.getUrlEncoder().withoutPadding()
                .encodeToString((userId + ":" + UUID.randomUUID() + ":" + Instant.now()).getBytes(StandardCharsets.UTF_8));
        Instant expiresAt = Instant.now().plus(jwtProperties.refreshTokenTtl());
        return new GeneratedRefreshToken(token, hash(token), expiresAt);
    }

    public String hash(String token) {
        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            byte[] hash = digest.digest(token.getBytes(StandardCharsets.UTF_8));
            return HexFormat.of().formatHex(hash);
        } catch (NoSuchAlgorithmException exception) {
            throw new IllegalStateException("SHA-256 must be available in the JDK", exception);
        }
    }

    public record GeneratedRefreshToken(
            String plainTextToken,
            String tokenHash,
            Instant expiresAt
    ) {
    }
}

