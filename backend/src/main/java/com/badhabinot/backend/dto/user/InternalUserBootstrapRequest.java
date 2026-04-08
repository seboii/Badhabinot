package com.badhabinot.backend.dto.user;

import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import java.util.UUID;

public record InternalUserBootstrapRequest(
        @NotNull UUID userId,
        @NotBlank @Email String email,
        @NotBlank @Size(min = 2, max = 100) String displayName,
        @NotBlank @Size(min = 2, max = 64) String timezone,
        @NotBlank @Size(min = 2, max = 16) String locale
) {
}


