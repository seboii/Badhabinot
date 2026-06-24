package com.badhabinot.backend.common.exception.auth;

/** Captcha doğrulaması başarısız, süresi dolmuş veya eksik token. */
public class InvalidCaptchaException extends RuntimeException {

    public InvalidCaptchaException(String message) {
        super(message);
    }
}
