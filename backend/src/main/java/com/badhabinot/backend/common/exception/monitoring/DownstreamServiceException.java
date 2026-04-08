package com.badhabinot.backend.common.exception.monitoring;

public class DownstreamServiceException extends RuntimeException {

    private final String errorCode;

    public DownstreamServiceException(String errorCode, String message) {
        super(message);
        this.errorCode = errorCode;
    }

    public String getErrorCode() {
        return errorCode;
    }
}
