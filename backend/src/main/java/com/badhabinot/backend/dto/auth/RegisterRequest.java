package com.badhabinot.backend.dto.auth;

import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;

public record RegisterRequest(
        @NotBlank @Email String email,
        @NotBlank
        @Size(min = 8, max = 100)
        @Pattern(
                regexp = "^(?=.*[a-z])(?=.*[A-Z])(?=.*\\d).{8,100}$",
                message = "Şifre en az 8 karakter olmalı ve en az bir büyük harf, bir küçük harf ve bir rakam içermeli."
        )
        String password,
        @NotBlank @Size(min = 2, max = 100) String displayName,
        @NotBlank @Size(min = 2, max = 64) String timezone,
        @NotBlank @Size(min = 2, max = 16) String locale,
        // Sunucu-taraflı captcha geçiş token'ı (POST /auth/captcha/verify'den alınır).
        // Zorunluluk kontrolü AuthController'da CaptchaService.consumePass ile yapılır.
        String captchaToken
) {
}


