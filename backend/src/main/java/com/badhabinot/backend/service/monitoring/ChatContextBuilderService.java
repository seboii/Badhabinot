package com.badhabinot.backend.service.monitoring;

import com.badhabinot.backend.dto.monitoring.AiChatRequest;
import com.badhabinot.backend.dto.monitoring.DailyReportResponse;
import com.badhabinot.backend.dto.monitoring.InternalUserAnalysisContext;
import com.badhabinot.backend.model.monitoring.BehaviorEvent;
import com.badhabinot.backend.model.monitoring.DailyReport;
import com.badhabinot.backend.model.monitoring.HydrationLog;
import com.badhabinot.backend.model.monitoring.MonitoringSession;
import com.badhabinot.backend.model.monitoring.ReminderEvent;
import com.badhabinot.backend.repository.monitoring.BehaviorEventRepository;
import com.badhabinot.backend.repository.monitoring.DailyReportRepository;
import com.badhabinot.backend.repository.monitoring.HydrationLogRepository;
import com.badhabinot.backend.repository.monitoring.MonitoringSessionRepository;
import com.badhabinot.backend.repository.monitoring.ReminderEventRepository;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.time.Duration;
import java.time.Instant;
import java.time.LocalDate;
import java.time.ZoneId;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.stream.Collectors;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Service;

@Service
public class ChatContextBuilderService {

    private static final TypeReference<Map<String, Object>> MAP_TYPE = new TypeReference<>() {
    };

    private final BehaviorEventRepository behaviorEventRepository;
    private final ReminderEventRepository reminderEventRepository;
    private final DailyReportRepository dailyReportRepository;
    private final MonitoringSessionRepository monitoringSessionRepository;
    private final HydrationLogRepository hydrationLogRepository;
    private final ObjectMapper objectMapper;

    public ChatContextBuilderService(
            BehaviorEventRepository behaviorEventRepository,
            ReminderEventRepository reminderEventRepository,
            DailyReportRepository dailyReportRepository,
            MonitoringSessionRepository monitoringSessionRepository,
            HydrationLogRepository hydrationLogRepository,
            ObjectMapper objectMapper
    ) {
        this.behaviorEventRepository = behaviorEventRepository;
        this.reminderEventRepository = reminderEventRepository;
        this.dailyReportRepository = dailyReportRepository;
        this.monitoringSessionRepository = monitoringSessionRepository;
        this.hydrationLogRepository = hydrationLogRepository;
        this.objectMapper = objectMapper;
    }

