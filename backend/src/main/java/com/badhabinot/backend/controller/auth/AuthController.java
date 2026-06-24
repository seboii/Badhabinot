package com.badhabinot.backend.controller.auth;

import com.badhabinot.backend.dto.auth.AuthenticatedUserResponse;
import com.badhabinot.backend.dto.auth.FaceLoginRequest;
import com.badhabinot.backend.dto.auth.LoginRequest;
import com.badhabinot.backend.dto.auth.LogoutRequest;
import com.badhabinot.backend.dto.auth.PasswordResetConfirmDto;
import com.badhabinot.backend.dto.auth.PasswordResetRequestDto;
import com.badhabinot.backend.dto.auth.RefreshTokenRequest;
import com.badhabinot.backend.dto.auth.RegisterRequest;
import com.badhabinot.backend.dto.auth.RegisterResponse;
import com.badhabinot.backend.dto.auth.TokenResponse;
import com.badhabinot.backend.common.exception.auth.TooManyLoginAttemptsException;
import com.badhabinot.backend.dto.auth.CaptchaChallengeResponse;
import com.badhabinot.backend.dto.auth.CaptchaVerifyRequest;
import com.badhabinot.backend.dto.auth.CaptchaVerifyResponse;
import com.badhabinot.backend.dto.auth.FaceChallengeResponse;
import com.badhabinot.backend.infrastructure.redis.CaptchaService;
import com.badhabinot.backend.infrastructure.redis.FaceChallengeService;
import com.badhabinot.backend.infrastructure.redis.RateLimiterService;
import com.badhabinot.backend.model.auth.AuthUser;
import com.badhabinot.backend.model.auth.UserRole;
import com.badhabinot.backend.repository.auth.AuthUserRepository;
import com.badhabinot.backend.service.auth.IAuthApplicationService;
import com.badhabinot.backend.service.auth.IMailService;
import com.badhabinot.backend.service.auth.IPasswordResetService;
import com.badhabinot.backend.service.monitoring.IPushNotificationService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.security.SecurityRequirement;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.validation.Valid;
import java.time.Duration;
import java.util.Map;
import org.springframework.http.HttpStatus;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.oauth2.jwt.Jwt;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/auth")
@Tag(name = "Authentication", description = "Registration, login, refresh, and current-user APIs")
public class AuthController {

    private final IAuthApplicationService authApplicationService;
    private final IPasswordResetService passwordResetService;
    private final RateLimiterService rateLimiter;
    private final CaptchaService captchaService;
    private final FaceChallengeService faceChallengeService;
    private final IMailService mailService;
    private final AuthUserRepository authUserRepository;
    private final IPushNotificationService pushNotificationService;

    public AuthController(
            IAuthApplicationService authApplicationService,
            IPasswordResetService passwordResetService,
            RateLimiterService rateLimiter,
            CaptchaService captchaService,
            FaceChallengeService faceChallengeService,
            IMailService mailService,
            AuthUserRepository authUserRepository,
            IPushNotificationService pushNotificationService
    ) {
        this.authApplicationService = authApplicationService;
        this.passwordResetService = passwordResetService;
        this.rateLimiter = rateLimiter;
        this.captchaService = captchaService;
        this.faceChallengeService = faceChallengeService;
        this.mailService = mailService;
        this.authUserRepository = authUserRepository;
        this.pushNotificationService = pushNotificationService;
    }

    @GetMapping("/captcha")
    @Operation(summary = "Issue a server-side image CAPTCHA challenge (public)")
    public CaptchaChallengeResponse captcha() {
        return captchaService.issue();
    }

    @PostMapping("/captcha/verify")
    @Operation(summary = "Verify a CAPTCHA solution and obtain a one-time pass token for registration")
    public CaptchaVerifyResponse verifyCaptcha(@Valid @RequestBody CaptchaVerifyRequest request) {
        return new CaptchaVerifyResponse(captchaService.verify(request.captchaId(), request.answer()));
    }

