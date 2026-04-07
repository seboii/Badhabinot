package com.badhabinot.monitoring.api.rest;

import com.badhabinot.monitoring.application.dto.AnalyzeFrameRequest;
import com.badhabinot.monitoring.application.dto.AnalyzeFrameResponse;
import com.badhabinot.monitoring.application.dto.AnalysisJobStatusResponse;
import com.badhabinot.monitoring.application.dto.ActivityItemResponse;
import com.badhabinot.monitoring.application.dto.DashboardResponse;
import com.badhabinot.monitoring.application.dto.DailyReportResponse;
import com.badhabinot.monitoring.application.dto.HydrationLogRequest;
import com.badhabinot.monitoring.application.dto.HydrationLogResponse;
import com.badhabinot.monitoring.application.dto.ReminderTriggerRequest;
import com.badhabinot.monitoring.application.dto.SessionStartRequest;
import com.badhabinot.monitoring.application.dto.SessionStartResponse;
import com.badhabinot.monitoring.application.dto.SessionStopResponse;
import com.badhabinot.monitoring.application.dto.WeeklyTrendResponse;
import com.badhabinot.monitoring.application.dto.BehaviorEventResponse;
import com.badhabinot.monitoring.application.dto.ChatRequest;
import com.badhabinot.monitoring.application.dto.ChatResponse;
import com.badhabinot.monitoring.application.service.AnalysisOrchestratorService;
import com.badhabinot.monitoring.application.service.BehaviorEventService;
import com.badhabinot.monitoring.application.service.DailyReportService;
import com.badhabinot.monitoring.application.service.GroundedChatService;
import com.badhabinot.monitoring.application.service.MonitoringExperienceService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.security.SecurityRequirement;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import java.time.LocalDate;
import java.util.List;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.oauth2.jwt.Jwt;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestParam;

@RestController
@RequestMapping("/api/v1/monitoring")
@Tag(name = "Monitoring", description = "Spring-to-Python orchestration endpoints")
public class MonitoringController {

    private final AnalysisOrchestratorService analysisOrchestratorService;
    private final MonitoringExperienceService monitoringExperienceService;
    private final BehaviorEventService behaviorEventService;
    private final DailyReportService dailyReportService;
    private final GroundedChatService groundedChatService;

    public MonitoringController(
            AnalysisOrchestratorService analysisOrchestratorService,
            MonitoringExperienceService monitoringExperienceService,
            BehaviorEventService behaviorEventService,
            DailyReportService dailyReportService,
            GroundedChatService groundedChatService
    ) {
        this.analysisOrchestratorService = analysisOrchestratorService;
        this.monitoringExperienceService = monitoringExperienceService;
        this.behaviorEventService = behaviorEventService;
        this.dailyReportService = dailyReportService;
        this.groundedChatService = groundedChatService;
    }

    @PostMapping("/sessions/start")
    @Operation(summary = "Start a live monitoring session", security = @SecurityRequirement(name = "bearerAuth"))
    public SessionStartResponse startSession(@AuthenticationPrincipal Jwt jwt, @Valid @RequestBody SessionStartRequest request) {
        return monitoringExperienceService.startSession(jwt, request);
    }

    @PostMapping("/sessions/{sessionId}/stop")
    @Operation(summary = "Stop a live monitoring session", security = @SecurityRequirement(name = "bearerAuth"))
    public SessionStopResponse stopSession(@AuthenticationPrincipal Jwt jwt, @PathVariable("sessionId") String sessionId) {
        return monitoringExperienceService.stopSession(jwt, sessionId);
    }

    @PostMapping("/analyze")
    @Operation(summary = "Analyze a frame through the vision and AI microservices", security = @SecurityRequirement(name = "bearerAuth"))
    public AnalyzeFrameResponse analyze(@AuthenticationPrincipal Jwt jwt, @Valid @RequestBody AnalyzeFrameRequest request) {
        return analysisOrchestratorService.analyze(jwt, request);
    }

    @GetMapping("/jobs/{analysisId}")
    @Operation(summary = "Return the short-lived orchestration state for an analysis job", security = @SecurityRequirement(name = "bearerAuth"))
    public AnalysisJobStatusResponse analysisJob(@AuthenticationPrincipal Jwt jwt, @PathVariable("analysisId") String analysisId) {
        return analysisOrchestratorService.getJobStatus(jwt, analysisId);
    }

    @GetMapping("/dashboard")
    @Operation(summary = "Return the dashboard screen payload", security = @SecurityRequirement(name = "bearerAuth"))
    public DashboardResponse dashboard(@AuthenticationPrincipal Jwt jwt) {
        return monitoringExperienceService.getDashboard(jwt);
    }

    @GetMapping("/activities")
    @Operation(summary = "Return recent activity feed items", security = @SecurityRequirement(name = "bearerAuth"))
    public List<ActivityItemResponse> activities(
            @AuthenticationPrincipal Jwt jwt,
            @RequestParam(name = "limit", defaultValue = "10") int limit
    ) {
        return monitoringExperienceService.getRecentActivities(jwt, limit);
    }

    @GetMapping("/events")
    @Operation(summary = "Return normalized behavior events", security = @SecurityRequirement(name = "bearerAuth"))
    public List<BehaviorEventResponse> events(
            @AuthenticationPrincipal Jwt jwt,
            @RequestParam(name = "limit", defaultValue = "12") int limit
    ) {
        return behaviorEventService.getRecentEvents(java.util.UUID.fromString(jwt.getSubject()), limit);
    }

    @GetMapping("/history/weekly")
    @Operation(summary = "Return weekly history trend for the UI history screen", security = @SecurityRequirement(name = "bearerAuth"))
    public WeeklyTrendResponse weeklyHistory(
            @AuthenticationPrincipal Jwt jwt,
            @DateTimeFormat(iso = DateTimeFormat.ISO.DATE)
            @RequestParam(name = "from", required = false) LocalDate from
    ) {
        return monitoringExperienceService.getWeeklyTrend(jwt, from);
    }

    @PostMapping("/hydration/log")
    @Operation(summary = "Log manual water intake from the dashboard", security = @SecurityRequirement(name = "bearerAuth"))
    public HydrationLogResponse logHydration(@AuthenticationPrincipal Jwt jwt, @Valid @RequestBody HydrationLogRequest request) {
        return monitoringExperienceService.logHydration(jwt, request);
    }

    @PostMapping("/reminders/trigger")
    @Operation(summary = "Trigger a reminder event for UI and scheduling workflows", security = @SecurityRequirement(name = "bearerAuth"))
    public ActivityItemResponse triggerReminder(@AuthenticationPrincipal Jwt jwt, @Valid @RequestBody ReminderTriggerRequest request) {
        return monitoringExperienceService.triggerReminder(jwt, request);
    }

    @GetMapping("/reports/daily")
    @Operation(summary = "Generate or return the persisted daily behavior report", security = @SecurityRequirement(name = "bearerAuth"))
    public DailyReportResponse dailyReport(
            @AuthenticationPrincipal Jwt jwt,
            @DateTimeFormat(iso = DateTimeFormat.ISO.DATE)
            @RequestParam(name = "date", required = false) LocalDate date
    ) {
        return dailyReportService.getDailyReport(jwt, date);
    }

    @PostMapping("/chat")
    @Operation(summary = "Respond to a grounded behavior-history chat message", security = @SecurityRequirement(name = "bearerAuth"))
    public ChatResponse chat(@AuthenticationPrincipal Jwt jwt, @Valid @RequestBody ChatRequest request) {
        return groundedChatService.chat(jwt, request);
    }
}
