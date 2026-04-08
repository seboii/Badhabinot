package com.badhabinot.backend.common.exception.auth;

public class UserProvisioningException extends RuntimeException {

    public UserProvisioningException(String message, Throwable cause) {
        super(message, cause);
    }
}
