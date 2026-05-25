package com.badhabinot.backend.service.auth.impl;

import com.badhabinot.backend.config.JwtProperties;
import com.badhabinot.backend.service.auth.IRefreshTokenService;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.Instant;
import java.util.Base64;
import java.util.HexFormat;
import java.util.UUID;
import org.springframework.stereotype.Component;

@Component
public class RefreshTokenServiceImpl implements IRefreshTokenService {

    private final JwtProperties jwtProperties;

    public RefreshTokenServiceImpl(JwtProperties jwtProperties) {
        this.jwtProperties = jwtProperties;
    }

    @Override
    public IRefreshTokenService.GeneratedRefreshToken generate(UUID userId) {
        String token = Base64.getUrlEncoder().withoutPadding()
                .encodeToString((userId + ":" + UUID.randomUUID() + ":" + Instant.now()).getBytes(StandardCharsets.UTF_8));
        Instant expiresAt = Instant.now().plus(jwtProperties.refreshTokenTtl());
        return new IRefreshTokenService.GeneratedRefreshToken(token, hash(token), expiresAt);
    }

    @Override
    public String hash(String token) {
        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            byte[] hash = digest.digest(token.getBytes(StandardCharsets.UTF_8));
            return HexFormat.of().formatHex(hash);
        } catch (NoSuchAlgorithmException exception) {
            throw new IllegalStateException("SHA-256 must be available in the JDK", exception);
        }
    }

}


