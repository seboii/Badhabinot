package com.badhabinot.backend.dto.auth;

import java.util.List;

/**
 * Sunucu-taraflı captcha challenge'ı. {@code tiles} her biri bir
 * {@code data:image/png;base64,...} URI'si olan 9 görsel karodur; hedef şekil
 * yalnızca etiket (promptTr/promptEn) olarak verilir — şekil bilgisi karolarda
 * piksel olarak gizlidir.
 */
public record CaptchaChallengeResponse(
        String captchaId,
        String promptTr,
        String promptEn,
        List<String> tiles
) {
}
