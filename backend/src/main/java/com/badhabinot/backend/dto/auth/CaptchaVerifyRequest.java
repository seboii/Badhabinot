package com.badhabinot.backend.dto.auth;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import java.util.List;

/** Kullanıcının captcha çözümü: hangi challenge ve seçilen karo indeksleri. */
public record CaptchaVerifyRequest(
        @NotBlank String captchaId,
        @NotNull List<Integer> answer
) {
}