    @PostMapping("/register")
    @ResponseStatus(HttpStatus.CREATED)
    @Operation(summary = "Register a new BADHABINOT user (requires admin approval before login)")
    public RegisterResponse register(@Valid @RequestBody RegisterRequest request, HttpServletRequest http) {
        // Kötüye kullanım koruması: aynı IP'den saatte en fazla 5 kayıt.
        if (!rateLimiter.allow("register:" + clientIp(http), 5, Duration.ofHours(1))) {
            throw new TooManyLoginAttemptsException("Çok fazla kayıt denemesi. Lütfen daha sonra tekrar deneyin.");
        }
        // Sunucu-taraflı robot doğrulaması: geçiş token'ı tek-kullanımlık tüketilir.
        captchaService.consumePass(request.captchaToken());
        RegisterResponse response = authApplicationService.register(request);
        // Yöneticiye "yeni kullanıcı onay bekliyor" bildirimi: hem e-posta hem
        // mobil push (admin Capacitor uygulamasında). Hatalar kaydı bozmaz.
        try {
            mailService.sendNewUserNotification(request.email());
        } catch (Exception ignored) {
            // non-fatal
        }
        try {
            for (AuthUser admin : authUserRepository.findByRole(UserRole.ADMIN)) {
                pushNotificationService.sendToUser(
                        admin.getId(),
                        "Yeni kayıt onayı bekliyor",
                        request.email() + " kaydoldu, onayını bekliyor.",
                        Map.of("type", "NEW_USER_PENDING", "email", request.email())
                );
            }
        } catch (Exception ignored) {
            // non-fatal (Firebase yapılandırılmamışsa sessizce atlanır)
        }
        return response;
    }

    @PostMapping("/login")
    @Operation(summary = "Authenticate an existing BADHABINOT user")
    public TokenResponse login(@Valid @RequestBody LoginRequest request) {
        return authApplicationService.login(request);
    }

    @PostMapping("/login/face/challenge")
    @Operation(summary = "Issue a random liveness challenge (blink / head-turn) for face login")
    public FaceChallengeResponse faceChallenge() {
        return faceChallengeService.issue();
    }

    @PostMapping("/login/face")
    @Operation(summary = "Authenticate using face recognition + active-challenge liveness")
    public TokenResponse loginWithFace(@Valid @RequestBody FaceLoginRequest request) {
        return authApplicationService.loginWithFace(request);
    }

    @PostMapping("/refresh")
    @Operation(summary = "Rotate refresh token and obtain a new access token")
    public TokenResponse refresh(@Valid @RequestBody RefreshTokenRequest request) {
        return authApplicationService.refresh(request);
    }

    @PostMapping("/logout")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    @Operation(summary = "Revoke refresh token and terminate the current login session", security = @SecurityRequirement(name = "bearerAuth"))
    public void logout(@AuthenticationPrincipal Jwt jwt, @Valid @RequestBody LogoutRequest request) {
        authApplicationService.logout(jwt, request);
    }

    @PostMapping("/password-reset-request")
    @Operation(summary = "Request a password reset email — always returns 200 to avoid email enumeration")
    public void passwordResetRequest(@Valid @RequestBody PasswordResetRequestDto request) {
        // E-posta spam'ini önle: aynı adrese saatte en fazla 3 sıfırlama isteği.
        if (!rateLimiter.allow("pwdreset:" + request.email().trim().toLowerCase(), 3, Duration.ofHours(1))) {
            throw new TooManyLoginAttemptsException("Çok fazla şifre sıfırlama isteği. Lütfen daha sonra tekrar deneyin.");
        }
        passwordResetService.requestReset(request);
    }

    /** Caddy/nginx arkasında gerçek istemci IP'si (ForwardedHeaderFilter X-Forwarded-For'u uygular). */
    private static String clientIp(HttpServletRequest http) {
        String ip = http.getRemoteAddr();
        return (ip == null || ip.isBlank()) ? "unknown" : ip;
    }

    @PostMapping("/password-reset-confirm")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    @Operation(summary = "Confirm a password reset using the token received by email")
    public void passwordResetConfirm(@Valid @RequestBody PasswordResetConfirmDto request) {
        passwordResetService.confirmReset(request);
    }

    @GetMapping("/me")
    @Operation(summary = "Inspect the currently authenticated user", security = @SecurityRequirement(name = "bearerAuth"))
    public AuthenticatedUserResponse me(@AuthenticationPrincipal Jwt jwt) {
        return authApplicationService.me(jwt);
    }
}
