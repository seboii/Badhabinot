package com.badhabinot.backend.service.auth.impl;

import com.badhabinot.backend.dto.auth.AuthenticatedUserResponse;
import com.badhabinot.backend.dto.auth.ChangePasswordDto;
import com.badhabinot.backend.dto.auth.FaceLoginRequest;
import com.badhabinot.backend.dto.auth.LoginRequest;
import com.badhabinot.backend.dto.auth.LogoutRequest;
import com.badhabinot.backend.dto.auth.RefreshTokenRequest;
import com.badhabinot.backend.dto.auth.RegisterRequest;
import com.badhabinot.backend.dto.auth.TokenResponse;
import com.badhabinot.backend.common.exception.auth.AuthenticationFailedException;
import com.badhabinot.backend.common.exception.auth.DuplicateEmailException;
import com.badhabinot.backend.common.exception.auth.FaceMismatchException;
import com.badhabinot.backend.common.exception.auth.FaceNotRegisteredException;
import com.badhabinot.backend.common.exception.auth.InvalidRefreshTokenException;
import com.badhabinot.backend.integration.python.VisionServiceClient;
import com.badhabinot.backend.model.auth.AccountStatus;
import com.badhabinot.backend.model.auth.AuthUser;
import com.badhabinot.backend.model.auth.RefreshToken;
import com.badhabinot.backend.model.auth.UserRole;
import com.badhabinot.backend.repository.auth.AuthUserRepository;
import com.badhabinot.backend.repository.auth.RefreshTokenRepository;
import com.badhabinot.backend.infrastructure.redis.LoginAttemptService;
import com.badhabinot.backend.service.auth.IAuthApplicationService;
import com.badhabinot.backend.service.auth.IRefreshTokenService;
import com.badhabinot.backend.service.auth.ITokenIssuer;
import com.badhabinot.backend.service.user.IUserContextService;
import java.time.Instant;
import java.util.List;
import java.util.Locale;
import java.util.UUID;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.oauth2.jwt.Jwt;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class AuthApplicationServiceImpl implements IAuthApplicationService {

    private final AuthUserRepository authUserRepository;
    private final RefreshTokenRepository refreshTokenRepository;
    private final PasswordEncoder passwordEncoder;
    private final ITokenIssuer tokenIssuer;
    private final IRefreshTokenService refreshTokenService;
    private final IUserContextService userContextService;
    private final LoginAttemptService loginAttemptService;
    private final VisionServiceClient visionServiceClient;

    public AuthApplicationServiceImpl(
            AuthUserRepository authUserRepository,
            RefreshTokenRepository refreshTokenRepository,
            PasswordEncoder passwordEncoder,
            ITokenIssuer tokenIssuer,
            IRefreshTokenService refreshTokenService,
            IUserContextService userContextService,
            LoginAttemptService loginAttemptService,
            VisionServiceClient visionServiceClient
    ) {
        this.authUserRepository = authUserRepository;
        this.refreshTokenRepository = refreshTokenRepository;
        this.passwordEncoder = passwordEncoder;
        this.tokenIssuer = tokenIssuer;
        this.refreshTokenService = refreshTokenService;
        this.userContextService = userContextService;
        this.loginAttemptService = loginAttemptService;
        this.visionServiceClient = visionServiceClient;
    }


    @Transactional(transactionManager = "authTransactionManager")
    @Override
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
    @Override
    public TokenResponse login(LoginRequest request) {
        String normalizedEmail = normalizeEmail(request.email());
        loginAttemptService.checkNotBlocked(normalizedEmail);

        AuthUser user = authUserRepository.findByEmail(normalizedEmail).orElse(null);
        if (user == null) {
            loginAttemptService.recordFailure(normalizedEmail);
            throw new AuthenticationFailedException("Invalid email or password");
        }
        if (!passwordEncoder.matches(request.password(), user.getPasswordHash())) {
            loginAttemptService.recordFailure(normalizedEmail);
            throw new AuthenticationFailedException("Invalid email or password");
        }
        if (user.getStatus() != AccountStatus.ACTIVE) {
            loginAttemptService.recordFailure(normalizedEmail);
            throw new AuthenticationFailedException("Account is not active");
        }

        loginAttemptService.resetAttempts(normalizedEmail);
        user.recordLogin();
        authUserRepository.save(user);
        return issueTokenResponse(user);
    }


    @Transactional(transactionManager = "authTransactionManager")
    @Override
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
    @Override
    public AuthenticatedUserResponse me(Jwt jwt) {
        UUID userId = UUID.fromString(jwt.getSubject());
        String email = jwt.getClaimAsString("email");
        List<String> roles = jwt.getClaimAsStringList("roles");
        return new AuthenticatedUserResponse(userId, email, roles, jwt.getIssuedAt(), jwt.getExpiresAt());
    }


    @Transactional(transactionManager = "authTransactionManager")
    @Override
    public void logout(Jwt jwt, LogoutRequest request) {
        refreshTokenRepository.findByTokenHash(refreshTokenService.hash(request.refreshToken()))
                .filter(token -> token.getUserId().equals(UUID.fromString(jwt.getSubject())))
                .ifPresent(token -> token.revoke(Instant.now()));
    }


    @Transactional(transactionManager = "authTransactionManager")
    @Override
    public TokenResponse loginWithFace(FaceLoginRequest request) {
        String normalizedEmail = normalizeEmail(request.email());
        loginAttemptService.checkNotBlocked(normalizedEmail);

        AuthUser user = authUserRepository.findByEmail(normalizedEmail).orElse(null);
        if (user == null) {
            loginAttemptService.recordFailure(normalizedEmail);
            throw new AuthenticationFailedException("Invalid email or password");
        }
        if (user.getStatus() != AccountStatus.ACTIVE) {
            loginAttemptService.recordFailure(normalizedEmail);
            throw new AuthenticationFailedException("Account is not active");
        }

        var faceStatus = visionServiceClient.faceStatus(user.getId().toString());
        if (!faceStatus.success()) {
            throw new FaceNotRegisteredException("No face profile registered for this account. Please sign in with your password.");
        }

        var verification = visionServiceClient.verifyFace(
                user.getId().toString(),
                request.faceImageBase64(),
                request.imageContentType()
        );
        if (!verification.verified()) {
            loginAttemptService.recordFailure(normalizedEmail);
            throw new FaceMismatchException("Face verification failed. Please try again or sign in with your password.");
        }

        loginAttemptService.resetAttempts(normalizedEmail);
        user.recordLogin();
        authUserRepository.save(user);
        return issueTokenResponse(user);
    }


    @Transactional(transactionManager = "authTransactionManager")
    @Override
    public void changePassword(UUID userId, ChangePasswordDto dto) {
        AuthUser user = authUserRepository.findById(userId)
                .orElseThrow(() -> new AuthenticationFailedException("User not found"));

        if (!passwordEncoder.matches(dto.currentPassword(), user.getPasswordHash())) {
            throw new IllegalArgumentException("Mevcut şifre hatalı");
        }

        user.updatePassword(passwordEncoder.encode(dto.newPassword()));
        authUserRepository.save(user);
        refreshTokenRepository.deleteByUserId(userId);
    }

    private TokenResponse issueTokenResponse(AuthUser user) {
        ITokenIssuer.IssuedAccessToken accessToken = tokenIssuer.issueAccessToken(user);
        IRefreshTokenService.GeneratedRefreshToken refresh = refreshTokenService.generate(user.getId());

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
