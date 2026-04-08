package com.badhabinot.backend.dto.monitoring;

import java.time.LocalDate;

public record WeeklyTrendPointResponse(
        LocalDate day,
        int alertCount,
        int reminderCount,
        int hydrationCount
) {
}


