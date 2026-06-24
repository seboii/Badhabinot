package com.badhabinot.backend.service.auth;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.verifyNoInteractions;
import static org.mockito.Mockito.when;

import com.badhabinot.backend.dto.auth.FaceLoginRequest;
import com.badhabinot.backend.dto.auth.LoginRequest;
import com.badhabinot.backend.dto.auth.RefreshTokenRequest;
import com.badhabinot.backend.dto.auth.RegisterRequest;
import com.badhabinot.backend.common.exception.auth.AuthenticationFailedException;
import com.badhabinot.backend.common.exception.auth.DuplicateEmailException;
import com.badhabinot.backend.common.exception.auth.FaceMismatchException;
import com.badhabinot.backend.common.exception.auth.FaceNotRegisteredException;
import com.badhabinot.backend.common.exception.auth.InvalidRefreshTokenException;
import com.badhabinot.backend.dto.monitoring.FaceRegisterResponse;
import com.badhabinot.backend.dto.monitoring.FaceVerificationResponse;
import com.badhabinot.backend.integration.python.VisionServiceClient;
import com.badhabinot.backend.model.auth.AccountStatus;
import com.badhabinot.backend.model.auth.AuthUser;
import com.badhabinot.backend.model.auth.RefreshToken;
import com.badhabinot.backend.model.auth.UserRole;
import com.badhabinot.backend.repository.auth.AuthUserRepository;
import com.badhabinot.backend.repository.auth.RefreshTokenRepository;
import com.badhabinot.backend.infrastructure.redis.LoginAttemptService;
import com.badhabinot.backend.service.auth.impl.AuthApplicationServiceImpl;
import com.badhabinot.backend.service.user.IUserContextService;
import java.time.Instant;
import java.util.Optional;
import java.util.UUID;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.security.crypto.password.PasswordEncoder;

@ExtendWith(MockitoExtension.class)
class AuthApplicationServiceTest {

    @Mock
    private AuthUserRepository authUserRepository;

    @Mock
    private RefreshTokenRepository refreshTokenRepository;

    @Mock
    private PasswordEncoder passwordEncoder;

    @Mock
    private ITokenIssuer tokenIssuer;

    @Mock
    private IRefreshTokenService refreshTokenService;

    @Mock
    private IUserContextService userContextService;

    @Mock
    private LoginAttemptService loginAttemptService;

    @Mock
    private VisionServiceClient visionServiceClient;

    @InjectMocks
    private AuthApplicationServiceImpl AuthApplicationServiceImpl;

    @Test
    void registerNormalizesEmailAndBootstrapsUserContext() {
        when(authUserRepository.existsByEmail("alice@example.com")).thenReturn(false);
        when(passwordEncoder.encode("secret-123")).thenReturn("encoded-password");
        when(authUserRepository.save(any())).thenAnswer(invocation -> invocation.getArgument(0));

        var response = AuthApplicationServiceImpl.register(new RegisterRequest(
                " Alice@Example.com ",
                "secret-123",
                "Alice",
                "Europe/Istanbul",
                "tr-TR",
                null
        ));

        // Yeni kayıt onay bekler — token verilmez.
        assertThat(response.pendingApproval()).isTrue();
        assertThat(response.session()).isNull();

        // Kullanıcı PENDING_APPROVAL durumunda kaydedilmeli.
        ArgumentCaptor<com.badhabinot.backend.model.auth.AuthUser> userCaptor =
                ArgumentCaptor.forClass(com.badhabinot.backend.model.auth.AuthUser.class);
        verify(authUserRepository).save(userCaptor.capture());
        assertThat(userCaptor.getValue().getStatus())
                .isEqualTo(com.badhabinot.backend.model.auth.AccountStatus.PENDING_APPROVAL);
        assertThat(userCaptor.getValue().getEmail()).isEqualTo("alice@example.com");

        ArgumentCaptor<UUID> userIdCaptor = ArgumentCaptor.forClass(UUID.class);
        verify(userContextService).bootstrap(
                userIdCaptor.capture(),
                eq("alice@example.com"),
                eq("Alice"),
                eq("Europe/Istanbul"),
                eq("tr-TR")
        );
        assertThat(userIdCaptor.getValue()).isNotNull();
    }

