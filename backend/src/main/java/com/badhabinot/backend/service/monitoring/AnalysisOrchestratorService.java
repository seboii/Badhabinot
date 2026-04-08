package com.badhabinot.backend.service.monitoring;

import com.badhabinot.backend.dto.monitoring.AiAnalysisRequest;
import com.badhabinot.backend.dto.monitoring.AiAnalysisResponse;
import com.badhabinot.backend.dto.monitoring.AnalyzeFrameRequest;
import com.badhabinot.backend.dto.monitoring.AnalyzeFrameResponse;
import com.badhabinot.backend.dto.monitoring.AnalysisJobStatusResponse;
import com.badhabinot.backend.dto.monitoring.BehaviorEventResponse;
import com.badhabinot.backend.dto.monitoring.InternalUserAnalysisContext;
import com.badhabinot.backend.dto.monitoring.ReminderEventResponse;
import com.badhabinot.backend.dto.monitoring.VisionAnalysisRequest;
import com.badhabinot.backend.dto.monitoring.VisionAnalysisResponse;
import com.badhabinot.backend.common.exception.monitoring.DownstreamServiceException;
import com.badhabinot.backend.model.monitoring.AnalysisJob;
import com.badhabinot.backend.model.monitoring.MonitoringSessionStatus;
import com.badhabinot.backend.repository.monitoring.AnalysisJobRepository;
import com.badhabinot.backend.repository.monitoring.MonitoringSessionRepository;
import com.badhabinot.backend.integration.python.AiAnalysisClient;
import com.badhabinot.backend.integration.python.VisionServiceClient;
import com.badhabinot.backend.infrastructure.redis.AnalysisJobStateStore;
import com.badhabinot.backend.service.user.UserContextService;
import java.time.Instant;
import java.util.Comparator;
import java.util.List;
import java.util.Optional;
import java.util.UUID;
import org.springframework.security.oauth2.jwt.Jwt;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class AnalysisOrchestratorService {

    private final AnalysisJobRepository analysisJobRepository;
    private final MonitoringSessionRepository monitoringSessionRepository;
    private final UserContextService userContextService;
    private final VisionServiceClient visionServiceClient;
    private final AiAnalysisClient aiAnalysisClient;
    private final BehaviorEventService behaviorEventService;
    private final ReminderEngineService reminderEngineService;
    private final AnalysisJobStateStore analysisJobStateStore;

    public AnalysisOrchestratorService(
            AnalysisJobRepository analysisJobRepository,
            MonitoringSessionRepository monitoringSessionRepository,
            UserContextService userContextService,
            VisionServiceClient visionServiceClient,
            AiAnalysisClient aiAnalysisClient,
            BehaviorEventService behaviorEventService,
            ReminderEngineService reminderEngineService,
            AnalysisJobStateStore analysisJobStateStore
    ) {
        this.analysisJobRepository = analysisJobRepository;
        this.monitoringSessionRepository = monitoringSessionRepository;
        this.userContextService = userContextService;
        this.visionServiceClient = visionServiceClient;
        this.aiAnalysisClient = aiAnalysisClient;
        this.behaviorEventService = behaviorEventService;
        this.reminderEngineService = reminderEngineService;
        this.analysisJobStateStore = analysisJobStateStore;
    }

    @Transactional(transactionManager = "monitoringTransactionManager", noRollbackFor = DownstreamServiceException.class)
    public AnalyzeFrameResponse analyze(Jwt jwt, AnalyzeFrameRequest request) {
        UUID userId = UUID.fromString(jwt.getSubject());
        UUID sessionId = requireActiveSession(userId, request.sessionId());
        InternalUserAnalysisContext context = userContextService.getMonitoringAnalysisContext(userId);
        ensureAnalysisAllowed(context);
        AnalysisJob job = analysisJobRepository.saveAndFlush(AnalysisJob.create(userId, request.sessionId(), request.frameId()));
        analysisJobStateStore.markProcessing(job);

        try {
            VisionAnalysisRequest visionRequest = new VisionAnalysisRequest(
                    job.getId().toString(),
                    userId.toString(),
                    request.sessionId(),
                    request.frameId(),
                    request.capturedAt(),
                    request.imageBase64(),
                    request.imageContentType()
            );

            VisionAnalysisResponse visionResponse = visionServiceClient.analyze(visionRequest);
            AiAnalysisClient.AiAnalysisInvocation aiInvocation = buildAiResponse(job, request, context, visionResponse);
            AiAnalysisResponse aiResponse = aiInvocation.response();
            Instant processedAt = Instant.now();
            List<BehaviorEventResponse> events = behaviorEventService.recordAnalysisEvents(
                    userId,
                    sessionId,
                    job.getId(),
                    processedAt,
                    visionResponse,
                    aiResponse
            );
            List<ReminderEventResponse> generatedReminders = reminderEngineService.evaluateAfterAnalysis(
                    userId,
                    sessionId,
                    context,
                    processedAt,
                    events
            );
            String dominantBehaviorType = resolveBehaviorType(aiResponse, events);
            double dominantConfidence = resolveConfidence(aiResponse, visionResponse, events);

            job.markCompleted(
                    visionResponse.subjectPresent(),
                    visionResponse.postureState(),
                    dominantBehaviorType,
                    dominantConfidence
            );

            job = analysisJobRepository.saveAndFlush(job);

            AnalyzeFrameResponse response = new AnalyzeFrameResponse(
                    job.getId(),
                    request.sessionId(),
                    request.frameId(),
                    visionResponse.subjectPresent(),
                    visionResponse.postureState(),
                    dominantBehaviorType,
                    dominantConfidence,
                    processedAt,
                    resolveSummary(aiResponse, events, visionResponse),
                    resolveRecommendation(aiResponse, events),
                    events,
                    generatedReminders,
                    new AnalyzeFrameResponse.ProcessingDetails(
                            visionResponse.processing().frameWidth(),
                            visionResponse.processing().frameHeight(),
                            visionResponse.processing().brightnessMean(),
                            visionResponse.processing().edgeDensity(),
                            visionResponse.processing().focusScore(),
                            visionResponse.signals().postureRiskScore(),
                            visionResponse.processing().visionLatencyMs(),
                            aiInvocation.latencyMs(),
                            aiResponse.scores()
                    ),
                    new AnalyzeFrameResponse.ModelDetails(
                            aiResponse.model().provider(),
                            aiResponse.model().name(),
                            aiResponse.model().mode()
                    )
            );
            analysisJobStateStore.markCompleted(job, response);
            return response;
        } catch (DownstreamServiceException exception) {
            job.markFailed(exception.getErrorCode(), exception.getMessage());
            job = analysisJobRepository.saveAndFlush(job);
            analysisJobStateStore.markFailed(job);
            throw exception;
        }
    }

    @Transactional(transactionManager = "monitoringTransactionManager", readOnly = true)
    public AnalysisJobStatusResponse getJobStatus(Jwt jwt, String analysisId) {
        UUID userId = UUID.fromString(jwt.getSubject());
        UUID jobId = parseAnalysisId(analysisId);

        Optional<AnalysisJobStatusResponse> cached = analysisJobStateStore.findOwned(jobId, userId);
        if (cached.isPresent()) {
            return cached.get();
        }

        AnalysisJob job = analysisJobRepository.findByIdAndUserId(jobId, userId)
                .orElseThrow(() -> new IllegalArgumentException("Analysis job not found"));

        return new AnalysisJobStatusResponse(
                job.getId(),
                job.getStatus().name(),
                job.getSessionId(),
                job.getFrameId(),
                job.getSubjectPresent(),
                job.getPostureState(),
                job.getBehaviorType(),
                job.getConfidence() == null ? null : job.getConfidence().doubleValue(),
                job.getCreatedAt(),
                job.getUpdatedAt(),
                null,
                null,
                job.getFailureCode(),
                job.getFailureMessage()
        );
    }

    private UUID requireActiveSession(UUID userId, String sessionId) {
        UUID parsedSessionId = parseAnalysisId(sessionId);
        monitoringSessionRepository.findByIdAndUserId(parsedSessionId, userId)
                .filter(session -> session.getStatus() == MonitoringSessionStatus.ACTIVE)
                .orElseThrow(() -> new IllegalArgumentException("Monitoring session is not active"));
        return parsedSessionId;
    }

    private void ensureAnalysisAllowed(InternalUserAnalysisContext context) {
        if (!context.cameraMonitoringAccepted()) {
            throw new IllegalStateException("Camera monitoring consent must be enabled before analyzing frames");
        }
        if (!context.remoteInferenceAccepted()) {
            throw new IllegalStateException("Remote inference consent must be enabled for API-based analysis");
        }
    }

    private AiAnalysisClient.AiAnalysisInvocation buildAiResponse(
            AnalysisJob job,
            AnalyzeFrameRequest request,
            InternalUserAnalysisContext context,
            VisionAnalysisResponse visionResponse
    ) {
        if (!visionResponse.subjectPresent()) {
            return new AiAnalysisClient.AiAnalysisInvocation(
                new AiAnalysisResponse(
                            job.getId().toString(),
                            "none",
                            0.0,
                            java.util.Map.of("hand_movement_pattern", 0.0, "smoking_like_gesture", 0.0),
                            "No subject was detected clearly enough for behavior interpretation.",
                            "Move into frame and retry the analysis.",
                            java.util.List.of(),
                            new AiAnalysisResponse.ModelDetails("none", "not-invoked", "not_invoked")
                    ),
                    0L
            );
        }

        return aiAnalysisClient.analyze(new AiAnalysisRequest(
                job.getId().toString(),
                context.userId(),
                request.sessionId(),
                request.frameId(),
                request.capturedAt(),
                context.timezone(),
                request.imageBase64(),
                request.imageContentType(),
                new AiAnalysisRequest.AnalysisSettings(
                        context.sensitivity(),
                        context.modelMode(),
                        context.remoteInferenceAccepted()
                ),
                new AiAnalysisRequest.VisionContext(
                        visionResponse.subjectPresent(),
                        visionResponse.postureState(),
                        visionResponse.processing().frameWidth(),
                        visionResponse.processing().frameHeight(),
                        visionResponse.detections().stream()
                                .map(detection -> new AiAnalysisRequest.VisionDetection(
                                        detection.eventType(),
                                        detection.confidence(),
                                        detection.severity(),
                                        detection.recommendationHint(),
                                        new AiAnalysisRequest.VisionEvidence(
                                                detection.evidence().faceDetected(),
                                                detection.evidence().upperBodyDetected(),
                                                detection.evidence().handCount(),
                                                detection.evidence().postureAlignmentScore(),
                                                detection.evidence().handFaceProximityScore(),
                                                detection.evidence().handMotionScore(),
                                                detection.evidence().repetitiveMotionScore(),
                                                detection.evidence().repeatedHandToFaceScore(),
                                                detection.evidence().elongatedObjectScore()
                                        )
                                ))
                                .toList(),
                        new AiAnalysisRequest.VisionSignals(
                                visionResponse.signals().brightnessMean(),
                                visionResponse.signals().edgeDensity(),
                                visionResponse.signals().centerEdgeDensity(),
                                visionResponse.signals().postureRiskScore(),
                                visionResponse.signals().handFaceProximityScore(),
                                visionResponse.signals().elongatedObjectScore(),
                                visionResponse.signals().focusScore(),
                                visionResponse.signals().postureConfidence(),
                                visionResponse.signals().postureAlignmentScore(),
                                visionResponse.signals().handMotionScore(),
                                visionResponse.signals().repetitiveMotionScore(),
                                visionResponse.signals().smokingGestureScore(),
                                visionResponse.signals().faceSizeRatio()
                        )
                )
        ));
    }

    private String resolveBehaviorType(AiAnalysisResponse aiResponse, List<BehaviorEventResponse> events) {
        if (aiResponse.behaviorType() != null && !"none".equalsIgnoreCase(aiResponse.behaviorType())) {
            return aiResponse.behaviorType();
        }
        return events.stream()
                .filter(event -> !"poor_posture".equals(event.eventType()))
                .max(Comparator.comparingDouble(BehaviorEventResponse::confidence))
                .map(BehaviorEventResponse::eventType)
                .orElse("none");
    }

    private double resolveConfidence(
            AiAnalysisResponse aiResponse,
            VisionAnalysisResponse visionResponse,
            List<BehaviorEventResponse> events
    ) {
        double eventConfidence = events.stream().mapToDouble(BehaviorEventResponse::confidence).max().orElse(0.0);
        return Math.max(
                Math.max(aiResponse.confidence(), eventConfidence),
                "poor".equalsIgnoreCase(visionResponse.postureState()) ? visionResponse.postureConfidence() : 0.0
        );
    }

    private String resolveSummary(
            AiAnalysisResponse aiResponse,
            List<BehaviorEventResponse> events,
            VisionAnalysisResponse visionResponse
    ) {
        if (aiResponse.summary() != null && !aiResponse.summary().isBlank()
                && !"none".equalsIgnoreCase(aiResponse.behaviorType())) {
            return aiResponse.summary();
        }
        return events.stream()
                .max(Comparator.comparingDouble(BehaviorEventResponse::confidence))
                .map(BehaviorEventResponse::interpretation)
                .orElseGet(() -> visionResponse.subjectPresent()
                        ? "The frame was processed successfully and no high-confidence risky behavior event was recorded."
                        : "No subject was detected clearly enough to produce a behavior summary.");
    }

    private String resolveRecommendation(AiAnalysisResponse aiResponse, List<BehaviorEventResponse> events) {
        if (aiResponse.recommendation() != null && !aiResponse.recommendation().isBlank()
                && !"none".equalsIgnoreCase(aiResponse.behaviorType())) {
            return aiResponse.recommendation();
        }
        return events.stream()
                .max(Comparator.comparingDouble(BehaviorEventResponse::confidence))
                .map(BehaviorEventResponse::recommendationHint)
                .orElse("Continue monitoring and capture another frame if posture or behavior changes.");
    }

    private UUID parseAnalysisId(String analysisId) {
        try {
            return UUID.fromString(analysisId);
        } catch (RuntimeException exception) {
            throw new IllegalArgumentException("Invalid analysis identifier");
        }
    }
}