    public AiChatRequest.Context build(
            UUID userId,
            InternalUserAnalysisContext userContext,
            LocalDate reportDate,
            DailyReportResponse currentReport
    ) {
        ZoneId zoneId = zoneId(userContext.timezone());
        LocalDate fromDate = reportDate.minusDays(6);
        Instant rangeStart = fromDate.atStartOfDay(zoneId).toInstant();
        Instant rangeEnd = reportDate.plusDays(1).atStartOfDay(zoneId).toInstant();

        List<BehaviorEvent> recentEvents = behaviorEventRepository.findByUserIdOrderByOccurredAtDesc(
                userId,
                PageRequest.of(0, 20)
        );
        List<ReminderEvent> recentReminders = reminderEventRepository.findByUserIdOrderByOccurredAtDesc(
                userId,
                PageRequest.of(0, 16)
        );
        List<MonitoringSession> recentSessions = monitoringSessionRepository.findByUserIdOrderByStartedAtDesc(
                userId,
                PageRequest.of(0, 12)
        );
        List<HydrationLog> hydrationLogsLast7Days = hydrationLogRepository.findByUserIdAndOccurredAtBetweenOrderByOccurredAtAsc(
                userId,
                rangeStart,
                rangeEnd
        );

        List<DailyReport> reportHistory = dailyReportRepository.findByUserIdAndReportDateBetweenOrderByReportDateDesc(
                userId,
                fromDate,
                reportDate
        );
        List<AiChatRequest.DailySnapshot> dailySnapshots = reportHistory.stream()
                .sorted(Comparator.comparing(DailyReport::getReportDate).reversed())
                .limit(7)
                .map(this::toDailySnapshot)
                .toList();

        DailyReport previousReport = dailyReportRepository.findFirstByUserIdAndReportDateBeforeOrderByReportDateDesc(
                        userId,
                        reportDate
                )
                .orElse(null);

        Map<String, Integer> recentEventTypeCounts = toCountMap(
                recentEvents.stream()
                        .map(BehaviorEvent::getEventType)
                        .toList()
        );
        Map<String, Integer> recentReminderTypeCounts = toCountMap(
                recentReminders.stream()
                        .map(ReminderEvent::getReminderType)
                        .toList()
        );

        int totalSessionsLast7Days = (int) recentSessions.stream()
                .filter(session -> !session.getStartedAt().isBefore(rangeStart) && session.getStartedAt().isBefore(rangeEnd))
                .count();
        int totalSessionMinutesLast7Days = recentSessions.stream()
                .filter(session -> !session.getStartedAt().isBefore(rangeStart) && session.getStartedAt().isBefore(rangeEnd))
                .mapToInt(session -> (int) sessionDurationMinutes(session))
                .sum();
        int hydrationLast7DaysMl = hydrationLogsLast7Days.stream().mapToInt(HydrationLog::getAmountMl).sum();
        int analysesCompletedLast7Days = reportHistory.stream().mapToInt(DailyReport::getAnalysesCompleted).sum();

        List<String> dataGaps = buildDataGaps(currentReport, reportHistory, recentEvents, recentReminders, recentSessions);
        String comparison = comparisonToPreviousDay(currentReport, previousReport);

        List<AiChatRequest.Fact> facts = buildFacts(
                currentReport,
                analysesCompletedLast7Days,
                hydrationLast7DaysMl,
                totalSessionsLast7Days,
                totalSessionMinutesLast7Days,
                comparison
        );

        return new AiChatRequest.Context(
                currentReport.hydrationProgressMl(),
                currentReport.waterGoalMl(),
                currentReport.analysesCompleted(),
                currentReport.postureAlertCount(),
                currentReport.handMovementCount(),
                currentReport.smokingLikeCount(),
                currentReport.reminderCount(),
                currentReport.poorPostureRatio(),
                currentReport.summary(),
                currentReport.recommendations(),
                facts,
                recentEvents.stream().map(this::toEvent).toList(),
                recentReminders.stream().map(this::toReminder).toList(),
                dailySnapshots,
                recentEventTypeCounts,
                recentReminderTypeCounts,
                recentSessions.stream().map(this::toSessionSnapshot).toList(),
                totalSessionsLast7Days,
                totalSessionMinutesLast7Days,
                hydrationLast7DaysMl,
                analysesCompletedLast7Days,
                comparison,
                dataGaps
        );
    }

    private List<AiChatRequest.Fact> buildFacts(
            DailyReportResponse currentReport,
            int analysesCompletedLast7Days,
            int hydrationLast7DaysMl,
            int totalSessionsLast7Days,
            int totalSessionMinutesLast7Days,
            String comparison
    ) {
        return List.of(
                new AiChatRequest.Fact("report_date", currentReport.reportDate().toString()),
                new AiChatRequest.Fact("hydration_progress_ml", String.valueOf(currentReport.hydrationProgressMl())),
                new AiChatRequest.Fact("water_goal_ml", String.valueOf(currentReport.waterGoalMl())),
                new AiChatRequest.Fact("posture_alert_count", String.valueOf(currentReport.postureAlertCount())),
                new AiChatRequest.Fact("hand_movement_count", String.valueOf(currentReport.handMovementCount())),
                new AiChatRequest.Fact("smoking_like_count", String.valueOf(currentReport.smokingLikeCount())),
                new AiChatRequest.Fact("analyses_completed_last_7_days", String.valueOf(analysesCompletedLast7Days)),
                new AiChatRequest.Fact("hydration_last_7_days_ml", String.valueOf(hydrationLast7DaysMl)),
                new AiChatRequest.Fact("total_sessions_last_7_days", String.valueOf(totalSessionsLast7Days)),
                new AiChatRequest.Fact("total_session_minutes_last_7_days", String.valueOf(totalSessionMinutesLast7Days)),
                new AiChatRequest.Fact("comparison_to_previous_day", comparison)
        );
    }

