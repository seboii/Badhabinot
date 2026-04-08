package com.badhabinot.backend.service.auth;

import com.badhabinot.backend.dto.auth.AuthenticatedUserResponse;
import com.badhabinot.backend.dto.auth.LoginRequest;
import com.badhabinot.backend.dto.auth.LogoutRequest;
import com.badhabinot.backend.dto.auth.RefreshTokenRequest;
import com.badhabinot.backend.dto.auth.RegisterRequest;
import com.badhabinot.backend.dto.auth.TokenResponse;
import com.badhabinot.backend.common.exception.auth.AuthenticationFailedException;
import com.badhabinot.backend.common.exception.auth.DuplicateEmailException;
import com.badhabinot.backend.common.exception.auth.InvalidRefreshTokenException;
import com.badhabinot.backend.model.auth.AccountStatus;
import com.badhabinot.backend.model.auth.AuthUser;
import com.badhabinot.backend.model.auth.RefreshToken;
import com.badhabinot.backend.model.auth.UserRole;
import com.badhabinot.backend.repository.auth.AuthUserRepository;
import com.badhabinot.backend.repository.auth.RefreshTokenRepository;
import com.badhabinot.backend.service.auth.RefreshTokenService;
import com.badhabinot.backend.service.auth.TokenIssuer;
import com.badhabinot.backend.service.user.UserContextService;
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
    private final UserContextService userContextService;

    public AuthApplicationService(
            AuthUserRepository authUserRepository,
            RefreshTokenRepository refreshTokenRepository,
            PasswordEncoder passwordEncoder,
            TokenIssuer tokenIssuer,
            RefreshTokenService refreshTokenService,
            UserContextService userContextService
    ) {
        this.authUserRepository = authUserRepository;
        this.refreshTokenRepository = refreshTokenRepository;
        this.passwordEncoder = passwordEncoder;
        this.tokenIssuer = tokenIssuer;
        this.refreshTokenService = refreshTokenService;
        this.userContextService = userContextService;
    }

    @Transactional(transactionManager = "authTransactionManager")
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

        userContextService.bootstrap(user.getId(), normalizedEmail, request.displayName(), request.timezone(), request.locale());
        return issueTokenResponse(user);
    }

    @Transactional(transactionManager = "authTransactionManager")
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

    @Transactional(transactionManager = "authTransactionManager")
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

    @Transactional(transactionManager = "authTransactionManager", readOnly = true)
    public AuthenticatedUserResponse me(Jwt jwt) {
        UUID userId = UUID.fromString(jwt.getSubject());
        String email = jwt.getClaimAsString("email");
        List<String> roles = jwt.getClaimAsStringList("roles");
        return new AuthenticatedUserResponse(userId, email, roles, jwt.getIssuedAt(), jwt.getExpiresAt());
    }

    @Transactional(transactionManager = "authTransactionManager")
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

