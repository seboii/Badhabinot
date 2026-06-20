package com.badhabinot.backend.dto.admin;

import java.time.Instant;
import java.time.LocalDate;

/** Admin için bir kullanıcının günlük rapor özeti. */
public record AdminReportSummary(
        LocalDate reportDate,
        int analysesCompleted,
        int postureAlertCount,
        int handMovementCount,
        int smokingLikeCount,
        int reminderCount,
        int hydrationProgressMl,
        int waterGoalMl,
        double poorPostureRatio,
        String summary,
        Instant generatedAt
) {
}
