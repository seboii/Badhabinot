package com.badhabinot.monitoring.application.dto;

import java.time.LocalDate;

public record WeeklyTrendPointResponse(
        LocalDate day,
        int alertCount,
        int reminderCount,
        int hydrationCount
) {
}

