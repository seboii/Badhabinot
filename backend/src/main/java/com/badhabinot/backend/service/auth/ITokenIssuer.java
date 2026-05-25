package com.badhabinot.backend.service.auth;

import com.badhabinot.backend.model.auth.AuthUser;
import java.time.Instant;

public interface ITokenIssuer {
    IssuedAccessToken issueAccessToken(AuthUser user);

    record IssuedAccessToken(String tokenValue, Instant expiresAt) {}
}