    @Test
    void registerRejectsDuplicateEmail() {
        when(authUserRepository.existsByEmail("duplicate@example.com")).thenReturn(true);

        assertThatThrownBy(() -> AuthApplicationServiceImpl.register(new RegisterRequest(
                "duplicate@example.com",
                "secret-123",
                "Alice",
                "UTC",
                "en-US",
                null
        ))).isInstanceOf(DuplicateEmailException.class)
                .hasMessageContaining("already exists");

        verifyNoInteractions(userContextService, tokenIssuer, refreshTokenService);
    }

    @Test
    void loginSucceedsWithCorrectCredentials() {
        Instant expiresAt = Instant.parse("2026-04-08T12:00:00Z");
        AuthUser user = AuthUser.create("bob@example.com", "hashed-pw", UserRole.USER, AccountStatus.ACTIVE);

        when(authUserRepository.findByEmail("bob@example.com")).thenReturn(Optional.of(user));
        when(passwordEncoder.matches("correct-pw", "hashed-pw")).thenReturn(true);
        when(authUserRepository.save(any())).thenAnswer(inv -> inv.getArgument(0));
        when(tokenIssuer.issueAccessToken(any())).thenReturn(new ITokenIssuer.IssuedAccessToken("access-token", expiresAt));
        when(refreshTokenService.generate(any())).thenReturn(new IRefreshTokenService.GeneratedRefreshToken(
                "refresh-token", "refresh-hash", expiresAt));

        var response = AuthApplicationServiceImpl.login(new LoginRequest("bob@example.com", "correct-pw"));

        assertThat(response.accessToken()).isEqualTo("access-token");
        assertThat(response.user().email()).isEqualTo("bob@example.com");
        verify(loginAttemptService).resetAttempts("bob@example.com");
    }

    @Test
    void loginRejectsWrongPassword() {
        AuthUser user = AuthUser.create("bob@example.com", "hashed-pw", UserRole.USER, AccountStatus.ACTIVE);
        when(authUserRepository.findByEmail("bob@example.com")).thenReturn(Optional.of(user));
        when(passwordEncoder.matches("wrong-pw", "hashed-pw")).thenReturn(false);

        assertThatThrownBy(() -> AuthApplicationServiceImpl.login(new LoginRequest("bob@example.com", "wrong-pw")))
                .isInstanceOf(AuthenticationFailedException.class);

        verify(loginAttemptService).recordFailure("bob@example.com");
        verifyNoInteractions(tokenIssuer, refreshTokenService);
    }

    @Test
    void loginRejectsUnknownEmail() {
        when(authUserRepository.findByEmail("ghost@example.com")).thenReturn(Optional.empty());

        assertThatThrownBy(() -> AuthApplicationServiceImpl.login(new LoginRequest("ghost@example.com", "pw")))
                .isInstanceOf(AuthenticationFailedException.class);

        verify(loginAttemptService).recordFailure("ghost@example.com");
    }

