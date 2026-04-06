package com.badhabinot.monitoring.infrastructure.redis;

import com.badhabinot.monitoring.application.dto.AnalysisJobStatusResponse;
import com.badhabinot.monitoring.application.dto.AnalyzeFrameResponse;
import com.badhabinot.monitoring.domain.model.AnalysisJob;
import com.badhabinot.monitoring.infrastructure.config.MonitoringRedisProperties;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.time.Instant;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Component;

@Component
public class AnalysisJobStateStore {

    private static final Logger log = LoggerFactory.getLogger(AnalysisJobStateStore.class);

    private final StringRedisTemplate redisTemplate;
    private final ObjectMapper objectMapper;
    private final MonitoringRedisProperties properties;

    public AnalysisJobStateStore(
            StringRedisTemplate redisTemplate,
            ObjectMapper objectMapper,
            MonitoringRedisProperties properties
    ) {
        this.redisTemplate = redisTemplate;
        this.objectMapper = objectMapper;
        this.properties = properties;
    }

    public void markProcessing(AnalysisJob job) {
        Instant expiresAt = Instant.now().plus(properties.analysisJobTtl());
        save(new StoredAnalysisJobState(
                job.getId(),
                job.getUserId(),
                job.getStatus().name(),
                job.getSessionId(),
                job.getFrameId(),
                null,
                null,
                null,
                null,
                job.getCreatedAt(),
                job.getUpdatedAt(),
                expiresAt,
                null,
                null,
                null
        ));
    }

    public void markCompleted(AnalysisJob job, AnalyzeFrameResponse response) {
        Instant expiresAt = Instant.now().plus(properties.analysisJobTtl());
        save(new StoredAnalysisJobState(
                job.getId(),
                job.getUserId(),
                job.getStatus().name(),
                job.getSessionId(),
                job.getFrameId(),
                response.subjectPresent(),
                response.postureState(),
                response.behaviorType(),
                response.confidence(),
                job.getCreatedAt(),
                job.getUpdatedAt(),
                expiresAt,
                response.processing(),
                null,
                null
        ));
    }

    public void markFailed(AnalysisJob job) {
        Instant expiresAt = Instant.now().plus(properties.analysisJobTtl());
        save(new StoredAnalysisJobState(
                job.getId(),
                job.getUserId(),
                job.getStatus().name(),
                job.getSessionId(),
                job.getFrameId(),
                job.getSubjectPresent(),
                job.getPostureState(),
                job.getBehaviorType(),
                job.getConfidence() == null ? null : job.getConfidence().doubleValue(),
                job.getCreatedAt(),
                job.getUpdatedAt(),
                expiresAt,
                null,
                job.getFailureCode(),
                job.getFailureMessage()
        ));
    }

    public Optional<AnalysisJobStatusResponse> findOwned(UUID analysisId, UUID userId) {
        return read(analysisId)
                .filter(state -> state.userId().equals(userId))
                .map(this::toResponse);
    }

    private Optional<StoredAnalysisJobState> read(UUID analysisId) {
        try {
            String value = redisTemplate.opsForValue().get(key(analysisId));
            if (value == null || value.isBlank()) {
                return Optional.empty();
            }
            return Optional.of(objectMapper.readValue(value, StoredAnalysisJobState.class));
        } catch (Exception exception) {
            log.warn("Redis analysis job lookup failed for {}: {}", analysisId, exception.getMessage());
            return Optional.empty();
        }
    }

    private void save(StoredAnalysisJobState state) {
        try {
            redisTemplate.opsForValue().set(
                    key(state.analysisId()),
                    objectMapper.writeValueAsString(state),
                    properties.analysisJobTtl()
            );
        } catch (JsonProcessingException exception) {
            log.warn("Unable to serialize analysis job state for {}: {}", state.analysisId(), exception.getMessage());
        } catch (Exception exception) {
            log.warn("Redis analysis job update failed for {}: {}", state.analysisId(), exception.getMessage());
        }
    }

    private AnalysisJobStatusResponse toResponse(StoredAnalysisJobState state) {
        return new AnalysisJobStatusResponse(
                state.analysisId(),
                state.status(),
                state.sessionId(),
                state.frameId(),
                state.subjectPresent(),
                state.postureState(),
                state.behaviorType(),
                state.confidence(),
                state.createdAt(),
                state.updatedAt(),
                state.expiresAt(),
                state.processing(),
                state.failureCode(),
                state.failureMessage()
        );
    }

    private String key(UUID analysisId) {
        return properties.analysisJobKeyPrefix() + analysisId;
    }

    private record StoredAnalysisJobState(
            UUID analysisId,
            UUID userId,
            String status,
            String sessionId,
            String frameId,
            Boolean subjectPresent,
            String postureState,
            String behaviorType,
            Double confidence,
            Instant createdAt,
            Instant updatedAt,
            Instant expiresAt,
            Map<String, Object> processing,
            String failureCode,
            String failureMessage
    ) {
    }
}
