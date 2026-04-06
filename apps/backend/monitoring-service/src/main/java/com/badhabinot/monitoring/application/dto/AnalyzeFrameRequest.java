package com.badhabinot.monitoring.application.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import java.time.Instant;

public record AnalyzeFrameRequest(
        @NotBlank @Size(max = 128) String sessionId,
        @NotBlank @Size(max = 128) String frameId,
        @NotNull Instant capturedAt,
        @NotBlank String imageBase64,
        @NotBlank @Size(max = 64) String imageContentType
) {
}

