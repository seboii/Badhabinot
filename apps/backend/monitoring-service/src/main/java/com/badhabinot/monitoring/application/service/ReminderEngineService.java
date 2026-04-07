package com.badhabinot.monitoring.application.service;

import com.badhabinot.monitoring.application.dto.BehaviorEventResponse;
import com.badhabinot.monitoring.application.dto.InternalUserAnalysisContext;
import com.badhabinot.monitoring.application.dto.ReminderEventResponse;
import com.badhabinot.monitoring.domain.model.ActivityCategory;
import com.badhabinot.monitoring.domain.model.ActivityFeedItem;
import com.badhabinot.monitoring.domain.model.HydrationLog;
import com.badhabinot.monitoring.domain.model.ReminderEvent;
import com.badhabinot.monitoring.domain.repository.ActivityFeedRepository;
import com.badhabinot.monitoring.domain.repository.HydrationLogRepository;
import com.badhabinot.monitoring.domain.repository.ReminderEventRepository;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.time.Duration;
import java.time.Instant;
import java.time.LocalTime;
import java.time.ZoneId;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class ReminderEngineService {

    private static final TypeReference<Map<String, Object>> MAP_TYPE = new TypeReference<>() {
    };

    private final ReminderEventRepository reminderEventRepository;
    private final ActivityFeedRepository activityFeedRepository;
    private final HydrationLogRepository hydrationLogRepository;
    private final ObjectMapper objectMapper;

    public ReminderEngineService(
            ReminderEventRepository reminderEventRepository,
            ActivityFeedRepository activityFeedRepository,
            HydrationLogRepository hydrationLogRepository,
            ObjectMapper objectMapper
    ) {
        this.reminderEventRepository = reminderEventRepository;
        this.activityFeedRepository = activityFeedRepository;
        this.hydrationLogRepository = hydrationLogRepository;
        this.objectMapper = objectMapper;
    }

    @Transactional
    public List<ReminderEventResponse> evaluateAfterAnalysis(
            UUID userId,
            UUID sessionId,
            InternalUserAnalysisContext context,
            Instant occurredAt,
            List<BehaviorEventResponse> events
    ) {
        if (!context.notificationsEnabled() || isQuietHours(context, occurredAt)) {
            return List.of();
        }

        List<ReminderEventResponse> reminders = new ArrayList<>();
        maybeCreateHydrationReminder(userId, sessionId, context, occurredAt).ifPresent(reminders::add);

        events.stream()
                .filter(event -> "poor_posture".equals(event.eventType()))
                .findFirst()
                .flatMap(event -> maybeCreatePostureReminder(userId, sessionId, context, occurredAt, event))
                .ifPresent(reminders::add);

        events.stream()
                .filter(event -> "smoking_like_gesture".equals(event.eventType()) && event.confidence() >= 0.55)
                .findFirst()
                .flatMap(event -> maybeCreateMindfulBreakReminder(userId, sessionId, context, occurredAt, event))
                .ifPresent(reminders::add);

        return reminders;
    }

    @Transactional
    public ReminderEventResponse recordManualReminder(
            UUID userId,
            UUID sessionId,
            String reminderType,
            String message,
            Instant occurredAt
    ) {
        String normalizedType = reminderType == null ? "general_reminder" : reminderType.trim().toLowerCase();
        return createReminder(
                userId,
                sessionId,
                normalizedType,
                "manual",
                "low",
                message == null || message.isBlank() ? defaultMessage(normalizedType) : message,
                "Manual reminder trigger from the client surface.",
                Map.of("manual", true),
                occurredAt
        );
    }

    @Transactional(readOnly = true)
    public List<ReminderEventResponse> getRecentReminders(UUID userId, int limit) {
        return reminderEventRepository.findByUserIdOrderByOccurredAtDesc(userId, PageRequest.of(0, Math.max(1, Math.min(limit, 20))))
                .stream()
                .map(this::toResponse)
                .toList();
    }

    private Optional<ReminderEventResponse> maybeCreateHydrationReminder(
            UUID userId,
            UUID sessionId,
            InternalUserAnalysisContext context,
            Instant occurredAt
    ) {
        Optional<HydrationLog> latestHydration = hydrationLogRepository.findFirstByUserIdOrderByOccurredAtDesc(userId);
        if (latestHydration.isPresent()
                && Duration.between(latestHydration.get().getOccurredAt(), occurredAt).toMinutes() < context.waterIntervalMin()) {
            return Optional.empty();
        }
        if (!cooldownElapsed(userId, "water_reminder", occurredAt, context.waterIntervalMin())) {
            return Optional.empty();
        }
        return Optional.of(createReminder(
                userId,
                sessionId,
                "water_reminder",
                "scheduled",
                "medium",
                "Time for water. You are approaching the hydration reminder interval.",
                "Hydration interval threshold elapsed without a recent water log.",
                Map.of(
                        "water_interval_min", context.waterIntervalMin(),
                        "water_goal_ml", context.waterGoalMl()
                ),
                occurredAt
        ));
    }

    private Optional<ReminderEventResponse> maybeCreatePostureReminder(
            UUID userId,
            UUID sessionId,
            InternalUserAnalysisContext context,
            Instant occurredAt,
            BehaviorEventResponse event
    ) {
        if (!cooldownElapsed(userId, "posture_reminder", occurredAt, context.exerciseIntervalMin())) {
            return Optional.empty();
        }
        return Optional.of(createReminder(
                userId,
                sessionId,
                "posture_reminder",
                "event_based",
                event.severity(),
                "Posture reset recommended. Sit back, uncurl the shoulders, and align the screen with eye level.",
                "Poor posture was detected above the reminder threshold.",
                Map.of(
                        "source_event_id", event.eventId().toString(),
                        "confidence", event.confidence()
                ),
                occurredAt
        ));
    }

    private Optional<ReminderEventResponse> maybeCreateMindfulBreakReminder(
            UUID userId,
            UUID sessionId,
            InternalUserAnalysisContext context,
            Instant occurredAt,
            BehaviorEventResponse event
    ) {
        if (!cooldownElapsed(userId, "mindful_break_reminder", occurredAt, context.exerciseIntervalMin())) {
            return Optional.empty();
        }
        return Optional.of(createReminder(
                userId,
                sessionId,
                "mindful_break_reminder",
                "event_based",
                event.severity(),
                "Take a short break, breathe, and review what triggered the smoking-like cue.",
                "A smoking-like gesture was detected and crossed the coaching threshold.",
                Map.of(
                        "source_event_id", event.eventId().toString(),
                        "confidence", event.confidence()
                ),
                occurredAt
        ));
    }

    private ReminderEventResponse createReminder(
            UUID userId,
            UUID sessionId,
            String reminderType,
            String source,
            String severity,
            String message,
            String triggerReason,
            Map<String, Object> metadata,
            Instant occurredAt
    ) {
        ReminderEvent reminderEvent = reminderEventRepository.save(ReminderEvent.create(
                userId,
                sessionId,
                reminderType,
                source,
                severity,
                message,
                triggerReason,
                writeJson(metadata),
                occurredAt
        ));

        activityFeedRepository.save(ActivityFeedItem.create(
                userId,
                sessionId,
                reminderType,
                ActivityCategory.REMINDER,
                titleFor(reminderType),
                message,
                null,
                occurredAt
        ));

        return toResponse(reminderEvent);
    }

    private boolean cooldownElapsed(UUID userId, String reminderType, Instant occurredAt, int cooldownMinutes) {
        return reminderEventRepository.findFirstByUserIdAndReminderTypeOrderByOccurredAtDesc(userId, reminderType)
                .map(event -> Duration.between(event.getOccurredAt(), occurredAt).toMinutes() >= cooldownMinutes)
                .orElse(true);
    }

    private boolean isQuietHours(InternalUserAnalysisContext context, Instant occurredAt) {
        if (!context.quietHoursEnabled()) {
            return false;
        }

        ZoneId zoneId = zoneId(context.timezone());
        LocalTime currentTime = occurredAt.atZone(zoneId).toLocalTime();
        LocalTime start = parseTime(context.quietHoursStart());
        LocalTime end = parseTime(context.quietHoursEnd());

        if (start.equals(end)) {
            return true;
        }
        if (start.isBefore(end)) {
            return !currentTime.isBefore(start) && currentTime.isBefore(end);
        }
        return !currentTime.isBefore(start) || currentTime.isBefore(end);
    }

    public ReminderEventResponse toResponse(ReminderEvent reminderEvent) {
        return new ReminderEventResponse(
                reminderEvent.getId(),
                reminderEvent.getSessionId() == null ? null : reminderEvent.getSessionId().toString(),
                reminderEvent.getReminderType(),
                reminderEvent.getSource(),
                reminderEvent.getSeverity(),
                reminderEvent.getMessage(),
                reminderEvent.getTriggerReason(),
                readJson(reminderEvent.getMetadataJson()),
                reminderEvent.getOccurredAt()
        );
    }

    private String titleFor(String reminderType) {
        return switch (reminderType) {
            case "water_reminder" -> "Hydration reminder";
            case "posture_reminder" -> "Posture reminder";
            case "mindful_break_reminder" -> "Mindful break reminder";
            default -> "Reminder";
        };
    }

    private String defaultMessage(String reminderType) {
        return switch (reminderType) {
            case "water_reminder" -> "Time for water.";
            case "posture_reminder" -> "Reset your posture for a moment.";
            case "break_reminder", "mindful_break_reminder" -> "Stand up and take a short break.";
            default -> "Reminder triggered.";
        };
    }

    private ZoneId zoneId(String timezone) {
        try {
            return ZoneId.of(timezone);
        } catch (RuntimeException exception) {
            return ZoneId.of("UTC");
        }
    }

    private LocalTime parseTime(String value) {
        try {
            return LocalTime.parse(value);
        } catch (RuntimeException exception) {
            return LocalTime.of(22, 0);
        }
    }

    private String writeJson(Map<String, Object> payload) {
        try {
            return objectMapper.writeValueAsString(payload);
        } catch (Exception exception) {
            return "{}";
        }
    }

    private Map<String, Object> readJson(String payload) {
        try {
            return objectMapper.readValue(payload, MAP_TYPE);
        } catch (Exception exception) {
            return Map.of();
        }
    }
}
