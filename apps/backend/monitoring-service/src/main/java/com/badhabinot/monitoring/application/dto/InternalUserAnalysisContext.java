package com.badhabinot.monitoring.application.dto;

public record InternalUserAnalysisContext(
        String userId,
        String timezone,
        String sensitivity,
        String modelMode,
        int waterGoalMl,
        boolean notificationsEnabled,
        boolean quietHoursEnabled,
        String quietHoursStart,
        String quietHoursEnd,
        boolean remoteInferenceAccepted
) {
}
