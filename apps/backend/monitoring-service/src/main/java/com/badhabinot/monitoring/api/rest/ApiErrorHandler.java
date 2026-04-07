package com.badhabinot.monitoring.api.rest;

import com.badhabinot.monitoring.application.exception.DownstreamServiceException;
import com.badhabinot.monitoring.application.exception.DownstreamTimeoutException;
import java.time.Instant;
import java.util.LinkedHashMap;
import java.util.Map;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.FieldError;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

@RestControllerAdvice
public class ApiErrorHandler {

    private static final Logger log = LoggerFactory.getLogger(ApiErrorHandler.class);

    @ExceptionHandler(DownstreamTimeoutException.class)
    public ResponseEntity<Map<String, Object>> handleTimeout(DownstreamTimeoutException exception) {
        return error(HttpStatus.GATEWAY_TIMEOUT, exception.getErrorCode(), exception.getMessage());
    }

    @ExceptionHandler(DownstreamServiceException.class)
    public ResponseEntity<Map<String, Object>> handleDownstream(DownstreamServiceException exception) {
        return error(HttpStatus.BAD_GATEWAY, exception.getErrorCode(), exception.getMessage());
    }

    @ExceptionHandler(IllegalArgumentException.class)
    public ResponseEntity<Map<String, Object>> handleIllegalArgument(IllegalArgumentException exception) {
        return error(HttpStatus.BAD_REQUEST, "invalid_request", exception.getMessage());
    }

    @ExceptionHandler(IllegalStateException.class)
    public ResponseEntity<Map<String, Object>> handleIllegalState(IllegalStateException exception) {
        return error(HttpStatus.CONFLICT, "workflow_conflict", exception.getMessage());
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<Map<String, Object>> handleValidation(MethodArgumentNotValidException exception) {
        Map<String, String> fieldErrors = new LinkedHashMap<>();
        for (FieldError fieldError : exception.getBindingResult().getFieldErrors()) {
            fieldErrors.put(fieldError.getField(), fieldError.getDefaultMessage());
        }
        Map<String, Object> body = baseBody(HttpStatus.BAD_REQUEST, "validation_failed", "Validation failed");
        body.put("fieldErrors", fieldErrors);
        return ResponseEntity.badRequest().body(body);
    }

    @ExceptionHandler(Exception.class)
    public ResponseEntity<Map<String, Object>> handleUnhandled(Exception exception) {
        log.error("Unhandled monitoring-service exception", exception);
        return error(HttpStatus.INTERNAL_SERVER_ERROR, "unexpected_error", "Unexpected server error");
    }

    private ResponseEntity<Map<String, Object>> error(HttpStatus status, String code, String message) {
        return ResponseEntity.status(status).body(baseBody(status, code, message));
    }

    private Map<String, Object> baseBody(HttpStatus status, String code, String message) {
        return new LinkedHashMap<>(Map.of(
                "timestamp", Instant.now(),
                "status", status.value(),
                "error", status.getReasonPhrase(),
                "code", code,
                "message", message
        ));
    }
}
