package com.badhabinot.backend.controller.user;

import com.badhabinot.backend.dto.auth.ChangePasswordDto;
import com.badhabinot.backend.dto.auth.DeleteAccountDto;
import com.badhabinot.backend.dto.user.ConsentResponse;
import com.badhabinot.backend.dto.user.SettingsResponse;
import com.badhabinot.backend.dto.user.UpdateConsentsRequest;
import com.badhabinot.backend.dto.user.UpdateProfileRequest;
import com.badhabinot.backend.dto.user.UpdateSettingsRequest;
import com.badhabinot.backend.dto.user.UserContextResponse;
import com.badhabinot.backend.dto.user.UserProfileResponse;
import com.badhabinot.backend.service.auth.AccountDeletionService;
import com.badhabinot.backend.service.auth.AuthApplicationService;
import com.badhabinot.backend.service.user.UserContextService;
import com.badhabinot.backend.security.CurrentUserClaims;
import java.util.UUID;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.security.SecurityRequirement;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.oauth2.jwt.Jwt;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping
@Tag(name = "Users", description = "User profile, settings, consent, and bootstrap APIs")
public class UserController {

    private final UserContextService userContextService;
    private final AuthApplicationService authApplicationService;
    private final AccountDeletionService accountDeletionService;

    public UserController(UserContextService userContextService, AuthApplicationService authApplicationService, AccountDeletionService accountDeletionService) {
        this.userContextService = userContextService;
        this.authApplicationService = authApplicationService;
        this.accountDeletionService = accountDeletionService;
    }

    @GetMapping("/api/v1/users/me")
    @Operation(summary = "Return current user profile and settings", security = @SecurityRequirement(name = "bearerAuth"))
    public UserContextResponse me(@AuthenticationPrincipal Jwt jwt) {
        return userContextService.getContext(CurrentUserClaims.from(jwt));
    }

    @PutMapping("/api/v1/users/me")
    @Operation(summary = "Update current user profile", security = @SecurityRequirement(name = "bearerAuth"))
    public UserProfileResponse updateProfile(@AuthenticationPrincipal Jwt jwt, @Valid @RequestBody UpdateProfileRequest request) {
        return userContextService.updateProfile(CurrentUserClaims.from(jwt), request);
    }

    @GetMapping("/api/v1/users/me/settings")
    @Operation(summary = "Return current user settings", security = @SecurityRequirement(name = "bearerAuth"))
    public SettingsResponse getSettings(@AuthenticationPrincipal Jwt jwt) {
        return userContextService.getSettings(CurrentUserClaims.from(jwt));
    }

    @PutMapping("/api/v1/users/me/settings")
    @Operation(summary = "Update current user settings", security = @SecurityRequirement(name = "bearerAuth"))
    public SettingsResponse updateSettings(@AuthenticationPrincipal Jwt jwt, @Valid @RequestBody UpdateSettingsRequest request) {
        return userContextService.updateSettings(CurrentUserClaims.from(jwt), request);
    }

    @GetMapping("/api/v1/users/me/consents")
    @Operation(summary = "Return current user consents", security = @SecurityRequirement(name = "bearerAuth"))
    public ConsentResponse getConsents(@AuthenticationPrincipal Jwt jwt) {
        return userContextService.getConsents(CurrentUserClaims.from(jwt));
    }

    @PutMapping("/api/v1/users/me/consents")
    @Operation(summary = "Update current user consents", security = @SecurityRequirement(name = "bearerAuth"))
    public ConsentResponse updateConsents(@AuthenticationPrincipal Jwt jwt, @Valid @RequestBody UpdateConsentsRequest request) {
        return userContextService.updateConsents(CurrentUserClaims.from(jwt), request);
    }

    @PostMapping("/api/v1/user/change-password")
    @Operation(summary = "Change the authenticated user's password and invalidate all refresh tokens", security = @SecurityRequirement(name = "bearerAuth"))
    public void changePassword(@AuthenticationPrincipal Jwt jwt, @Valid @RequestBody ChangePasswordDto request) {
        UUID userId = UUID.fromString(jwt.getSubject());
        authApplicationService.changePassword(userId, request);
    }

    @DeleteMapping("/api/v1/user/account")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    @Operation(summary = "Permanently delete the authenticated user's account and all associated data", security = @SecurityRequirement(name = "bearerAuth"))
    public void deleteAccount(@AuthenticationPrincipal Jwt jwt, @Valid @RequestBody DeleteAccountDto request) {
        UUID userId = UUID.fromString(jwt.getSubject());
        accountDeletionService.deleteAccount(userId, request.password());
    }
}

