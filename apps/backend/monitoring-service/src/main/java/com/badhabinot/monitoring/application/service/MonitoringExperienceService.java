package com.badhabinot.monitoring.application.service;

import com.badhabinot.monitoring.application.dto.ActivityItemResponse;
import com.badhabinot.monitoring.application.dto.DashboardResponse;
import com.badhabinot.monitoring.application.dto.HydrationLogRequest;
import com.badhabinot.monitoring.application.dto.HydrationLogResponse;
import com.badhabinot.monitoring.application.dto.InternalUserAnalysisContext;
import com.badhabinot.monitoring.application.dto.ReminderTriggerRequest;
import com.badhabinot.monitoring.application.dto.SessionStartRequest;
import com.badhabinot.monitoring.application.dto.SessionStartResponse;
import com.badhabinot.monitoring.application.dto.SessionStopResponse;
import com.badhabinot.monitoring.application.dto.WeeklyTrendPointResponse;
import com.badhabinot.monitoring.application.dto.WeeklyTrendResponse;
import com.badhabinot.monitoring.domain.model.ActivityCategory;
import com.badhabinot.monitoring.domain.model.ActivityFeedItem;
import com.badhabinot.monitoring.domain.model.HydrationLog;
import com.badhabinot.monitoring.domain.model.MonitoringSession;
import com.badhabinot.monitoring.domain.model.MonitoringSessionStatus;
import com.badhabinot.monitoring.domain.repository.ActivityFeedRepository;
import com.badhabinot.monitoring.domain.repository.HydrationLogRepository;
import com.badhabinot.monitoring.domain.repository.MonitoringSessionRepository;
import com.badhabinot.monitoring.infrastructure.client.UserContextClient;
import java.time.Instant;
import java.time.LocalDate;
import java.time.ZoneId;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.stream.Collectors;
import org.springframework.data.domain.PageRequest;
import org.springframework.security.oauth2.jwt.Jwt;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class MonitoringExperienceService {

    private final MonitoringSessionRepository monitoringSessionRepository;
    private final ActivityFeedRepository activityFeedRepository;
    private final HydrationLogRepository hydrationLogRepository;
    private final UserContextClient userContextClient;
    private final ReminderEngineService reminderEngineService;

    public MonitoringExperienceService(
            MonitoringSessionRepository monitoringSessionRepository,
            ActivityFeedRepository activityFeedRepository,
            HydrationLogRepository hydrationLogRepository,
            UserContextClient userContextClient,
            ReminderEngineService reminderEngineService
    ) {
        this.monitoringSessionRepository = monitoringSessionRepository;
        this.activityFeedRepository = activityFeedRepository;
        this.hydrationLogRepository = hydrationLogRepository;
        this.userContextClient = userContextClient;
        this.reminderEngineService = reminderEngineService;
    }

    @Transactional
    public SessionStartResponse startSession(Jwt jwt, SessionStartRequest request) {
        UUID userId = UUID.fromString(jwt.getSubject());
        monitoringSessionRepository.findFirstByUserIdAndStatusOrderByStartedAtDesc(userId, MonitoringSessionStatus.ACTIVE)
                .ifPresent(existing -> {
                    existing.stop();
                    monitoringSessionRepository.save(existing);
                });

        MonitoringSession session = monitoringSessionRepository.save(MonitoringSession.start(userId, request.clientSurface(), request.deviceType()));
        activityFeedRepository.save(ActivityFeedItem.create(
                userId,
                session.getId(),
                "monitoring_started",
                ActivityCategory.SYSTEM,
                "Oturum Basladi",
                request.clientSurface() + " istemcisi uzerinden izleme basladi.",
                null,
                session.getStartedAt()
        ));
        return new SessionStartResponse(session.getId().toString(), session.getStatus().name(), session.getStartedAt());
    }

    @Transactional
    public SessionStopResponse stopSession(Jwt jwt, String sessionId) {
        UUID userId = UUID.fromString(jwt.getSubject());
        MonitoringSession session = monitoringSessionRepository.findById(parseSessionId(sessionId))
                .filter(candidate -> candidate.getUserId().equals(userId))
                .orElseThrow(() -> new IllegalArgumentException("Monitoring session not found"));
        session.stop();
        monitoringSessionRepository.save(session);
        activityFeedRepository.save(ActivityFeedItem.create(
                userId,
                session.getId(),
                "monitoring_stopped",
                ActivityCategory.SYSTEM,
                "Oturum Sonlandi",
                "Canli izleme oturumu durduruldu.",
                null,
                session.getEndedAt()
        ));
        return new SessionStopResponse(session.getId().toString(), session.getStatus().name(), session.getEndedAt());
    }

    @Transactional(readOnly = true)
    public DashboardResponse getDashboard(Jwt jwt) {
        UUID userId = UUID.fromString(jwt.getSubject());
        InternalUserAnalysisContext context = userContextClient.fetch(userId);
        ZoneId zoneId = zoneId(context.timezone());
        Instant now = Instant.now();
        LocalDate today = LocalDate.now(zoneId);
        Instant dayStart = today.atStartOfDay(zoneId).toInstant();
        Instant dayEnd = today.plusDays(1).atStartOfDay(zoneId).toInstant();

        var activeSession = monitoringSessionRepository.findFirstByUserIdAndStatusOrderByStartedAtDesc(userId, MonitoringSessionStatus.ACTIVE);
        List<ActivityFeedItem> todayActivities = activityFeedRepository.findByUserIdAndOccurredAtBetweenOrderByOccurredAtAsc(userId, dayStart, dayEnd);
        List<ActivityFeedItem> recent = activityFeedRepository.findByUserIdOrderByOccurredAtDesc(userId, PageRequest.of(0, 5));
        List<HydrationLog> hydrationToday = hydrationLogRepository.findByUserIdAndOccurredAtBetweenOrderByOccurredAtAsc(userId, dayStart, dayEnd);

        int alertCount = (int) todayActivities.stream().filter(item -> item.getCategory() == ActivityCategory.ALERT).count();
        int reminderCount = (int) todayActivities.stream().filter(item -> item.getCategory() == ActivityCategory.REMINDER).count();
        int waterProgressMl = hydrationToday.stream().mapToInt(HydrationLog::getAmountMl).sum();

        ActivityItemResponse latest = recent.isEmpty() ? null : toActivityResponse(recent.getFirst());
        boolean analysisEnabled = context.cameraMonitoringAccepted() && context.remoteInferenceAccepted();
        String privacyMode = analysisEnabled ? "API_CONSENTED" : "CONSENT_REQUIRED";

        return new DashboardResponse(
                activeSession.isPresent(),
                activeSession.map(session -> session.getId().toString()).orElse(null),
                context.modelMode(),
                privacyMode,
                analysisEnabled,
                computeStreakDays(userId, zoneId, today),
                alertCount,
                reminderCount,
                waterProgressMl,
                context.waterGoalMl(),
                latest,
                recent.stream().map(this::toActivityResponse).toList(),
                now
        );
    }

    @Transactional(readOnly = true)
    public List<ActivityItemResponse> getRecentActivities(Jwt jwt, int limit) {
        UUID userId = UUID.fromString(jwt.getSubject());
        return activityFeedRepository.findByUserIdOrderByOccurredAtDesc(userId, PageRequest.of(0, Math.max(1, Math.min(limit, 20))))
                .stream()
                .map(this::toActivityResponse)
                .toList();
    }

    @Transactional(readOnly = true)
    public WeeklyTrendResponse getWeeklyTrend(Jwt jwt, LocalDate from) {
        UUID userId = UUID.fromString(jwt.getSubject());
        InternalUserAnalysisContext context = userContextClient.fetch(userId);
        ZoneId zoneId = zoneId(context.timezone());
        LocalDate startDate = from == null ? LocalDate.now(zoneId).minusDays(6) : from;
        LocalDate endDate = startDate.plusDays(6);
        Instant fromInstant = startDate.atStartOfDay(zoneId).toInstant();
        Instant toInstant = endDate.plusDays(1).atStartOfDay(zoneId).toInstant();

        List<ActivityFeedItem> activities = activityFeedRepository.findByUserIdAndOccurredAtBetweenOrderByOccurredAtAsc(userId, fromInstant, toInstant);
        List<HydrationLog> hydrationLogs = hydrationLogRepository.findByUserIdAndOccurredAtBetweenOrderByOccurredAtAsc(userId, fromInstant, toInstant);

        Map<LocalDate, List<ActivityFeedItem>> activitiesByDay = activities.stream()
                .collect(Collectors.groupingBy(item -> item.getOccurredAt().atZone(zoneId).toLocalDate()));
        Map<LocalDate, Long> hydrationCounts = hydrationLogs.stream()
                .collect(Collectors.groupingBy(log -> log.getOccurredAt().atZone(zoneId).toLocalDate(), Collectors.counting()));

        List<WeeklyTrendPointResponse> points = new ArrayList<>();
        for (LocalDate current = startDate; !current.isAfter(endDate); current = current.plusDays(1)) {
            List<ActivityFeedItem> dayActivities = activitiesByDay.getOrDefault(current, List.of());
            int alertCount = (int) dayActivities.stream().filter(item -> item.getCategory() == ActivityCategory.ALERT).count();
            int reminderCount = (int) dayActivities.stream().filter(item -> item.getCategory() == ActivityCategory.REMINDER).count();
            int hydrationCount = hydrationCounts.getOrDefault(current, 0L).intValue();
            points.add(new WeeklyTrendPointResponse(current, alertCount, reminderCount, hydrationCount));
        }

        return new WeeklyTrendResponse(startDate, endDate, points);
    }

    @Transactional
    public HydrationLogResponse logHydration(Jwt jwt, HydrationLogRequest request) {
        UUID userId = UUID.fromString(jwt.getSubject());
        UUID sessionId = nullableSessionId(request.sessionId());
        Instant occurredAt = request.occurredAt() == null ? Instant.now() : request.occurredAt();

        HydrationLog log = hydrationLogRepository.save(HydrationLog.create(userId, sessionId, request.amountMl(), request.source(), occurredAt));
        activityFeedRepository.save(ActivityFeedItem.create(
                userId,
                sessionId,
                "water_logged",
                ActivityCategory.MANUAL,
                "Su Icildi",
                request.amountMl() + " ml su girisi kaydedildi.",
                null,
                occurredAt
        ));
        return new HydrationLogResponse(log.getId(), request.amountMl(), request.source(), occurredAt);
    }

    @Transactional
    public ActivityItemResponse triggerReminder(Jwt jwt, ReminderTriggerRequest request) {
        UUID userId = UUID.fromString(jwt.getSubject());
        UUID sessionId = nullableSessionId(request.sessionId());
        Instant occurredAt = request.occurredAt() == null ? Instant.now() : request.occurredAt();
        var reminder = reminderEngineService.recordManualReminder(userId, sessionId, request.reminderType(), request.message(), occurredAt);
        return new ActivityItemResponse(
                reminder.reminderId(),
                reminder.reminderType(),
                ActivityCategory.REMINDER.name(),
                reminder.reminderType().replace('_', ' '),
                reminder.message(),
                null,
                reminder.occurredAt()
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

    private int computeStreakDays(UUID userId, ZoneId zoneId, LocalDate today) {
        List<ActivityFeedItem> recentActivities = activityFeedRepository.findByUserIdOrderByOccurredAtDesc(userId, PageRequest.of(0, 64));
        List<HydrationLog> hydrationLogs = hydrationLogRepository.findByUserIdAndOccurredAtBetweenOrderByOccurredAtAsc(
                userId,
                today.minusDays(30).atStartOfDay(zoneId).toInstant(),
                today.plusDays(1).atStartOfDay(zoneId).toInstant()
        );

        List<LocalDate> activeDates = new ArrayList<>();
        activeDates.addAll(recentActivities.stream().map(item -> item.getOccurredAt().atZone(zoneId).toLocalDate()).toList());
        activeDates.addAll(hydrationLogs.stream().map(log -> log.getOccurredAt().atZone(zoneId).toLocalDate()).toList());

        List<LocalDate> distinct = activeDates.stream().distinct().sorted(Comparator.reverseOrder()).toList();
        int streak = 0;
        LocalDate cursor = today;
        for (LocalDate date : distinct) {
            if (date.equals(cursor)) {
                streak++;
                cursor = cursor.minusDays(1);
            }
        }
        return streak;
    }

    private UUID parseSessionId(String sessionId) {
        try {
            return UUID.fromString(sessionId);
        } catch (RuntimeException exception) {
            throw new IllegalArgumentException("Invalid session identifier");
        }
    }

    private UUID nullableSessionId(String sessionId) {
        if (sessionId == null || sessionId.isBlank()) {
            return null;
        }
        return parseSessionId(sessionId);
    }

    private ZoneId zoneId(String timezone) {
        try {
            return ZoneId.of(timezone);
        } catch (RuntimeException exception) {
            return ZoneId.of("UTC");
        }
    }
}
