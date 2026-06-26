package com.badhabinot.backend.service.monitoring;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.badhabinot.backend.dto.monitoring.BehaviorEventResponse;
import com.badhabinot.backend.dto.monitoring.InternalUserAnalysisContext;
import com.badhabinot.backend.model.monitoring.ActivityFeedItem;
import com.badhabinot.backend.model.monitoring.HydrationLog;
import com.badhabinot.backend.model.monitoring.ReminderEvent;
import com.badhabinot.backend.repository.monitoring.ActivityFeedRepository;
import com.badhabinot.backend.repository.monitoring.HydrationLogRepository;
import com.badhabinot.backend.repository.monitoring.ReminderEventRepository;
import com.badhabinot.backend.service.monitoring.IPushNotificationService;
import com.badhabinot.backend.service.monitoring.impl.ReminderEngineServiceImpl;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.UUID;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

@ExtendWith(MockitoExtension.class)
class ReminderEngineServiceTest {

    @Mock
    private ReminderEventRepository reminderEventRepository;

    @Mock
    private ActivityFeedRepository activityFeedRepository;

    @Mock
    private HydrationLogRepository hydrationLogRepository;

    @Mock
    private IPushNotificationService pushNotificationService;

    private ReminderEngineServiceImpl ReminderEngineServiceImpl;

    @BeforeEach
    void setUp() {
        ReminderEngineServiceImpl = new ReminderEngineServiceImpl(
                reminderEventRepository,
                activityFeedRepository,
                hydrationLogRepository,
                new ObjectMapper().findAndRegisterModules(),
                pushNotificationService
        );
    }

    @Test
    void evaluateAfterAnalysisCreatesHydrationAndPostureReminders() {
        UUID userId = UUID.randomUUID();
        UUID sessionId = UUID.randomUUID();
        Instant occurredAt = Instant.parse("2026-04-08T09:00:00Z");

        InternalUserAnalysisContext context = new InternalUserAnalysisContext(
                userId.toString(),
                "UTC",
                "MEDIUM",
                "API",
                true,
                2500,
                60,
                45,
                true,
                false,
                "22:00",
                "08:00",
                true,
                "llama3.2:3b",
                "http://localhost:11434"
        );
        BehaviorEventResponse postureEvent = new BehaviorEventResponse(
                UUID.randomUUID(),
                UUID.randomUUID(),
                sessionId.toString(),
                "poor_posture",
                "vision",
                0.91,
                "medium",
                "Poor posture detected",
                "Take a posture reset",
                java.util.Map.of("posture_alignment", 0.4),
                occurredAt
        );

        when(hydrationLogRepository.findFirstByUserIdOrderByOccurredAtDesc(userId)).thenReturn(Optional.empty());
        when(reminderEventRepository.findFirstByUserIdAndReminderTypeOrderByOccurredAtDesc(eq(userId), anyString()))
                .thenReturn(Optional.empty());
        when(reminderEventRepository.save(any(ReminderEvent.class))).thenAnswer(invocation -> invocation.getArgument(0));
        when(activityFeedRepository.save(any(ActivityFeedItem.class))).thenAnswer(invocation -> invocation.getArgument(0));

        var reminders = ReminderEngineServiceImpl.evaluateAfterAnalysis(userId, sessionId, context, occurredAt, List.of(postureEvent));

        assertThat(reminders).hasSize(2);
        assertThat(reminders).extracting("reminderType").containsExactlyInAnyOrder("water_reminder", "posture_reminder");
        org.mockito.Mockito.verify(reminderEventRepository, org.mockito.Mockito.times(2)).save(any(ReminderEvent.class));
        org.mockito.Mockito.verify(activityFeedRepository, org.mockito.Mockito.times(2)).save(any(ActivityFeedItem.class));
    }

    @Test
    void evaluateAfterAnalysisReturnsEmptyDuringQuietHours() {
        UUID userId = UUID.randomUUID();
        UUID sessionId = UUID.randomUUID();
        Instant occurredAt = Instant.parse("2026-04-08T23:15:00Z");

        InternalUserAnalysisContext context = new InternalUserAnalysisContext(
                userId.toString(),
                "UTC",
                "MEDIUM",
                "API",
                true,
                2500,
                60,
                45,
                true,
                true,
                "22:00",
                "08:00",
                true,
                "llama3.2:3b",
                "http://localhost:11434"
        );
        var reminders = ReminderEngineServiceImpl.evaluateAfterAnalysis(userId, sessionId, context, occurredAt, List.of());

        assertThat(reminders).isEmpty();
        verify(reminderEventRepository, never()).save(any(ReminderEvent.class));
        verify(activityFeedRepository, never()).save(any(ActivityFeedItem.class));
    }
}
