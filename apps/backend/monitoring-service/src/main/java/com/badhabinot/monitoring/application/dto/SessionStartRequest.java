package com.badhabinot.monitoring.application.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public record SessionStartRequest(
        @NotBlank @Size(max = 32) String clientSurface,
        @NotBlank @Size(max = 32) String deviceType
) {
}

