package com.badhabinot.user.application.dto;

import com.badhabinot.user.domain.model.ModelMode;
import com.badhabinot.user.domain.model.Sensitivity;
import com.fasterxml.jackson.annotation.JsonFormat;
import java.time.Instant;
import java.time.LocalTime;

public record SettingsResponse(
        Sensitivity sensitivity,
        int waterGoalMl,
        int waterIntervalMin,
        int exerciseIntervalMin,
        boolean quietHoursEnabled,
        @JsonFormat(pattern = "HH:mm") LocalTime quietHoursStart,
        @JsonFormat(pattern = "HH:mm") LocalTime quietHoursEnd,
        ModelMode modelMode,
        boolean notificationsEnabled,
        Instant updatedAt
) {
}
