package com.badhabinot.user.application.dto;

import com.badhabinot.user.domain.model.ModelMode;
import com.badhabinot.user.domain.model.Sensitivity;
import com.fasterxml.jackson.annotation.JsonFormat;
import java.time.LocalTime;
import java.util.UUID;

public record InternalUserAnalysisContextResponse(
        UUID userId,
        String timezone,
        Sensitivity sensitivity,
        ModelMode modelMode,
        int waterGoalMl,
        boolean notificationsEnabled,
        boolean quietHoursEnabled,
        @JsonFormat(pattern = "HH:mm") LocalTime quietHoursStart,
        @JsonFormat(pattern = "HH:mm") LocalTime quietHoursEnd,
        boolean remoteInferenceAccepted
) {
}
