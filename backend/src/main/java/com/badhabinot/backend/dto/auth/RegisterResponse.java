package com.badhabinot.backend.dto.auth;

/**
 * Kayıt yanıtı. Yeni kullanıcılar yönetici onayı beklediğinden kayıtta token
 * verilmez; onay sonrası kullanıcı normal giriş yapar.
 *
 * @param pendingApproval onay bekleniyorsa true (session null olur)
 * @param message kullanıcıya gösterilecek bilgilendirme
 * @param session onay gerekmiyorsa (ileride otomatik onay) oturum; aksi halde null
 */
public record RegisterResponse(
        boolean pendingApproval,
        String message,
        TokenResponse session
) {
}
