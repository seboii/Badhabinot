package com.badhabinot.backend.dto.user;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public record UpdateProfileRequest(
        @NotBlank @Size(min = 2, max = 100) String displayName,
        @NotBlank @Size(min = 2, max = 64) String timezone,
        @NotBlank @Size(min = 2, max = 16) String locale
) {
}


