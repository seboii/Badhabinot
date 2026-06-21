package com.badhabinot.backend.dto.auth;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;

public record ChangePasswordDto(
        @NotBlank String currentPassword,
        @NotBlank
        @Size(min = 8, max = 100)
        @Pattern(
                regexp = "^(?=.*[a-z])(?=.*[A-Z])(?=.*\\d).{8,100}$",
                message = "Şifre en az 8 karakter olmalı ve en az bir büyük harf, bir küçük harf ve bir rakam içermeli."
        )
        String newPassword
) {
}
