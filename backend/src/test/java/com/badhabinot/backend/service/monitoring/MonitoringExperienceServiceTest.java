package com.badhabinot.backend.service.monitoring;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.badhabinot.backend.dto.monitoring.InternalUserAnalysisContext;
import com.badhabinot.backend.dto.monitoring.SessionStartRequest;
import com.badhabinot.backend.model.monitoring.ActivityCategory;
import com.badhabinot.backend.model.monitoring.ActivityFeedItem;
import com.badhabinot.backend.model.monitoring.HydrationLog;
import com.badhabinot.backend.model.monitoring.MonitoringSession;
import com.badhabinot.backend.model.monitoring.MonitoringSessionStatus;
import com.badhabinot.backend.repository.monitoring.ActivityFeedRepository;
import com.badhabinot.backend.repository.monitoring.HydrationLogRepository;
import com.badhabinot.backend.repository.monitoring.MonitoringSessionRepository;
import com.badhabinot.backend.service.user.UserContextService;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.UUID;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.data.domain.Pageable;
import org.springframework.security.oauth2.jwt.Jwt;

@ExtendWith(MockitoExtension.class)
class MonitoringExperienceServiceTest {

    @Mock
    private MonitoringSessionRepository monitoringSessionRepository;

    @Mock
    private ActivityFeedRepository activityFeedRepository;

    @Mock
    private HydrationLogRepository hydrationLogRepository;

    @Mock
    private UserContextService userContextService;

    @Mock
    private ReminderEngineService reminderEngineService;

    @InjectMocks
    private MonitoringExperienceService monitoringExperienceService;

    @Test
    void getDashboardAggregatesActivitiesHydrationAndPrivacyState() {
        UUID userId = UUID.randomUUID();
        UUID sessionId = UUID.randomUUID();
        Jwt jwt = jwt(userId);
        MonitoringSession activeSession = MonitoringSession.start(userId, "web", "desktop");
        org.springframework.test.util.ReflectionTestUtils.setField(activeSession, "id", sessionId);

        InternalUserAnalysisContext context = new InternalUserAnalysisContext(
                userId.toString(),
                "UTC",
                "MEDIUM",
                "API",
                true,
                2500,
                60,
                60,
                true,
                false,
                "22:00",
                "08:00",
                true
        );
        ActivityFeedItem alert = ActivityFeedItem.create(
                userId,
                sessionId,
                "poor_posture",
                ActivityCategory.ALERT,
                "Alert",
                "Posture alert",
                0.88,
                Instant.now()
        );
        ActivityFeedItem reminder = ActivityFeedItem.create(
                userId,
                sessionId,
                "water_reminder",
                ActivityCategory.REMINDER,
                "Reminder",
                "Drink water",
                null,
                Instant.now()
        );
        HydrationLog hydrationLog = HydrationLog.create(userId, sessionId, 750, "manual", Instant.now());

        when(userContextService.getMonitoringAnalysisContext(userId)).thenReturn(context);
        when(monitoringSessionRepository.findFirstByUserIdAndStatusOrderByStartedAtDesc(userId, MonitoringSessionStatus.ACTIVE))
                .thenReturn(Optional.of(activeSession));
        when(activityFeedRepository.findByUserIdAndOccurredAtBetweenOrderByOccurredAtAsc(eq(userId), any(), any()))
                .thenReturn(List.of(alert, reminder));
        when(activityFeedRepository.findByUserIdOrderByOccurredAtDesc(eq(userId), any(Pageable.class)))
                .thenReturn(List.of(reminder, alert));
        when(hydrationLogRepository.findByUserIdAndOccurredAtBetweenOrderByOccurredAtAsc(eq(userId), any(), any()))
                .thenReturn(List.of(hydrationLog));

        var dashboard = monitoringExperienceService.getDashboard(jwt);

        assertThat(dashboard.monitoringActive()).isTrue();
        assertThat(dashboard.activeSessionId()).isEqualTo(sessionId.toString());
        assertThat(dashboard.analysisEnabled()).isTrue();
        assertThat(dashboard.alertCountToday()).isEqualTo(1);
        assertThat(dashboard.reminderCountToday()).isEqualTo(1);
        assertThat(dashboard.waterProgressMl()).isEqualTo(750);
        assertThat(dashboard.privacyMode()).isEqualTo("API_CONSENTED");
        assertThat(dashboard.recentActivities()).hasSize(2);
        assertThat(dashboard.streakDays()).isGreaterThanOrEqualTo(1);
    }

    @Test
    void startSessionStopsExistingSessionBeforeCreatingANewOne() {
        UUID userId = UUID.randomUUID();
        Jwt jwt = jwt(userId);
        MonitoringSession existingSession = MonitoringSession.start(userId, "web", "desktop");

        when(monitoringSessionRepository.findFirstByUserIdAndStatusOrderByStartedAtDesc(userId, MonitoringSessionStatus.ACTIVE))
                .thenReturn(Optional.of(existingSession));
        when(monitoringSessionRepository.save(any(MonitoringSession.class))).thenAnswer(invocation -> invocation.getArgument(0));
        when(activityFeedRepository.save(any(ActivityFeedItem.class))).thenAnswer(invocation -> invocation.getArgument(0));

        var response = monitoringExperienceService.startSession(jwt, new SessionStartRequest("mobile", "phone"));

        assertThat(response.status()).isEqualTo(MonitoringSessionStatus.ACTIVE.name());
        verify(monitoringSessionRepository).save(existingSession);
        verify(activityFeedRepository).save(any(ActivityFeedItem.class));
    }

    private Jwt jwt(UUID userId) {
        Jwt jwt = org.mockito.Mockito.mock(Jwt.class);
        when(jwt.getSubject()).thenReturn(userId.toString());
        return jwt;
    }
}
