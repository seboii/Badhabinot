package com.badhabinot.backend.controller.monitoring;

import com.badhabinot.backend.dto.monitoring.AnalyzeFrameRequest;
import com.badhabinot.backend.dto.monitoring.PushTokenRequest;
import com.badhabinot.backend.dto.monitoring.PushDeviceResponse;
import com.badhabinot.backend.service.monitoring.IPushNotificationService;
import com.badhabinot.backend.dto.monitoring.AnalyzeFrameResponse;
import com.badhabinot.backend.dto.monitoring.FaceRegisterRequest;
import com.badhabinot.backend.dto.monitoring.FaceRegisterResponse;
import com.badhabinot.backend.integration.python.VisionServiceClient;
import com.badhabinot.backend.dto.monitoring.AnalysisJobStatusResponse;
import com.badhabinot.backend.dto.monitoring.ActivityItemResponse;
import com.badhabinot.backend.dto.monitoring.DashboardResponse;
import com.badhabinot.backend.dto.monitoring.DailyReportResponse;
import com.badhabinot.backend.dto.monitoring.HydrationLogRequest;
import com.badhabinot.backend.dto.monitoring.HydrationLogResponse;
import com.badhabinot.backend.dto.monitoring.ReminderTriggerRequest;
import com.badhabinot.backend.dto.monitoring.SessionStartRequest;
import com.badhabinot.backend.dto.monitoring.SessionStartResponse;
import com.badhabinot.backend.dto.monitoring.SessionStopResponse;
import com.badhabinot.backend.dto.monitoring.WeeklyTrendResponse;
import com.badhabinot.backend.dto.monitoring.BehaviorEventResponse;
import com.badhabinot.backend.dto.monitoring.ChatHistoryResponse;
import com.badhabinot.backend.dto.monitoring.ChatRequest;
import com.badhabinot.backend.dto.monitoring.ChatResponse;
import com.badhabinot.backend.integration.python.AiChatClient;
import com.badhabinot.backend.service.monitoring.IAnalysisOrchestratorService;
import com.badhabinot.backend.service.monitoring.IBehaviorEventService;
import com.badhabinot.backend.service.monitoring.IDailyReportService;
import com.badhabinot.backend.service.monitoring.IGroundedChatService;
import com.badhabinot.backend.service.monitoring.IMonitoringExperienceService;
import com.badhabinot.backend.service.user.IUserContextService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.security.SecurityRequirement;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import java.time.LocalDate;
import java.util.List;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.http.MediaType;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.oauth2.jwt.Jwt;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

@RestController
@RequestMapping("/api/v1/monitoring")
@Tag(name = "Monitoring", description = "Spring-to-Python orchestration endpoints")
public class MonitoringController {

    private final IAnalysisOrchestratorService analysisOrchestratorService;
    private final IMonitoringExperienceService monitoringExperienceService;
    private final IBehaviorEventService behaviorEventService;
    private final IDailyReportService dailyReportService;
    private final IGroundedChatService groundedChatService;
    private final VisionServiceClient visionServiceClient;
    private final AiChatClient aiChatClient;
    private final IUserContextService userContextService;
    private final IPushNotificationService pushNotificationService;

