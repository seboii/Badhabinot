package com.badhabinot.backend.common.exception.auth;

/** Canlılık (liveness) görevi yapılamadı veya challenge geçersiz/expired. */
public class FaceLivenessFailedException extends RuntimeException {

    public FaceLivenessFailedException(String message) {
        super(message);
    }
}
