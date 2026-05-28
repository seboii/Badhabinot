package com.badhabinot.backend.dto.monitoring;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.time.Instant;
import java.time.LocalDate;
import java.util.List;
import java.util.Map;

public record AiChatRequest(
        String conversationId,
        String userId,
        String timezone,
        LocalDate reportDate,
        String message,
        List<Message> history,
        Context context,
        String aiMode,
        String localModelName,
        String ollamaBaseUrl,
        String chatPersona,
        String customSystemPrompt
) {
    public record Message(
            String role,
            String content,
            Instant createdAt
    ) {
    }

    public record Context(
            int hydrationProgressMl,
            int waterGoalMl,
            int analysesCompleted,
            int postureAlertCount,
            int handMovementCount,
            int smokingLikeCount,
            int reminderCount,
            double poorPostureRatio,
            String summary,
            List<String> recommendations,
            List<Fact> facts,
            List<Event> recentEvents,
            List<Reminder> recentReminders,
            List<DailySnapshot> recentDailySnapshots,
            Map<String, Integer> recentEventTypeCounts,
            Map<String, Integer> recentReminderTypeCounts,
            List<SessionSnapshot> recentSessions,
            @JsonProperty("total_sessions_last_7_days") int totalSessionsLast7Days,
            @JsonProperty("total_session_minutes_last_7_days") int totalSessionMinutesLast7Days,
            @JsonProperty("hydration_last_7_days_ml") int hydrationLast7DaysMl,
            @JsonProperty("analyses_completed_last_7_days") int analysesCompletedLast7Days,
            String comparisonToPreviousDay,
            List<String> dataGaps,
            List<BehavioralPattern> behavioralPatterns
    ) {
    }

    public record BehavioralPattern(
            String eventType,
            int peakHourOfDay,
            int peakHourCount,
            String peakDayOfWeek,
            int peakDayCount,
            @JsonProperty("total_count_last_7_days") int totalCountLast7Days,
            String intensityLabel,
            String trendLabel
    ) {
    }

    public record Fact(
            String label,
            String value
    ) {
    }

    public record Event(
            String eventType,
            double confidence,
            String severity,
            String interpretation,
            Instant occurredAt,
            Map<String, Object> evidence
    ) {
    }

    public record Reminder(
            String reminderType,
            String message,
            String triggerReason,
            Instant occurredAt
    ) {
    }

    public record DailySnapshot(
            LocalDate reportDate,
            int analysesCompleted,
            int postureAlertCount,
            int handMovementCount,
            int smokingLikeCount,
            int reminderCount,
            int hydrationProgressMl,
            int waterGoalMl,
            double poorPostureRatio,
            String summary
    ) {
    }

    public record SessionSnapshot(
            String sessionId,
            String status,
            Instant startedAt,
            Instant endedAt,
            long durationMinutes
    ) {
    }
}

