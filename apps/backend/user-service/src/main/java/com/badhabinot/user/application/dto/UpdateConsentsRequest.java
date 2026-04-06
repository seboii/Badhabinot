package com.badhabinot.user.application.dto;

import jakarta.validation.constraints.NotNull;

public record UpdateConsentsRequest(
        @NotNull Boolean privacyPolicyAccepted,
        @NotNull Boolean cameraMonitoringAccepted,
        @NotNull Boolean remoteInferenceAccepted
) {
}

