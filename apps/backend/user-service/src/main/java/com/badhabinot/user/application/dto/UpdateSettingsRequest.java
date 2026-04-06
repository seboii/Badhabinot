package com.badhabinot.user.application.dto;

import com.badhabinot.user.domain.model.ModelMode;
import com.badhabinot.user.domain.model.Sensitivity;
import com.fasterxml.jackson.annotation.JsonFormat;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotNull;
import java.time.LocalTime;

public record UpdateSettingsRequest(
        @NotNull Sensitivity sensitivity,
        @NotNull @Min(250) @Max(6000) Integer waterGoalMl,
        @NotNull @Min(15) @Max(240) Integer waterIntervalMin,
        @NotNull @Min(15) @Max(240) Integer exerciseIntervalMin,
        @NotNull Boolean quietHoursEnabled,
        @NotNull @JsonFormat(pattern = "HH:mm") LocalTime quietHoursStart,
        @NotNull @JsonFormat(pattern = "HH:mm") LocalTime quietHoursEnd,
        @NotNull ModelMode modelMode,
        @NotNull Boolean notificationsEnabled
) {
}
