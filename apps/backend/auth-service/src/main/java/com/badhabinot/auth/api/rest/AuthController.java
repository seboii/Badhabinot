package com.badhabinot.auth.api.rest;

import com.badhabinot.auth.application.dto.AuthenticatedUserResponse;
import com.badhabinot.auth.application.dto.LoginRequest;
import com.badhabinot.auth.application.dto.LogoutRequest;
import com.badhabinot.auth.application.dto.RefreshTokenRequest;
import com.badhabinot.auth.application.dto.RegisterRequest;
import com.badhabinot.auth.application.dto.TokenResponse;
import com.badhabinot.auth.application.service.AuthApplicationService;
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

    private final AuthApplicationService authApplicationService;

    public AuthController(AuthApplicationService authApplicationService) {
        this.authApplicationService = authApplicationService;
    }

    @PostMapping("/register")
    @ResponseStatus(HttpStatus.CREATED)
    @Operation(summary = "Register a new BADHABINOT user")
    public TokenResponse register(@Valid @RequestBody RegisterRequest request) {
        return authApplicationService.register(request);
    }

    @PostMapping("/login")
    @Operation(summary = "Authenticate an existing BADHABINOT user")
    public TokenResponse login(@Valid @RequestBody LoginRequest request) {
        return authApplicationService.login(request);
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

    @GetMapping("/me")
    @Operation(summary = "Inspect the currently authenticated user", security = @SecurityRequirement(name = "bearerAuth"))
    public AuthenticatedUserResponse me(@AuthenticationPrincipal Jwt jwt) {
        return authApplicationService.me(jwt);
    }
}
