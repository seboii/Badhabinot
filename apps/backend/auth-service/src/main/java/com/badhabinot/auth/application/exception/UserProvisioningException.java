package com.badhabinot.auth.application.exception;

public class UserProvisioningException extends RuntimeException {

    public UserProvisioningException(String message, Throwable cause) {
        super(message, cause);
    }
}

