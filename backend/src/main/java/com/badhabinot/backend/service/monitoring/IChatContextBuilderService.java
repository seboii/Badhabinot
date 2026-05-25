package com.badhabinot.backend.service.monitoring;

import com.badhabinot.backend.dto.monitoring.AiChatRequest;
import com.badhabinot.backend.dto.monitoring.DailyReportResponse;
import com.badhabinot.backend.dto.monitoring.InternalUserAnalysisContext;
import java.time.LocalDate;
import java.util.UUID;

public interface IChatContextBuilderService {
    AiChatRequest.Context build(UUID userId, InternalUserAnalysisContext userContext, LocalDate reportDate, DailyReportResponse currentReport);
}
