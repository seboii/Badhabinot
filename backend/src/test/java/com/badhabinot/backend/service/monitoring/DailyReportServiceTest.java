package com.badhabinot.backend.service.monitoring;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.badhabinot.backend.dto.monitoring.BehaviorEventResponse;
import com.badhabinot.backend.dto.monitoring.InternalUserAnalysisContext;
import com.badhabinot.backend.dto.monitoring.ReminderEventResponse;
import com.badhabinot.backend.model.monitoring.ActivityCategory;
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
import com.fasterxml.jackson.databind.ObjectMapper;
import java.time.Instant;
import java.time.LocalDate;
import java.util.List;
import java.util.Optional;
import java.util.UUID;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

@ExtendWith(MockitoExtension.class)
class DailyReportServiceTest {

    @Mock
    private DailyReportRepository dailyReportRepository;

    @Mock
    private BehaviorEventRepository behaviorEventRepository;

    @Mock
    private ReminderEventRepository reminderEventRepository;

    @Mock
    private HydrationLogRepository hydrationLogRepository;

    @Mock
    private ActivityFeedRepository activityFeedRepository;

    @Mock
    private AnalysisJobRepository analysisJobRepository;

    @Mock
    private UserContextService userContextService;

    @Mock
    private BehaviorEventService behaviorEventService;

    @Mock
    private ReminderEngineService reminderEngineService;

    private DailyReportService dailyReportService;

    @BeforeEach
    void setUp() {
        dailyReportService = new DailyReportService(
                dailyReportRepository,
                behaviorEventRepository,
                reminderEventRepository,
                hydrationLogRepository,
                activityFeedRepository,
                analysisJobRepository,
                userContextService,
                behaviorEventService,
                reminderEngineService,
                new ObjectMapper().findAndRegisterModules()
        );
    }

    @Test
    void getDailyReportAggregatesSignalsAndBuildsTargetedRecommendations() {
        UUID userId = UUID.randomUUID();
        UUID sessionId = UUID.randomUUID();
        LocalDate reportDate = LocalDate.of(2026, 4, 8);
        Instant occurredAt = Instant.parse("2026-04-08T09:00:00Z");
        InternalUserAnalysisContext context = context(userId, 2500);

        AnalysisJob poorPostureJob = AnalysisJob.create(userId, sessionId.toString(), "frame-1");
        poorPostureJob.markCompleted(true, "poor", "none", 0.74);
        AnalysisJob neutralJob = AnalysisJob.create(userId, sessionId.toString(), "frame-2");
        neutralJob.markCompleted(true, "good", "hand_movement_pattern", 0.62);

        BehaviorEvent poorPostureEvent = BehaviorEvent.create(
                poorPostureJob.getId(),
                userId,
                sessionId,
                "poor_posture",
                "vision",
                0.84,
                "medium",
                "Posture alignment dropped.",
                "Reset posture.",
                "{\"posture_alignment_score\":0.42}",
                occurredAt
        );
        BehaviorEvent handMovementEvent = BehaviorEvent.create(
                neutralJob.getId(),
                userId,
                sessionId,
                "hand_movement_pattern",
                "ai",
                0.77,
                "medium",
                "Repeated hand motion detected.",
                "Pause briefly.",
                "{\"hand_motion_score\":0.66}",
                occurredAt.plusSeconds(30)
        );
        ReminderEvent waterReminder = ReminderEvent.create(
                userId,
                sessionId,
                "water_reminder",
                "scheduled",
                "medium",
                "Drink water.",
                "Hydration interval elapsed.",
                "{\"water_interval_min\":60}",
                occurredAt.plusSeconds(60)
        );
        HydrationLog hydrationLog = HydrationLog.create(userId, sessionId, 600, "manual", occurredAt.plusSeconds(90));
        ActivityFeedItem timelineItem = ActivityFeedItem.create(
                userId,
                sessionId,
                "water_reminder",
                ActivityCategory.REMINDER,
                "Hydration reminder",
                "Drink water.",
                null,
                occurredAt.plusSeconds(60)
        );

        when(analysisJobRepository.findByUserIdAndCreatedAtBetweenOrderByCreatedAtAsc(eq(userId), any(), any()))
                .thenReturn(List.of(poorPostureJob, neutralJob));
        when(behaviorEventRepository.findByUserIdAndOccurredAtBetweenOrderByOccurredAtAsc(eq(userId), any(), any()))
                .thenReturn(List.of(poorPostureEvent, handMovementEvent));
        when(reminderEventRepository.findByUserIdAndOccurredAtBetweenOrderByOccurredAtAsc(eq(userId), any(), any()))
                .thenReturn(List.of(waterReminder));
        when(hydrationLogRepository.findByUserIdAndOccurredAtBetweenOrderByOccurredAtAsc(eq(userId), any(), any()))
                .thenReturn(List.of(hydrationLog));
        when(activityFeedRepository.findByUserIdAndOccurredAtBetweenOrderByOccurredAtAsc(eq(userId), any(), any()))
                .thenReturn(List.of(timelineItem));
        when(dailyReportRepository.findByUserIdAndReportDate(userId, reportDate)).thenReturn(Optional.empty());
        when(dailyReportRepository.save(any(DailyReport.class))).thenAnswer(invocation -> invocation.getArgument(0));
        when(behaviorEventService.toResponse(poorPostureEvent)).thenReturn(new BehaviorEventResponse(
                poorPostureEvent.getId(),
                poorPostureEvent.getAnalysisId(),
                sessionId.toString(),
                "poor_posture",
                "vision",
                0.84,
                "medium",
                "Posture alignment dropped.",
                "Reset posture.",
                java.util.Map.of("posture_alignment_score", 0.42),
                occurredAt
        ));
        when(behaviorEventService.toResponse(handMovementEvent)).thenReturn(new BehaviorEventResponse(
                handMovementEvent.getId(),
                handMovementEvent.getAnalysisId(),
                sessionId.toString(),
                "hand_movement_pattern",
                "ai",
                0.77,
                "medium",
                "Repeated hand motion detected.",
                "Pause briefly.",
                java.util.Map.of("hand_motion_score", 0.66),
                occurredAt.plusSeconds(30)
        ));
        when(reminderEngineService.toResponse(waterReminder)).thenReturn(new ReminderEventResponse(
                waterReminder.getId(),
                sessionId.toString(),
                "water_reminder",
                "scheduled",
                "medium",
                "Drink water.",
                "Hydration interval elapsed.",
                java.util.Map.of("water_interval_min", 60),
                occurredAt.plusSeconds(60)
        ));

        var response = dailyReportService.getDailyReport(userId, reportDate, context);

        assertThat(response.analysesCompleted()).isEqualTo(2);
        assertThat(response.postureAlertCount()).isEqualTo(1);
        assertThat(response.handMovementCount()).isEqualTo(1);
        assertThat(response.smokingLikeCount()).isEqualTo(0);
        assertThat(response.reminderCount()).isEqualTo(1);
        assertThat(response.hydrationProgressMl()).isEqualTo(600);
        assertThat(response.poorPostureRatio()).isEqualTo(0.5);
        assertThat(response.summary()).contains("processed 2 analysis frames");
        assertThat(response.recommendations())
                .anySatisfy(recommendation -> assertThat(recommendation).contains("posture reset"))
                .anySatisfy(recommendation -> assertThat(recommendation).contains("Hydration stayed below"));
        assertThat(response.keyBehaviorEvents()).hasSize(2);
        assertThat(response.reminders()).hasSize(1);
        assertThat(response.timeline()).hasSize(1);

        verify(dailyReportRepository).save(any(DailyReport.class));
    }

