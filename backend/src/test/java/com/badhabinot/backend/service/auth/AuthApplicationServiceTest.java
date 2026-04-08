package com.badhabinot.backend.service.auth;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.verifyNoInteractions;
import static org.mockito.Mockito.when;

import com.badhabinot.backend.dto.auth.RefreshTokenRequest;
import com.badhabinot.backend.dto.auth.RegisterRequest;
import com.badhabinot.backend.common.exception.auth.DuplicateEmailException;
import com.badhabinot.backend.common.exception.auth.InvalidRefreshTokenException;
import com.badhabinot.backend.model.auth.AccountStatus;
import com.badhabinot.backend.model.auth.RefreshToken;
import com.badhabinot.backend.model.auth.UserRole;
import com.badhabinot.backend.repository.auth.AuthUserRepository;
import com.badhabinot.backend.repository.auth.RefreshTokenRepository;
import com.badhabinot.backend.service.user.UserContextService;
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
    private TokenIssuer tokenIssuer;

    @Mock
    private RefreshTokenService refreshTokenService;

    @Mock
    private UserContextService userContextService;

    @InjectMocks
    private AuthApplicationService authApplicationService;

    @Test
    void registerNormalizesEmailAndBootstrapsUserContext() {
        Instant expiresAt = Instant.parse("2026-04-08T12:00:00Z");
        when(authUserRepository.existsByEmail("alice@example.com")).thenReturn(false);
        when(passwordEncoder.encode("secret-123")).thenReturn("encoded-password");
        when(authUserRepository.save(any())).thenAnswer(invocation -> invocation.getArgument(0));
        when(tokenIssuer.issueAccessToken(any())).thenReturn(new TokenIssuer.IssuedAccessToken("access-token", expiresAt));
        when(refreshTokenService.generate(any())).thenReturn(new RefreshTokenService.GeneratedRefreshToken(
                "refresh-token",
                "refresh-hash",
                expiresAt
        ));

        var response = authApplicationService.register(new RegisterRequest(
                " Alice@Example.com ",
                "secret-123",
                "Alice",
                "Europe/Istanbul",
                "tr-TR"
        ));

        assertThat(response.accessToken()).isEqualTo("access-token");
        assertThat(response.refreshToken()).isEqualTo("refresh-token");
        assertThat(response.user().email()).isEqualTo("alice@example.com");

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

        assertThatThrownBy(() -> authApplicationService.register(new RegisterRequest(
                "duplicate@example.com",
                "secret-123",
                "Alice",
                "UTC",
                "en-US"
        ))).isInstanceOf(DuplicateEmailException.class)
                .hasMessageContaining("already exists");

        verifyNoInteractions(userContextService, tokenIssuer, refreshTokenService);
    }

    @Test
    void refreshRejectsRevokedToken() {
        UUID userId = UUID.randomUUID();
        RefreshToken token = RefreshToken.issue(userId, "token-hash", Instant.now().plusSeconds(300));
        token.revoke(Instant.now());

        when(refreshTokenService.hash("refresh-token")).thenReturn("token-hash");
        when(refreshTokenRepository.findByTokenHash("token-hash")).thenReturn(Optional.of(token));

        assertThatThrownBy(() -> authApplicationService.refresh(new RefreshTokenRequest("refresh-token")))
                .isInstanceOf(InvalidRefreshTokenException.class)
                .hasMessageContaining("expired or revoked");

        verifyNoInteractions(authUserRepository);
    }
}
