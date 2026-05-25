package com.badhabinot.backend.service.monitoring;

import com.badhabinot.backend.dto.monitoring.AnalysisJobStatusResponse;
import com.badhabinot.backend.dto.monitoring.AnalyzeFrameRequest;
import com.badhabinot.backend.dto.monitoring.AnalyzeFrameResponse;
import org.springframework.security.oauth2.jwt.Jwt;

public interface IAnalysisOrchestratorService {
    AnalyzeFrameResponse analyze(Jwt jwt, AnalyzeFrameRequest request);
    AnalysisJobStatusResponse getJobStatus(Jwt jwt, String analysisId);
}
