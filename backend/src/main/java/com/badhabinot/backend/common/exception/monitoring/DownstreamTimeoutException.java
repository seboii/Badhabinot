package com.badhabinot.backend.common.exception.monitoring;

public class DownstreamTimeoutException extends DownstreamServiceException {

    public DownstreamTimeoutException(String errorCode, String message) {
        super(errorCode, message);
    }
}
