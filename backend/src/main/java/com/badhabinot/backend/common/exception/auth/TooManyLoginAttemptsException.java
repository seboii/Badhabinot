package com.badhabinot.backend.common.exception.auth;

public class TooManyLoginAttemptsException extends RuntimeException {

    public TooManyLoginAttemptsException(String message) {
        super(message);
    }
}