    public MonitoringController(
            IAnalysisOrchestratorService analysisOrchestratorService,
            IMonitoringExperienceService monitoringExperienceService,
            IBehaviorEventService behaviorEventService,
            IDailyReportService dailyReportService,
            IGroundedChatService groundedChatService,
            VisionServiceClient visionServiceClient,
            AiChatClient aiChatClient,
            IUserContextService userContextService,
            IPushNotificationService pushNotificationService
    ) {
        this.analysisOrchestratorService = analysisOrchestratorService;
        this.monitoringExperienceService = monitoringExperienceService;
        this.behaviorEventService = behaviorEventService;
        this.dailyReportService = dailyReportService;
        this.groundedChatService = groundedChatService;
        this.visionServiceClient = visionServiceClient;
        this.aiChatClient = aiChatClient;
        this.userContextService = userContextService;
        this.pushNotificationService = pushNotificationService;
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
    @Operation(summary = "Return paginated activity feed items", security = @SecurityRequirement(name = "bearerAuth"))
    public List<ActivityItemResponse> activities(
            @AuthenticationPrincipal Jwt jwt,
            @RequestParam(name = "page", defaultValue = "0") int page,
            @RequestParam(name = "size", defaultValue = "15") int size
    ) {
        return monitoringExperienceService.getRecentActivities(jwt, page, size);
    }

    @GetMapping("/events")
    @Operation(summary = "Return normalized behavior events", security = @SecurityRequirement(name = "bearerAuth"))
    public List<BehaviorEventResponse> events(
            @AuthenticationPrincipal Jwt jwt,
            @RequestParam(name = "page", defaultValue = "0") int page,
            @RequestParam(name = "size", defaultValue = "15") int size
    ) {
        return behaviorEventService.getRecentEvents(java.util.UUID.fromString(jwt.getSubject()), page, size);
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

    @PostMapping(value = "/chat/stream", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    @Operation(summary = "Stream a grounded chat response as SSE tokens", security = @SecurityRequirement(name = "bearerAuth"))
    public SseEmitter chatStream(@AuthenticationPrincipal Jwt jwt, @Valid @RequestBody ChatRequest request) {
        return groundedChatService.chatStream(jwt, request);
    }

    @GetMapping("/chat/history")
    @Operation(summary = "Return recent chat history for the latest or requested conversation", security = @SecurityRequirement(name = "bearerAuth"))
    public ChatHistoryResponse chatHistory(
            @AuthenticationPrincipal Jwt jwt,
            @RequestParam(name = "conversation_id", required = false) String conversationId,
            @RequestParam(name = "limit", defaultValue = "40") int limit
    ) {
        return groundedChatService.history(jwt, conversationId, limit);
    }

    // ── Phase 2 — Face Registration endpoints ─────────────────────────────

    @PostMapping("/face/register")
    @Operation(summary = "Submit a camera frame to enrol the authenticated user's face", security = @SecurityRequirement(name = "bearerAuth"))
    public FaceRegisterResponse registerFace(
            @AuthenticationPrincipal Jwt jwt,
            @Valid @RequestBody FaceRegisterRequest request
    ) {
        String userId = jwt.getSubject();
        return visionServiceClient.registerFace(userId, request);
    }

    @GetMapping("/face/status")
    @Operation(summary = "Return face enrolment status for the authenticated user", security = @SecurityRequirement(name = "bearerAuth"))
    public FaceRegisterResponse faceStatus(@AuthenticationPrincipal Jwt jwt) {
        String userId = jwt.getSubject();
        return visionServiceClient.faceStatus(userId);
    }

    @org.springframework.web.bind.annotation.DeleteMapping("/face")
    @Operation(summary = "Delete the authenticated user's stored face profile", security = @SecurityRequirement(name = "bearerAuth"))
    public void deleteFaceProfile(@AuthenticationPrincipal Jwt jwt) {
        String userId = jwt.getSubject();
        visionServiceClient.deleteFaceProfile(userId);
    }

    // ── Local AI ──────────────────────────────────────────────────────────────

    @GetMapping("/ai/ollama/health")
    @Operation(summary = "Proxy Ollama connectivity check through the ai-service using the user's saved settings", security = @SecurityRequirement(name = "bearerAuth"))
    public java.util.Map<String, Object> ollamaHealth(@AuthenticationPrincipal Jwt jwt) {
        java.util.UUID userId = java.util.UUID.fromString(jwt.getSubject());
        com.badhabinot.backend.dto.monitoring.InternalUserAnalysisContext ctx = userContextService.getMonitoringAnalysisContext(userId);
        return aiChatClient.ollamaHealth(ctx.ollamaBaseUrl(), ctx.localModelName());
    }

    // ── Push Notifications ───────────────────────────────────────────────────

    @PostMapping("/push/register")
    @Operation(summary = "Register an FCM push token for this user", security = @SecurityRequirement(name = "bearerAuth"))
    public PushDeviceResponse registerPushToken(@AuthenticationPrincipal Jwt jwt,
                                                 @Valid @RequestBody PushTokenRequest request) {
        java.util.UUID userId = java.util.UUID.fromString(jwt.getSubject());
        pushNotificationService.registerToken(userId, request.getToken(),
                request.getPlatform(), request.getDeviceName());
        return new PushDeviceResponse(null, request.getPlatform(),
                request.getDeviceName(), true, java.time.Instant.now());
    }

    @DeleteMapping("/push/unregister/{token}")
    @Operation(summary = "Unregister an FCM push token", security = @SecurityRequirement(name = "bearerAuth"))
    public void unregisterPushToken(@PathVariable("token") String token) {
        pushNotificationService.unregisterToken(token);
    }
}
