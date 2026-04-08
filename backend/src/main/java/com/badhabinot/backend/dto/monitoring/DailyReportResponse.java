package com.badhabinot.backend.dto.monitoring;

import java.time.Instant;
import java.time.LocalDate;
import java.util.List;
import java.util.UUID;

public record DailyReportResponse(
        UUID reportId,
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
        List<String> recommendations,
        List<BehaviorEventResponse> keyBehaviorEvents,
        List<ReminderEventResponse> reminders,
        List<ActivityItemResponse> timeline,
        Instant generatedAt
) {
}

