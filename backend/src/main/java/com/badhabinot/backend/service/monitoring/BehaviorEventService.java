package com.badhabinot.backend.service.monitoring;

import com.badhabinot.backend.dto.monitoring.AiAnalysisResponse;
import com.badhabinot.backend.dto.monitoring.BehaviorEventResponse;
import com.badhabinot.backend.dto.monitoring.VisionAnalysisResponse;
import com.badhabinot.backend.model.monitoring.ActivityCategory;
import com.badhabinot.backend.model.monitoring.ActivityFeedItem;
import com.badhabinot.backend.model.monitoring.BehaviorEvent;
import com.badhabinot.backend.repository.monitoring.ActivityFeedRepository;
import com.badhabinot.backend.repository.monitoring.BehaviorEventRepository;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.time.Instant;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class BehaviorEventService {

    private static final TypeReference<Map<String, Object>> MAP_TYPE = new TypeReference<>() {
    };

    private final BehaviorEventRepository behaviorEventRepository;
    private final ActivityFeedRepository activityFeedRepository;
    private final ObjectMapper objectMapper;

    public BehaviorEventService(
            BehaviorEventRepository behaviorEventRepository,
            ActivityFeedRepository activityFeedRepository,
            ObjectMapper objectMapper
    ) {
        this.behaviorEventRepository = behaviorEventRepository;
        this.activityFeedRepository = activityFeedRepository;
        this.objectMapper = objectMapper;
    }

    @Transactional(transactionManager = "monitoringTransactionManager")
    public List<BehaviorEventResponse> recordAnalysisEvents(
            UUID userId,
            UUID sessionId,
            UUID analysisId,
            Instant occurredAt,
            VisionAnalysisResponse visionResponse,
            AiAnalysisResponse aiResponse
    ) {
        Map<String, PendingEvent> eventByType = new LinkedHashMap<>();
        for (VisionAnalysisResponse.Detection detection : visionResponse.detections()) {
            eventByType.put(
                    detection.eventType(),
                    new PendingEvent(
                            detection.eventType(),
                            detectorFor(detection.eventType()),
                            detection.confidence(),
                            detection.severity(),
                            interpretationFor(detection.eventType(), detection.confidence()),
                            detection.recommendationHint(),
                            objectMapper.convertValue(detection.evidence(), MAP_TYPE)
                    )
            );
        }

        if (aiResponse.behaviorType() != null && !"none".equalsIgnoreCase(aiResponse.behaviorType())) {
            eventByType.putIfAbsent(
                    aiResponse.behaviorType(),
                    new PendingEvent(
                            aiResponse.behaviorType(),
                            "ai.behavior",
                            aiResponse.confidence(),
                            severityFor(aiResponse.confidence()),
                            interpretationFor(aiResponse.behaviorType(), aiResponse.confidence()),
                            aiResponse.recommendation(),
                            Map.of(
                                    "grounded_facts", aiResponse.groundedFacts() == null ? List.of() : aiResponse.groundedFacts(),
                                    "scores", aiResponse.scores()
                            )
                    )
            );
        }

        List<BehaviorEventResponse> responses = new ArrayList<>();
        for (PendingEvent pendingEvent : eventByType.values()) {
            if (pendingEvent.confidence() < 0.45) {
                continue;
            }

            String evidenceJson = writeJson(pendingEvent.evidence());
            BehaviorEvent event = behaviorEventRepository.save(BehaviorEvent.create(
                    analysisId,
                    userId,
                    sessionId,
                    pendingEvent.eventType(),
                    pendingEvent.detector(),
                    pendingEvent.confidence(),
                    pendingEvent.severity(),
                    pendingEvent.interpretation(),
                    pendingEvent.recommendationHint(),
                    evidenceJson,
                    occurredAt
            ));

            activityFeedRepository.save(ActivityFeedItem.create(
                    userId,
                    sessionId,
                    pendingEvent.eventType(),
                    ActivityCategory.ALERT,
                    titleFor(pendingEvent.eventType()),
                    pendingEvent.interpretation(),
                    pendingEvent.confidence(),
                    occurredAt
            ));

            responses.add(toResponse(event));
        }
        return responses;
    }

    @Transactional(transactionManager = "monitoringTransactionManager", readOnly = true)
    public List<BehaviorEventResponse> getRecentEvents(UUID userId, int limit) {
        return behaviorEventRepository.findByUserIdOrderByOccurredAtDesc(userId, PageRequest.of(0, Math.max(1, Math.min(limit, 25))))
                .stream()
                .map(this::toResponse)
                .toList();
    }

    public BehaviorEventResponse toResponse(BehaviorEvent event) {
        return new BehaviorEventResponse(
                event.getId(),
                event.getAnalysisId(),
                event.getSessionId() == null ? null : event.getSessionId().toString(),
                event.getEventType(),
                event.getDetector(),
                event.getConfidence().doubleValue(),
                event.getSeverity(),
                event.getInterpretation(),
                event.getRecommendationHint(),
                readJson(event.getEvidenceJson()),
                event.getOccurredAt()
        );
    }

    private String detectorFor(String eventType) {
        return switch (eventType) {
            case "poor_posture" -> "vision.posture";
            case "hand_movement_pattern" -> "vision.hand";
            case "smoking_like_gesture" -> "vision.smoking";
            default -> "vision.generic";
        };
    }

    private String interpretationFor(String eventType, double confidence) {
        return switch (eventType) {
            case "poor_posture" -> String.format(
                    "Posture drift was detected with %.0f%% confidence. A quick posture reset is recommended.",
                    confidence * 100
            );
            case "hand_movement_pattern" -> String.format(
                    "A repetitive hand movement pattern appeared with %.0f%% confidence.",
                    confidence * 100
            );
            case "smoking_like_gesture" -> String.format(
                    "A smoking-like hand-to-mouth gesture appeared with %.0f%% confidence. Treat it as a cue, not certainty.",
                    confidence * 100
            );
            default -> "Behavior activity was detected.";
        };
    }

    private String titleFor(String eventType) {
        return switch (eventType) {
            case "poor_posture" -> "Posture alert";
            case "hand_movement_pattern" -> "Hand movement alert";
            case "smoking_like_gesture" -> "Smoking-like gesture alert";
            default -> "Behavior alert";
        };
    }

    private String severityFor(double confidence) {
        if (confidence >= 0.80) {
            return "high";
        }
        if (confidence >= 0.62) {
            return "medium";
        }
        return "low";
    }

    private String writeJson(Map<String, Object> payload) {
        try {
            return objectMapper.writeValueAsString(payload);
        } catch (Exception exception) {
            return "{}";
        }
    }

    private Map<String, Object> readJson(String payload) {
        try {
            return objectMapper.readValue(payload, MAP_TYPE);
        } catch (Exception exception) {
            return Map.of();
        }
    }

    private record PendingEvent(
            String eventType,
            String detector,
            double confidence,
            String severity,
            String interpretation,
            String recommendationHint,
            Map<String, Object> evidence
    ) {
    }
}

