package com.badhabinot.backend.service.monitoring;

import com.badhabinot.backend.dto.monitoring.BehaviorEventResponse;
import com.badhabinot.backend.dto.monitoring.InternalUserAnalysisContext;
import com.badhabinot.backend.dto.monitoring.ReminderEventResponse;
import com.badhabinot.backend.model.monitoring.ReminderEvent;
import java.time.Instant;
import java.util.List;
import java.util.UUID;

public interface IReminderEngineService {
    List<ReminderEventResponse> evaluateAfterAnalysis(UUID userId, UUID sessionId, InternalUserAnalysisContext context, Instant occurredAt, List<BehaviorEventResponse> events);
    ReminderEventResponse recordManualReminder(UUID userId, UUID sessionId, String reminderType, String message, Instant occurredAt);
    List<ReminderEventResponse> getRecentReminders(UUID userId, int limit);
    ReminderEventResponse toResponse(ReminderEvent reminderEvent);
}
