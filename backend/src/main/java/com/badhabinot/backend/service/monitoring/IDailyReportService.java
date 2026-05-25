package com.badhabinot.backend.service.monitoring;

import com.badhabinot.backend.dto.monitoring.DailyReportResponse;
import com.badhabinot.backend.dto.monitoring.InternalUserAnalysisContext;
import java.time.LocalDate;
import java.util.UUID;
import org.springframework.security.oauth2.jwt.Jwt;

public interface IDailyReportService {
    DailyReportResponse getDailyReport(Jwt jwt, LocalDate requestedDate);
    DailyReportResponse getDailyReport(UUID userId, LocalDate reportDate, InternalUserAnalysisContext context);
}