    @Test
    void getDailyReportAddsStabilityRecommendationWhenRiskSignalsAreAbsent() {
        UUID userId = UUID.randomUUID();
        LocalDate reportDate = LocalDate.of(2026, 4, 8);
        InternalUserAnalysisContext context = context(userId, 2000);
        DailyReport existing = DailyReport.create(userId, reportDate);
        Instant occurredAt = Instant.parse("2026-04-08T10:00:00Z");

        when(analysisJobRepository.findByUserIdAndCreatedAtBetweenOrderByCreatedAtAsc(eq(userId), any(), any()))
                .thenReturn(List.of());
        when(behaviorEventRepository.findByUserIdAndOccurredAtBetweenOrderByOccurredAtAsc(eq(userId), any(), any()))
                .thenReturn(List.of());
        when(reminderEventRepository.findByUserIdAndOccurredAtBetweenOrderByOccurredAtAsc(eq(userId), any(), any()))
                .thenReturn(List.of());
        when(hydrationLogRepository.findByUserIdAndOccurredAtBetweenOrderByOccurredAtAsc(eq(userId), any(), any()))
                .thenReturn(List.of(HydrationLog.create(userId, null, 2200, "manual", occurredAt)));
        when(activityFeedRepository.findByUserIdAndOccurredAtBetweenOrderByOccurredAtAsc(eq(userId), any(), any()))
                .thenReturn(List.of());
        when(dailyReportRepository.findByUserIdAndReportDate(userId, reportDate)).thenReturn(Optional.of(existing));
        when(dailyReportRepository.save(any(DailyReport.class))).thenAnswer(invocation -> invocation.getArgument(0));

        var response = dailyReportService.getDailyReport(userId, reportDate, context);

        assertThat(response.recommendations())
                .containsExactly("The tracked patterns stayed stable today. Keep the same monitoring cadence tomorrow.");
        assertThat(response.summary()).contains("processed 0 analysis frames");
        assertThat(response.poorPostureRatio()).isEqualTo(0.0);
    }

    private InternalUserAnalysisContext context(UUID userId, int waterGoalMl) {
        return new InternalUserAnalysisContext(
                userId.toString(),
                "UTC",
                "MEDIUM",
                "API",
                true,
                waterGoalMl,
                60,
                45,
                true,
                false,
                "22:00",
                "08:00",
                true
        );
    }
}
