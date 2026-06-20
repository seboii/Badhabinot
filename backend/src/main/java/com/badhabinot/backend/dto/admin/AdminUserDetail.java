package com.badhabinot.backend.dto.admin;

import java.time.Instant;
import java.util.UUID;

/** Admin için tek kullanıcının tüm DB'lerden derlenmiş detayı. */
public record AdminUserDetail(
        UUID id,
        String email,
        String role,
        String status,
        Instant createdAt,
        Instant lastLoginAt,
        Profile profile,
        Settings settings,
        Consents consents,
        Stats stats,
        Face face
) {
    public record Profile(String displayName, String timezone, String locale) {
    }

    public record Settings(
            String sensitivity,
            String modelMode,
            int waterGoalMl,
            int waterIntervalMin,
            int exerciseIntervalMin,
            boolean notificationsEnabled
    ) {
    }

    public record Consents(
            boolean privacyPolicyAccepted,
            boolean cameraMonitoringAccepted,
            boolean remoteInferenceAccepted
    ) {
    }

    public record Stats(
            long sessions,
            long analyses,
            long events,
            long reports,
            long chatMessages
    ) {
    }

    public record Face(boolean enrolled, int framesEnrolled) {
    }
}
