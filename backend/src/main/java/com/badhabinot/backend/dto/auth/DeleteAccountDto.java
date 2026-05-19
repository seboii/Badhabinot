package com.badhabinot.backend.dto.auth;

import jakarta.validation.constraints.NotBlank;

public record DeleteAccountDto(
        @NotBlank String password
) {
}
