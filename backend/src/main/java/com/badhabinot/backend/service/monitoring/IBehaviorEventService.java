package com.badhabinot.backend.service.monitoring;

import com.badhabinot.backend.dto.monitoring.AiAnalysisResponse;
import com.badhabinot.backend.dto.monitoring.BehaviorEventResponse;
import com.badhabinot.backend.dto.monitoring.VisionAnalysisResponse;
import com.badhabinot.backend.model.monitoring.BehaviorEvent;
import java.time.Instant;
import java.util.List;
import java.util.UUID;

public interface IBehaviorEventService {
    List<BehaviorEventResponse> recordAnalysisEvents(UUID userId, UUID sessionId, UUID analysisId, Instant occurredAt, VisionAnalysisResponse visionResponse, AiAnalysisResponse aiResponse);
    List<BehaviorEventResponse> getRecentEvents(UUID userId, int page, int size);
    BehaviorEventResponse toResponse(BehaviorEvent event);
}
