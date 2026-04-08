package com.badhabinot.backend.service.monitoring;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.verifyNoInteractions;
import static org.mockito.Mockito.when;

import com.badhabinot.backend.dto.monitoring.AnalysisJobStatusResponse;
import com.badhabinot.backend.dto.monitoring.AnalyzeFrameRequest;
import com.badhabinot.backend.dto.monitoring.InternalUserAnalysisContext;
import com.badhabinot.backend.dto.monitoring.VisionAnalysisResponse;
import com.badhabinot.backend.integration.python.AiAnalysisClient;
import com.badhabinot.backend.integration.python.VisionServiceClient;
import com.badhabinot.backend.infrastructure.redis.AnalysisJobStateStore;
import com.badhabinot.backend.model.monitoring.AnalysisJob;
import com.badhabinot.backend.model.monitoring.MonitoringSession;
import com.badhabinot.backend.repository.monitoring.AnalysisJobRepository;
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
import org.springframework.security.oauth2.jwt.Jwt;
import org.springframework.test.util.ReflectionTestUtils;

@ExtendWith(MockitoExtension.class)
class AnalysisOrchestratorServiceTest {

    @Mock
    private AnalysisJobRepository analysisJobRepository;

    @Mock
    private MonitoringSessionRepository monitoringSessionRepository;

    @Mock
    private UserContextService userContextService;

    @Mock
    private VisionServiceClient visionServiceClient;

    @Mock
    private AiAnalysisClient aiAnalysisClient;

    @Mock
    private BehaviorEventService behaviorEventService;

    @Mock
    private ReminderEngineService reminderEngineService;

    @Mock
    private AnalysisJobStateStore analysisJobStateStore;

    @InjectMocks
    private AnalysisOrchestratorService analysisOrchestratorService;

    @Test
    void analyzeRejectsFramesWhenRemoteInferenceConsentIsMissing() {
        UUID userId = UUID.randomUUID();
        UUID sessionId = UUID.randomUUID();
        Jwt jwt = jwt(userId);
        when(monitoringSessionRepository.findByIdAndUserId(sessionId, userId))
                .thenReturn(Optional.of(activeSession(userId, sessionId)));
        when(userContextService.getMonitoringAnalysisContext(userId)).thenReturn(new InternalUserAnalysisContext(
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
                false
        ));

        AnalyzeFrameRequest request = new AnalyzeFrameRequest(
                sessionId.toString(),
                "frame-1",
                Instant.parse("2026-04-08T09:00:00Z"),
                "base64-image",
                "image/jpeg"
        );

        assertThatThrownBy(() -> analysisOrchestratorService.analyze(jwt, request))
                .isInstanceOf(IllegalStateException.class)
                .hasMessageContaining("Remote inference consent");

        verifyNoInteractions(visionServiceClient, aiAnalysisClient);
    }

    @Test
    void analyzeCompletesWithoutCallingAiWhenNoSubjectIsDetected() {
        UUID userId = UUID.randomUUID();
        UUID sessionId = UUID.randomUUID();
        Jwt jwt = jwt(userId);
        when(monitoringSessionRepository.findByIdAndUserId(sessionId, userId))
                .thenReturn(Optional.of(activeSession(userId, sessionId)));
        when(userContextService.getMonitoringAnalysisContext(userId)).thenReturn(new InternalUserAnalysisContext(
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
        ));
        when(analysisJobRepository.saveAndFlush(any(AnalysisJob.class))).thenAnswer(invocation -> {
            AnalysisJob job = invocation.getArgument(0);
            if (job.getCreatedAt() == null) {
                ReflectionTestUtils.setField(job, "createdAt", Instant.parse("2026-04-08T09:00:00Z"));
            }
            ReflectionTestUtils.setField(job, "updatedAt", Instant.parse("2026-04-08T09:00:01Z"));
            return job;
        });
        when(visionServiceClient.analyze(any())).thenReturn(new VisionAnalysisResponse(
                "request-1",
                false,
                "unknown",
                0.0,
                List.of(),
                new VisionAnalysisResponse.Signals(0.1, 0.2, 0.1, 0.0, 0.0, 0.0, 0.7, 0.0, 0.0, 0.0, 0.0, 0.0, 0.2),
                new VisionAnalysisResponse.Processing(1280, 720, 0.1, 0.2, 0.7, 45L)
        ));
        when(behaviorEventService.recordAnalysisEvents(eq(userId), eq(sessionId), any(), any(), any(), any()))
                .thenReturn(List.of());
        when(reminderEngineService.evaluateAfterAnalysis(eq(userId), eq(sessionId), any(), any(), any()))
                .thenReturn(List.of());

        AnalyzeFrameRequest request = new AnalyzeFrameRequest(
                sessionId.toString(),
                "frame-2",
                Instant.parse("2026-04-08T09:00:00Z"),
                "base64-image",
                "image/jpeg"
        );

        var response = analysisOrchestratorService.analyze(jwt, request);

        assertThat(response.subjectPresent()).isFalse();
        assertThat(response.model().provider()).isEqualTo("none");
        assertThat(response.summary()).contains("No subject");
        verifyNoInteractions(aiAnalysisClient);
        verify(analysisJobStateStore).markProcessing(any(AnalysisJob.class));
        verify(analysisJobStateStore).markCompleted(any(AnalysisJob.class), any());
    }

    @Test
    void getJobStatusReturnsCachedStateWhenAvailable() {
        UUID userId = UUID.randomUUID();
        UUID analysisId = UUID.randomUUID();
        Jwt jwt = jwt(userId);
        AnalysisJobStatusResponse cached = new AnalysisJobStatusResponse(
                analysisId,
                "COMPLETED",
                "session-1",
                "frame-1",
                true,
                "good",
                "none",
                0.82,
                Instant.parse("2026-04-08T09:00:00Z"),
                Instant.parse("2026-04-08T09:00:01Z"),
                Instant.parse("2026-04-08T09:15:00Z"),
                java.util.Map.of("vision_latency_ms", 42),
                null,
                null
        );
        when(analysisJobStateStore.findOwned(analysisId, userId)).thenReturn(Optional.of(cached));

        var response = analysisOrchestratorService.getJobStatus(jwt, analysisId.toString());

        assertThat(response).isEqualTo(cached);
        verifyNoInteractions(analysisJobRepository);
    }

    private Jwt jwt(UUID userId) {
        Jwt jwt = org.mockito.Mockito.mock(Jwt.class);
        when(jwt.getSubject()).thenReturn(userId.toString());
        return jwt;
    }

    private MonitoringSession activeSession(UUID userId, UUID sessionId) {
        MonitoringSession session = MonitoringSession.start(userId, "web", "desktop");
        ReflectionTestUtils.setField(session, "id", sessionId);
        return session;
    }
}
