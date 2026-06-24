package com.badhabinot.backend.dto.auth;

/** Başarılı captcha doğrulamasında verilen tek-kullanımlık geçiş token'ı. */
public record CaptchaVerifyResponse(String token) {
}
