package com.badhabinot.backend.service.monitoring;

import com.badhabinot.backend.dto.monitoring.ActivityItemResponse;
import com.badhabinot.backend.dto.monitoring.BehaviorEventResponse;
import com.badhabinot.backend.dto.monitoring.DailyReportResponse;
import com.badhabinot.backend.dto.monitoring.InternalUserAnalysisContext;
import com.badhabinot.backend.dto.monitoring.ReminderEventResponse;
import com.badhabinot.backend.model.monitoring.ActivityFeedItem;
import com.badhabinot.backend.model.monitoring.AnalysisJob;
import com.badhabinot.backend.model.monitoring.BehaviorEvent;
import com.badhabinot.backend.model.monitoring.DailyReport;
import com.badhabinot.backend.model.monitoring.HydrationLog;
import com.badhabinot.backend.model.monitoring.ReminderEvent;
import com.badhabinot.backend.repository.monitoring.ActivityFeedRepository;
import com.badhabinot.backend.repository.monitoring.AnalysisJobRepository;
import com.badhabinot.backend.repository.monitoring.BehaviorEventRepository;
import com.badhabinot.backend.repository.monitoring.DailyReportRepository;
import com.badhabinot.backend.repository.monitoring.HydrationLogRepository;
import com.badhabinot.backend.repository.monitoring.ReminderEventRepository;
import com.badhabinot.backend.service.user.UserContextService;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.time.Instant;
import java.time.LocalDate;
import java.time.ZoneId;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import org.springframework.security.oauth2.jwt.Jwt;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class DailyReportService {

    private static final TypeReference<List<String>> STRING_LIST = new TypeReference<>() {
    };
    private static final TypeReference<Map<String, Object>> MAP_TYPE = new TypeReference<>() {
    };

    private final DailyReportRepository dailyReportRepository;
    private final BehaviorEventRepository behaviorEventRepository;
    private final ReminderEventRepository reminderEventRepository;
    private final HydrationLogRepository hydrationLogRepository;
    private final ActivityFeedRepository activityFeedRepository;
    private final AnalysisJobRepository analysisJobRepository;
    private final UserContextService userContextService;
    private final BehaviorEventService behaviorEventService;
    private final ReminderEngineService reminderEngineService;
    private final ObjectMapper objectMapper;

    public DailyReportService(
            DailyReportRepository dailyReportRepository,
            BehaviorEventRepository behaviorEventRepository,
            ReminderEventRepository reminderEventRepository,
            HydrationLogRepository hydrationLogRepository,
            ActivityFeedRepository activityFeedRepository,
            AnalysisJobRepository analysisJobRepository,
            UserContextService userContextService,
            BehaviorEventService behaviorEventService,
            ReminderEngineService reminderEngineService,
            ObjectMapper objectMapper
    ) {
        this.dailyReportRepository = dailyReportRepository;
        this.behaviorEventRepository = behaviorEventRepository;
        this.reminderEventRepository = reminderEventRepository;
        this.hydrationLogRepository = hydrationLogRepository;
        this.activityFeedRepository = activityFeedRepository;
        this.analysisJobRepository = analysisJobRepository;
        this.userContextService = userContextService;
        this.behaviorEventService = behaviorEventService;
        this.reminderEngineService = reminderEngineService;
        this.objectMapper = objectMapper;
    }

    @Transactional(transactionManager = "monitoringTransactionManager")
    public DailyReportResponse getDailyReport(Jwt jwt, LocalDate requestedDate) {
        UUID userId = UUID.fromString(jwt.getSubject());
        InternalUserAnalysisContext context = userContextService.getMonitoringAnalysisContext(userId);
        LocalDate reportDate = requestedDate == null ? LocalDate.now(zoneId(context.timezone())) : requestedDate;
        return getDailyReport(userId, reportDate, context);
    }

    @Transactional(transactionManager = "monitoringTransactionManager")
    public DailyReportResponse getDailyReport(UUID userId, LocalDate reportDate, InternalUserAnalysisContext context) {
        ZoneId zoneId = zoneId(context.timezone());
        Instant dayStart = reportDate.atStartOfDay(zoneId).toInstant();
        Instant dayEnd = reportDate.plusDays(1).atStartOfDay(zoneId).toInstant();

        List<AnalysisJob> analyses = analysisJobRepository.findByUserIdAndCreatedAtBetweenOrderByCreatedAtAsc(userId, dayStart, dayEnd);
        List<BehaviorEvent> events = behaviorEventRepository.findByUserIdAndOccurredAtBetweenOrderByOccurredAtAsc(userId, dayStart, dayEnd);
        List<ReminderEvent> reminders = reminderEventRepository.findByUserIdAndOccurredAtBetweenOrderByOccurredAtAsc(userId, dayStart, dayEnd);
        List<HydrationLog> hydrationLogs = hydrationLogRepository.findByUserIdAndOccurredAtBetweenOrderByOccurredAtAsc(userId, dayStart, dayEnd);
        List<ActivityFeedItem> timeline = activityFeedRepository.findByUserIdAndOccurredAtBetweenOrderByOccurredAtAsc(userId, dayStart, dayEnd);

        int postureAlertCount = (int) events.stream().filter(event -> "poor_posture".equals(event.getEventType())).count();
        int handMovementCount = (int) events.stream().filter(event -> "hand_movement_pattern".equals(event.getEventType())).count();
        int smokingLikeCount = (int) events.stream().filter(event -> "smoking_like_gesture".equals(event.getEventType())).count();
        int reminderCount = reminders.size();
        int hydrationProgressMl = hydrationLogs.stream().mapToInt(HydrationLog::getAmountMl).sum();
        long poorPostureFrames = analyses.stream().filter(job -> "poor".equalsIgnoreCase(job.getPostureState())).count();
        double poorPostureRatio = analyses.isEmpty() ? 0.0 : (double) poorPostureFrames / analyses.size();

        List<String> recommendations = buildRecommendations(
                postureAlertCount,
                handMovementCount,
                smokingLikeCount,
                hydrationProgressMl,
                context.waterGoalMl(),
                poorPostureRatio
        );
        String summary = buildSummary(
                analyses.size(),
                postureAlertCount,
                handMovementCount,
                smokingLikeCount,
                reminderCount,
                hydrationProgressMl,
                context.waterGoalMl(),
                poorPostureRatio
        );

        DailyReport report = dailyReportRepository.findByUserIdAndReportDate(userId, reportDate)
                .orElseGet(() -> DailyReport.create(userId, reportDate));
        report.refresh(
                analyses.size(),
                postureAlertCount,
                handMovementCount,
                smokingLikeCount,
                reminderCount,
                hydrationProgressMl,
                context.waterGoalMl(),
                poorPostureRatio,
                summary,
                writeJson(recommendations),
                Instant.now()
        );
        report = dailyReportRepository.save(report);

        List<BehaviorEventResponse> keyEvents = events.stream()
                .sorted(Comparator.comparing(BehaviorEvent::getOccurredAt).reversed()
                        .thenComparing(event -> event.getConfidence().doubleValue(), Comparator.reverseOrder()))
                .limit(8)
                .map(behaviorEventService::toResponse)
                .toList();

        List<ReminderEventResponse> reminderResponses = reminders.stream()
                .sorted(Comparator.comparing(ReminderEvent::getOccurredAt).reversed())
                .limit(8)
                .map(reminderEngineService::toResponse)
                .toList();

        return new DailyReportResponse(
                report.getId(),
                reportDate,
                analyses.size(),
                postureAlertCount,
                handMovementCount,
                smokingLikeCount,
                reminderCount,
                hydrationProgressMl,
                context.waterGoalMl(),
                round(poorPostureRatio),
                report.getSummary(),
                readStringList(report.getRecommendationsJson()),
                keyEvents,
                reminderResponses,
                timeline.stream().sorted(Comparator.comparing(ActivityFeedItem::getOccurredAt).reversed()).limit(20).map(this::toActivityResponse).toList(),
                report.getGeneratedAt()
        );
    }

    private List<String> buildRecommendations(
            int postureAlertCount,
            int handMovementCount,
            int smokingLikeCount,
            int hydrationProgressMl,
            int waterGoalMl,
            double poorPostureRatio
    ) {
        List<String> recommendations = new ArrayList<>();
        if (postureAlertCount > 0 || poorPostureRatio >= 0.35) {
            recommendations.add("Schedule a posture reset every 30 to 45 minutes and lift the display closer to eye level.");
        }
        if (handMovementCount >= 3) {
            recommendations.add("Keep hands occupied with a low-friction substitute to reduce repetitive hand-to-face movement.");
        }
        if (smokingLikeCount > 0) {
            recommendations.add("Review the times of the smoking-like cues and log what was happening immediately before them.");
        }
        if (hydrationProgressMl < (waterGoalMl * 0.7)) {
            recommendations.add("Hydration stayed below the daily target. Add a water checkpoint earlier in the work block.");
        }
        if (recommendations.isEmpty()) {
            recommendations.add("The tracked patterns stayed stable today. Keep the same monitoring cadence tomorrow.");
        }
        return recommendations;
    }

    private String buildSummary(
            int analysesCompleted,
            int postureAlertCount,
            int handMovementCount,
            int smokingLikeCount,
            int reminderCount,
            int hydrationProgressMl,
            int waterGoalMl,
            double poorPostureRatio
    ) {
        return String.format(
                "The system processed %d analysis frames today. It recorded %d posture alerts, %d hand-movement events, %d smoking-like cues, and %d reminders. Hydration reached %d of %d ml, and poor-posture frames accounted for %.0f%% of analyzed captures.",
                analysesCompleted,
                postureAlertCount,
                handMovementCount,
                smokingLikeCount,
                reminderCount,
                hydrationProgressMl,
                waterGoalMl,
                poorPostureRatio * 100
        );
    }

    private ActivityItemResponse toActivityResponse(ActivityFeedItem item) {
        return new ActivityItemResponse(
                item.getId(),
                item.getActivityType(),
                item.getCategory().name(),
                item.getTitle(),
                item.getMessage(),
                item.getConfidence() == null ? null : item.getConfidence().doubleValue(),
                item.getOccurredAt()
        );
    }

    private ZoneId zoneId(String timezone) {
        try {
            return ZoneId.of(timezone);
        } catch (RuntimeException exception) {
            return ZoneId.of("UTC");
        }
    }

    private String writeJson(List<String> values) {
        try {
            return objectMapper.writeValueAsString(values);
        } catch (Exception exception) {
            return "[]";
        }
    }

    private List<String> readStringList(String payload) {
        try {
            return objectMapper.readValue(payload, STRING_LIST);
        } catch (Exception exception) {
            return List.of();
        }
    }

    private double round(double value) {
        return Math.round(value * 10_000.0) / 10_000.0;
    }
}

