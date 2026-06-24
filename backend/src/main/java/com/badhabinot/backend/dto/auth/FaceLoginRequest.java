package com.badhabinot.backend.dto.auth;

import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotEmpty;
import java.util.List;

/**
 * Aktif challenge ile yüz girişi. Tek kare yerine kısa bir kare DİZİSİ gönderilir;
 * sunucu hem kimliği (embedding) hem istenen eylemin (challenge) yapıldığını doğrular.
 */
public record FaceLoginRequest(
        @Email @NotBlank String email,
        @NotBlank String challengeId,
        @NotEmpty List<String> frames,
        @NotBlank String imageContentType
) {
}
