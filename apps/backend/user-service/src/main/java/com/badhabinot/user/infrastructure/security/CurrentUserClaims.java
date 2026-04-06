package com.badhabinot.user.infrastructure.security;

import java.util.UUID;
import org.springframework.security.oauth2.jwt.Jwt;

public record CurrentUserClaims(
        UUID userId,
        String email
) {

    public static CurrentUserClaims from(Jwt jwt) {
        return new CurrentUserClaims(UUID.fromString(jwt.getSubject()), jwt.getClaimAsString("email"));
    }
}
