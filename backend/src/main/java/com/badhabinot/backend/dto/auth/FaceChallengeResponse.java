package com.badhabinot.backend.dto.auth;

/**
 * Yüz girişi öncesi verilen canlılık görevi (challenge). İstemci bu eylemi
 * yaparken kısa bir kare dizisi yakalar ve {@code challengeId} ile geri gönderir.
 */
public record FaceChallengeResponse(
        String challengeId,
        String action,      // BLINK | TURN_HEAD
        String promptTr,
        String promptEn
) {
}
