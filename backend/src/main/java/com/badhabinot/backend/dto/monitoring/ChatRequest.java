package com.badhabinot.backend.dto.monitoring;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public record ChatRequest(
        @Size(max = 64) String conversationId,
        @NotBlank @Size(max = 2000) String message
) {
}

