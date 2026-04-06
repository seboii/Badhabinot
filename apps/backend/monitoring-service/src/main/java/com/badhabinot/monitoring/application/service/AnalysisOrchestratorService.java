package com.badhabinot.monitoring.application.service;

import com.badhabinot.monitoring.application.dto.AnalyzeFrameRequest;
import com.badhabinot.monitoring.application.dto.AnalyzeFrameResponse;
import com.badhabinot.monitoring.application.dto.AnalysisJobStatusResponse;
import com.badhabinot.monitoring.application.dto.InternalUserAnalysisContext;
import com.badhabinot.monitoring.application.dto.VisionAnalysisRequest;
import com.badhabinot.monitoring.application.dto.VisionAnalysisResponse;
import com.badhabinot.monitoring.application.exception.DownstreamServiceException;
import com.badhabinot.monitoring.domain.model.AnalysisJob;
import com.badhabinot.monitoring.domain.repository.AnalysisJobRepository;
import com.badhabinot.monitoring.infrastructure.client.UserContextClient;
import com.badhabinot.monitoring.infrastructure.client.VisionServiceClient;
import com.badhabinot.monitoring.infrastructure.redis.AnalysisJobStateStore;
import java.time.Instant;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;
import org.springframework.security.oauth2.jwt.Jwt;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class AnalysisOrchestratorService {

    private final AnalysisJobRepository analysisJobRepository;
    private final UserContextClient userContextClient;
    private final VisionServiceClient visionServiceClient;
    private final MonitoringExperienceService monitoringExperienceService;
    private final AnalysisJobStateStore analysisJobStateStore;

    public AnalysisOrchestratorService(
            AnalysisJobRepository analysisJobRepository,
            UserContextClient userContextClient,
            VisionServiceClient visionServiceClient,
            MonitoringExperienceService monitoringExperienceService,
            AnalysisJobStateStore analysisJobStateStore
    ) {
        this.analysisJobRepository = analysisJobRepository;
        this.userContextClient = userContextClient;
        this.visionServiceClient = visionServiceClient;
        this.monitoringExperienceService = monitoringExperienceService;
        this.analysisJobStateStore = analysisJobStateStore;
    }

    @Transactional(noRollbackFor = DownstreamServiceException.class)
    public AnalyzeFrameResponse analyze(Jwt jwt, AnalyzeFrameRequest request) {
        UUID userId = UUID.fromString(jwt.getSubject());
        AnalysisJob job = analysisJobRepository.saveAndFlush(AnalysisJob.create(userId, request.sessionId(), request.frameId()));
        analysisJobStateStore.markProcessing(job);

        try {
            InternalUserAnalysisContext context = userContextClient.fetch(userId);
            VisionAnalysisRequest visionRequest = new VisionAnalysisRequest(
                    job.getId().toString(),
                    userId.toString(),
                    request.sessionId(),
                    request.frameId(),
                    request.capturedAt(),
                    request.imageBase64(),
                    request.imageContentType(),
                    new VisionAnalysisRequest.VisionSettings(
                            context.sensitivity(),
                            context.modelMode(),
                            context.remoteInferenceAccepted()
                    )
            );

            VisionAnalysisResponse visionResponse = visionServiceClient.analyze(visionRequest);
            job.markCompleted(
                    visionResponse.subjectPresent(),
                    visionResponse.postureState(),
                    visionResponse.inference().behaviorType(),
                    visionResponse.inference().confidence()
            );
            if (visionResponse.subjectPresent()) {
                monitoringExperienceService.recordAnalysisActivities(
                        userId,
                        request.sessionId(),
                        visionResponse.postureState(),
                        visionResponse.inference().behaviorType(),
                        visionResponse.inference().confidence(),
                        request.capturedAt()
                );
            }

            Map<String, Object> processing = new LinkedHashMap<>();
            processing.put("frameWidth", visionResponse.processing().frameWidth());
            processing.put("frameHeight", visionResponse.processing().frameHeight());
            processing.put("brightnessMean", visionResponse.processing().brightnessMean());
            processing.put("edgeDensity", visionResponse.processing().edgeDensity());
            processing.put("visionLatencyMs", visionResponse.processing().visionLatencyMs());
            processing.put("aiLatencyMs", visionResponse.processing().aiLatencyMs());
            processing.put("scores", visionResponse.inference().scores());

            job = analysisJobRepository.saveAndFlush(job);

            AnalyzeFrameResponse response = new AnalyzeFrameResponse(
                    job.getId(),
                    request.sessionId(),
                    request.frameId(),
                    visionResponse.subjectPresent(),
                    visionResponse.postureState(),
                    visionResponse.inference().behaviorType(),
                    visionResponse.inference().confidence(),
                    request.capturedAt(),
                    processing
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

    @Transactional(readOnly = true)
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

    private UUID parseAnalysisId(String analysisId) {
        try {
            return UUID.fromString(analysisId);
        } catch (RuntimeException exception) {
            throw new IllegalArgumentException("Invalid analysis identifier");
        }
    }
}
