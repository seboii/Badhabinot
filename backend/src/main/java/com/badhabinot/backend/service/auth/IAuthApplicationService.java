package com.badhabinot.backend.service.auth;

import com.badhabinot.backend.dto.auth.AuthenticatedUserResponse;
import com.badhabinot.backend.dto.auth.ChangePasswordDto;
import com.badhabinot.backend.dto.auth.FaceLoginRequest;
import com.badhabinot.backend.dto.auth.LoginRequest;
import com.badhabinot.backend.dto.auth.LogoutRequest;
import com.badhabinot.backend.dto.auth.RefreshTokenRequest;
import com.badhabinot.backend.dto.auth.RegisterRequest;
import com.badhabinot.backend.dto.auth.TokenResponse;
import java.util.UUID;
import org.springframework.security.oauth2.jwt.Jwt;

public interface IAuthApplicationService {
    TokenResponse register(RegisterRequest request);
    TokenResponse login(LoginRequest request);
    TokenResponse loginWithFace(FaceLoginRequest request);
    TokenResponse refresh(RefreshTokenRequest request);
    AuthenticatedUserResponse me(Jwt jwt);
    void logout(Jwt jwt, LogoutRequest request);
    void changePassword(UUID userId, ChangePasswordDto dto);
}
