package com.badhabinot.monitoring.application.dto;

import java.time.Instant;
import java.util.List;

public record DashboardResponse(
        boolean monitoringActive,
        String activeSessionId,
        String modelMode,
        String privacyMode,
        int streakDays,
        int alertCountToday,
        int reminderCountToday,
        int waterProgressMl,
        int waterGoalMl,
        ActivityItemResponse latestActivity,
        List<ActivityItemResponse> recentActivities,
        Instant generatedAt
) {
}

