package com.badhabinot.auth.application.service;

import com.badhabinot.auth.application.dto.AuthenticatedUserResponse;
import com.badhabinot.auth.application.dto.LoginRequest;
import com.badhabinot.auth.application.dto.LogoutRequest;
import com.badhabinot.auth.application.dto.RefreshTokenRequest;
import com.badhabinot.auth.application.dto.RegisterRequest;
import com.badhabinot.auth.application.dto.TokenResponse;
import com.badhabinot.auth.application.exception.AuthenticationFailedException;
import com.badhabinot.auth.application.exception.DuplicateEmailException;
import com.badhabinot.auth.application.exception.InvalidRefreshTokenException;
import com.badhabinot.auth.domain.model.AccountStatus;
import com.badhabinot.auth.domain.model.AuthUser;
import com.badhabinot.auth.domain.model.RefreshToken;
import com.badhabinot.auth.domain.model.UserRole;
import com.badhabinot.auth.domain.repository.AuthUserRepository;
import com.badhabinot.auth.domain.repository.RefreshTokenRepository;
import com.badhabinot.auth.infrastructure.client.UserProvisioningClient;
import com.badhabinot.auth.infrastructure.security.RefreshTokenService;
import com.badhabinot.auth.infrastructure.security.TokenIssuer;
import java.time.Instant;
import java.util.List;
import java.util.Locale;
import java.util.UUID;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.oauth2.jwt.Jwt;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class AuthApplicationService {

    private final AuthUserRepository authUserRepository;
    private final RefreshTokenRepository refreshTokenRepository;
    private final PasswordEncoder passwordEncoder;
    private final TokenIssuer tokenIssuer;
    private final RefreshTokenService refreshTokenService;
    private final UserProvisioningClient userProvisioningClient;

    public AuthApplicationService(
            AuthUserRepository authUserRepository,
            RefreshTokenRepository refreshTokenRepository,
            PasswordEncoder passwordEncoder,
            TokenIssuer tokenIssuer,
            RefreshTokenService refreshTokenService,
            UserProvisioningClient userProvisioningClient
    ) {
        this.authUserRepository = authUserRepository;
        this.refreshTokenRepository = refreshTokenRepository;
        this.passwordEncoder = passwordEncoder;
        this.tokenIssuer = tokenIssuer;
        this.refreshTokenService = refreshTokenService;
        this.userProvisioningClient = userProvisioningClient;
    }

    @Transactional
    public TokenResponse register(RegisterRequest request) {
        String normalizedEmail = normalizeEmail(request.email());
        if (authUserRepository.existsByEmail(normalizedEmail)) {
            throw new DuplicateEmailException("An account already exists for that email address");
        }

        AuthUser user = AuthUser.create(
                normalizedEmail,
                passwordEncoder.encode(request.password()),
                UserRole.USER,
                AccountStatus.ACTIVE
        );
        authUserRepository.save(user);

        userProvisioningClient.bootstrapUser(user.getId(), normalizedEmail, request.displayName(), request.timezone(), request.locale());
        return issueTokenResponse(user);
    }

    @Transactional
    public TokenResponse login(LoginRequest request) {
        AuthUser user = authUserRepository.findByEmail(normalizeEmail(request.email()))
                .orElseThrow(() -> new AuthenticationFailedException("Invalid email or password"));
        if (!passwordEncoder.matches(request.password(), user.getPasswordHash())) {
            throw new AuthenticationFailedException("Invalid email or password");
        }
        if (user.getStatus() != AccountStatus.ACTIVE) {
            throw new AuthenticationFailedException("Account is not active");
        }
        return issueTokenResponse(user);
    }

    @Transactional
    public TokenResponse refresh(RefreshTokenRequest request) {
        RefreshToken storedToken = refreshTokenRepository.findByTokenHash(refreshTokenService.hash(request.refreshToken()))
                .orElseThrow(() -> new InvalidRefreshTokenException("Refresh token is invalid"));

        if (!storedToken.isUsable()) {
            throw new InvalidRefreshTokenException("Refresh token is expired or revoked");
        }

        AuthUser user = authUserRepository.findById(storedToken.getUserId())
                .orElseThrow(() -> new InvalidRefreshTokenException("User no longer exists for refresh token"));

        storedToken.revoke(Instant.now());
        return issueTokenResponse(user);
    }

    @Transactional(readOnly = true)
    public AuthenticatedUserResponse me(Jwt jwt) {
        UUID userId = UUID.fromString(jwt.getSubject());
        String email = jwt.getClaimAsString("email");
        List<String> roles = jwt.getClaimAsStringList("roles");
        return new AuthenticatedUserResponse(userId, email, roles, jwt.getIssuedAt(), jwt.getExpiresAt());
    }

    @Transactional
    public void logout(Jwt jwt, LogoutRequest request) {
        refreshTokenRepository.findByTokenHash(refreshTokenService.hash(request.refreshToken()))
                .filter(token -> token.getUserId().equals(UUID.fromString(jwt.getSubject())))
                .ifPresent(token -> token.revoke(Instant.now()));
    }

    private TokenResponse issueTokenResponse(AuthUser user) {
        TokenIssuer.IssuedAccessToken accessToken = tokenIssuer.issueAccessToken(user);
        RefreshTokenService.GeneratedRefreshToken refresh = refreshTokenService.generate(user.getId());

        refreshTokenRepository.save(RefreshToken.issue(
                user.getId(),
                refresh.tokenHash(),
                refresh.expiresAt()
        ));

        return new TokenResponse(
                accessToken.tokenValue(),
                accessToken.expiresAt(),
                refresh.plainTextToken(),
                refresh.expiresAt(),
                new TokenResponse.UserSummary(user.getId(), user.getEmail(), user.getRole().name())
        );
    }

    private String normalizeEmail(String email) {
        return email.trim().toLowerCase(Locale.ROOT);
    }
}
