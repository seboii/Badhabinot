package com.badhabinot.backend.service.auth;

import com.badhabinot.backend.dto.auth.PasswordResetConfirmDto;
import com.badhabinot.backend.dto.auth.PasswordResetRequestDto;

public interface IPasswordResetService {
    void requestReset(PasswordResetRequestDto request);
    void confirmReset(PasswordResetConfirmDto request);
}
