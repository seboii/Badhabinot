package com.badhabinot.backend.dto.auth;

import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public record RegisterRequest(
        @NotBlank @Email String email,
        @NotBlank @Size(min = 8, max = 100) String password,
        @NotBlank @Size(min = 2, max = 100) String displayName,
        @NotBlank @Size(min = 2, max = 64) String timezone,
        @NotBlank @Size(min = 2, max = 16) String locale
) {
}


