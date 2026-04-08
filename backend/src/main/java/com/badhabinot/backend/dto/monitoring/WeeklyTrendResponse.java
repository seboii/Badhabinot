package com.badhabinot.backend.dto.monitoring;

import java.time.LocalDate;
import java.util.List;

public record WeeklyTrendResponse(
        LocalDate from,
        LocalDate to,
        List<WeeklyTrendPointResponse> points
) {
}

