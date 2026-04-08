package com.badhabinot.backend.dto.user;

import com.badhabinot.backend.model.user.ModelMode;
import com.badhabinot.backend.model.user.Sensitivity;
import com.fasterxml.jackson.annotation.JsonFormat;
import java.time.LocalTime;
import java.util.UUID;

public record InternalUserAnalysisContextResponse(
        UUID userId,
        String timezone,
        Sensitivity sensitivity,
        ModelMode modelMode,
        boolean cameraMonitoringAccepted,
        int waterGoalMl,
        int waterIntervalMin,
        int exerciseIntervalMin,
        boolean notificationsEnabled,
        boolean quietHoursEnabled,
        @JsonFormat(pattern = "HH:mm") LocalTime quietHoursStart,
        @JsonFormat(pattern = "HH:mm") LocalTime quietHoursEnd,
        boolean remoteInferenceAccepted
) {
}