    @Test
    void faceLoginSucceedsWhenFaceMatches() {
        Instant expiresAt = Instant.parse("2026-04-08T12:00:00Z");
        UUID userId = UUID.randomUUID();
        AuthUser user = AuthUser.create("carol@example.com", "hashed-pw", UserRole.USER, AccountStatus.ACTIVE);

        when(authUserRepository.findByEmail("carol@example.com")).thenReturn(Optional.of(user));
        when(visionServiceClient.faceStatus(any())).thenReturn(
                new FaceRegisterResponse(userId.toString(), true, 5, "Profile active"));
        when(visionServiceClient.verifyFace(any(), any(), any())).thenReturn(
                new FaceVerificationResponse(true, 0.92f, "Yüz doğrulandı"));
        when(authUserRepository.save(any())).thenAnswer(inv -> inv.getArgument(0));
        when(tokenIssuer.issueAccessToken(any())).thenReturn(new ITokenIssuer.IssuedAccessToken("access-token", expiresAt));
        when(refreshTokenService.generate(any())).thenReturn(
                new IRefreshTokenService.GeneratedRefreshToken("refresh-token", "refresh-hash", expiresAt));

        var response = AuthApplicationServiceImpl.loginWithFace(
                new FaceLoginRequest("carol@example.com", "base64image==", "image/jpeg"));

        assertThat(response.accessToken()).isEqualTo("access-token");
        assertThat(response.user().email()).isEqualTo("carol@example.com");
        verify(loginAttemptService).resetAttempts("carol@example.com");
    }

    @Test
    void faceLoginThrowsFaceNotRegisteredWhenNoProfile() {
        AuthUser user = AuthUser.create("dave@example.com", "hashed-pw", UserRole.USER, AccountStatus.ACTIVE);
        when(authUserRepository.findByEmail("dave@example.com")).thenReturn(Optional.of(user));
        when(visionServiceClient.faceStatus(any())).thenReturn(
                new FaceRegisterResponse("user-id", false, 0, "No profile"));

        assertThatThrownBy(() -> AuthApplicationServiceImpl.loginWithFace(
                new FaceLoginRequest("dave@example.com", "base64image==", "image/jpeg")))
                .isInstanceOf(FaceNotRegisteredException.class);

        verifyNoInteractions(tokenIssuer, refreshTokenService);
    }

    @Test
    void faceLoginThrowsFaceMismatchWhenVerificationFails() {
        AuthUser user = AuthUser.create("eve@example.com", "hashed-pw", UserRole.USER, AccountStatus.ACTIVE);
        when(authUserRepository.findByEmail("eve@example.com")).thenReturn(Optional.of(user));
        when(visionServiceClient.faceStatus(any())).thenReturn(
                new FaceRegisterResponse("user-id", true, 5, "Profile active"));
        when(visionServiceClient.verifyFace(any(), any(), any())).thenReturn(
                new FaceVerificationResponse(false, 0.42f, "Yüz eşleşmedi"));

        assertThatThrownBy(() -> AuthApplicationServiceImpl.loginWithFace(
                new FaceLoginRequest("eve@example.com", "base64image==", "image/jpeg")))
                .isInstanceOf(FaceMismatchException.class);

        verify(loginAttemptService).recordFailure("eve@example.com");
        verifyNoInteractions(tokenIssuer, refreshTokenService);
    }

    @Test
    void faceLoginThrowsAuthFailedForUnknownEmail() {
        when(authUserRepository.findByEmail("ghost@example.com")).thenReturn(Optional.empty());

        assertThatThrownBy(() -> AuthApplicationServiceImpl.loginWithFace(
                new FaceLoginRequest("ghost@example.com", "base64image==", "image/jpeg")))
                .isInstanceOf(AuthenticationFailedException.class);

        verify(loginAttemptService).recordFailure("ghost@example.com");
    }

    @Test
    void refreshRejectsRevokedToken() {
        UUID userId = UUID.randomUUID();
        RefreshToken token = RefreshToken.issue(userId, "token-hash", Instant.now().plusSeconds(300));
        token.revoke(Instant.now());

        when(refreshTokenService.hash("refresh-token")).thenReturn("token-hash");
        when(refreshTokenRepository.findByTokenHash("token-hash")).thenReturn(Optional.of(token));

        assertThatThrownBy(() -> AuthApplicationServiceImpl.refresh(new RefreshTokenRequest("refresh-token")))
                .isInstanceOf(InvalidRefreshTokenException.class)
                .hasMessageContaining("expired or revoked");

        verifyNoInteractions(authUserRepository);
    }
}
