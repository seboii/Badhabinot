package com.badhabinot.backend.dto.user;

import jakarta.validation.constraints.NotNull;

public record UpdateConsentsRequest(
        @NotNull Boolean privacyPolicyAccepted,
        @NotNull Boolean cameraMonitoringAccepted,
        @NotNull Boolean remoteInferenceAccepted
) {
}


