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
import com.badhabinot.backend.service.auth.IAuthApplicationService;
import com.badhabinot.backend.service.auth.IPasswordResetService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.security.SecurityRequirement;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
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

    public AuthController(IAuthApplicationService authApplicationService, IPasswordResetService passwordResetService) {
        this.authApplicationService = authApplicationService;
        this.passwordResetService = passwordResetService;
    }

    @PostMapping("/register")
    @ResponseStatus(HttpStatus.CREATED)
    @Operation(summary = "Register a new BADHABINOT user (requires admin approval before login)")
    public RegisterResponse register(@Valid @RequestBody RegisterRequest request) {
        return authApplicationService.register(request);
    }

    @PostMapping("/login")
    @Operation(summary = "Authenticate an existing BADHABINOT user")
    public TokenResponse login(@Valid @RequestBody LoginRequest request) {
        return authApplicationService.login(request);
    }

    @PostMapping("/login/face")
    @Operation(summary = "Authenticate using face recognition — requires a registered face profile")
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
        passwordResetService.requestReset(request);
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
