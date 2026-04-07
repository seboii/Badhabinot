package com.badhabinot.monitoring.application.dto;

public record InternalUserAnalysisContext(
        String userId,
        String timezone,
        String sensitivity,
        String modelMode,
        boolean cameraMonitoringAccepted,
        int waterGoalMl,
        int waterIntervalMin,
        int exerciseIntervalMin,
        boolean notificationsEnabled,
        boolean quietHoursEnabled,
        String quietHoursStart,
        String quietHoursEnd,
        boolean remoteInferenceAccepted
) {
}
