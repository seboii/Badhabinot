package com.badhabinot.backend.dto.user;

import java.time.Instant;

public record ConsentResponse(
        boolean privacyPolicyAccepted,
        boolean cameraMonitoringAccepted,
        boolean remoteInferenceAccepted,
        Instant acceptedAt,
        Instant updatedAt
) {
}


