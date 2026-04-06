package com.badhabinot.monitoring.application.exception;

public class DownstreamTimeoutException extends DownstreamServiceException {

    public DownstreamTimeoutException(String errorCode, String message) {
        super(errorCode, message);
    }
}