    private List<String> buildDataGaps(
            DailyReportResponse currentReport,
            List<DailyReport> reportHistory,
            List<BehaviorEvent> events,
            List<ReminderEvent> reminders,
            List<MonitoringSession> sessions
    ) {
        List<String> gaps = new ArrayList<>();
        if (currentReport.analysesCompleted() == 0) {
            gaps.add("No analysis frames were processed for the requested day.");
        }
        if (reportHistory.size() < 2) {
            gaps.add("Historical comparison is limited because fewer than two daily reports are available.");
        }
        if (events.isEmpty()) {
            gaps.add("Recent behavior event history is empty.");
        }
        if (reminders.isEmpty()) {
            gaps.add("No recent reminder history is available.");
        }
        if (sessions.isEmpty()) {
            gaps.add("No monitoring session history is available.");
        }
        return gaps;
    }

    private String comparisonToPreviousDay(DailyReportResponse currentReport, DailyReport previousReport) {
        if (previousReport == null) {
            return "No previous daily report exists for direct day-over-day comparison.";
        }
        int postureDelta = currentReport.postureAlertCount() - previousReport.getPostureAlertCount();
        int hydrationDelta = currentReport.hydrationProgressMl() - previousReport.getHydrationProgressMl();
        int smokingDelta = currentReport.smokingLikeCount() - previousReport.getSmokingLikeCount();

        return String.format(
                "Compared with %s: posture alerts %+d, hydration %+d ml, smoking-like cues %+d.",
                previousReport.getReportDate(),
                postureDelta,
                hydrationDelta,
                smokingDelta
        );
    }

    private Map<String, Integer> toCountMap(List<String> values) {
        return values.stream()
                .collect(Collectors.toMap(
                        value -> value,
                        value -> 1,
                        Integer::sum,
                        LinkedHashMap::new
                ));
    }

    private AiChatRequest.Event toEvent(BehaviorEvent event) {
        return new AiChatRequest.Event(
                event.getEventType(),
                event.getConfidence().doubleValue(),
                event.getSeverity(),
                event.getInterpretation(),
                event.getOccurredAt(),
                readMap(event.getEvidenceJson())
        );
    }

    private AiChatRequest.Reminder toReminder(ReminderEvent reminder) {
        return new AiChatRequest.Reminder(
                reminder.getReminderType(),
                reminder.getMessage(),
                reminder.getTriggerReason(),
                reminder.getOccurredAt()
        );
    }

    private AiChatRequest.DailySnapshot toDailySnapshot(DailyReport report) {
        return new AiChatRequest.DailySnapshot(
                report.getReportDate(),
                report.getAnalysesCompleted(),
                report.getPostureAlertCount(),
                report.getHandMovementCount(),
                report.getSmokingLikeCount(),
                report.getReminderCount(),
                report.getHydrationProgressMl(),
                report.getWaterGoalMl(),
                report.getPoorPostureRatio().doubleValue(),
                report.getSummary()
        );
    }

    private AiChatRequest.SessionSnapshot toSessionSnapshot(MonitoringSession session) {
        return new AiChatRequest.SessionSnapshot(
                session.getId().toString(),
                session.getStatus().name(),
                session.getStartedAt(),
                session.getEndedAt(),
                sessionDurationMinutes(session)
        );
    }

    private long sessionDurationMinutes(MonitoringSession session) {
        Instant end = session.getEndedAt() == null ? Instant.now() : session.getEndedAt();
        return Math.max(0, Duration.between(session.getStartedAt(), end).toMinutes());
    }

    private Map<String, Object> readMap(String payload) {
        try {
            return objectMapper.readValue(payload, MAP_TYPE);
        } catch (Exception exception) {
            return Map.of();
        }
    }

    private ZoneId zoneId(String timezone) {
        try {
            return ZoneId.of(timezone);
        } catch (RuntimeException exception) {
            return ZoneId.of("UTC");
        }
    }
}

