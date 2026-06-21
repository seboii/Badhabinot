package com.badhabinot.backend.service.admin.impl;

import com.badhabinot.backend.dto.admin.AdminReportSummary;
import com.badhabinot.backend.dto.admin.AdminStats;
import com.badhabinot.backend.dto.admin.AdminUserDetail;
import com.badhabinot.backend.dto.admin.AdminUserListResponse;
import com.badhabinot.backend.dto.admin.AdminUserAiSettingsRequest;
import com.badhabinot.backend.dto.admin.AdminUserSummary;
import com.badhabinot.backend.dto.monitoring.FaceRegisterResponse;
import com.badhabinot.backend.dto.user.UpdateSettingsRequest;
import com.badhabinot.backend.integration.python.VisionServiceClient;
import com.badhabinot.backend.model.auth.AuthUser;
import com.badhabinot.backend.model.auth.UserRole;
import com.badhabinot.backend.model.user.ChatPersona;
import com.badhabinot.backend.model.user.ModelMode;
import com.badhabinot.backend.model.user.Sensitivity;
import com.badhabinot.backend.model.user.UserSettings;
import java.time.LocalTime;
import com.badhabinot.backend.repository.auth.AuthUserRepository;
import com.badhabinot.backend.repository.monitoring.AnalysisJobRepository;
import com.badhabinot.backend.repository.monitoring.BehaviorEventRepository;
import com.badhabinot.backend.repository.monitoring.ChatMessageRepository;
import com.badhabinot.backend.repository.monitoring.DailyReportRepository;
import com.badhabinot.backend.repository.monitoring.MonitoringSessionRepository;
import com.badhabinot.backend.repository.user.UserConsentRepository;
import com.badhabinot.backend.repository.user.UserProfileRepository;
import com.badhabinot.backend.repository.user.UserSettingsRepository;
import com.badhabinot.backend.service.admin.IAdminService;
import com.badhabinot.backend.service.auth.IAccountDeletionService;
import com.badhabinot.backend.service.user.IUserContextService;
import java.util.List;
import java.util.UUID;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.stereotype.Service;

@Service
public class AdminServiceImpl implements IAdminService {

    private final AuthUserRepository authUserRepository;
    private final UserProfileRepository userProfileRepository;
    private final UserSettingsRepository userSettingsRepository;
    private final UserConsentRepository userConsentRepository;
    private final MonitoringSessionRepository monitoringSessionRepository;
    private final AnalysisJobRepository analysisJobRepository;
    private final BehaviorEventRepository behaviorEventRepository;
    private final DailyReportRepository dailyReportRepository;
    private final ChatMessageRepository chatMessageRepository;
    private final IAccountDeletionService accountDeletionService;
    private final VisionServiceClient visionServiceClient;
    private final IUserContextService userContextService;

    public AdminServiceImpl(
            AuthUserRepository authUserRepository,
            UserProfileRepository userProfileRepository,
            UserSettingsRepository userSettingsRepository,
            UserConsentRepository userConsentRepository,
            MonitoringSessionRepository monitoringSessionRepository,
            AnalysisJobRepository analysisJobRepository,
            BehaviorEventRepository behaviorEventRepository,
            DailyReportRepository dailyReportRepository,
            ChatMessageRepository chatMessageRepository,
            IAccountDeletionService accountDeletionService,
            VisionServiceClient visionServiceClient,
            IUserContextService userContextService
    ) {
        this.userContextService = userContextService;
        this.authUserRepository = authUserRepository;
        this.userProfileRepository = userProfileRepository;
        this.userSettingsRepository = userSettingsRepository;
        this.userConsentRepository = userConsentRepository;
        this.monitoringSessionRepository = monitoringSessionRepository;
        this.analysisJobRepository = analysisJobRepository;
        this.behaviorEventRepository = behaviorEventRepository;
        this.dailyReportRepository = dailyReportRepository;
        this.chatMessageRepository = chatMessageRepository;
        this.accountDeletionService = accountDeletionService;
        this.visionServiceClient = visionServiceClient;
    }

    @Override
    public AdminUserListResponse listUsers(String search, int page, int size) {
        int safePage = Math.max(0, page);
        int safeSize = Math.min(100, Math.max(1, size));
        Pageable pageable = PageRequest.of(safePage, safeSize, Sort.by(Sort.Direction.DESC, "createdAt"));

        Page<AuthUser> result = (search != null && !search.isBlank())
                ? authUserRepository.findByEmailContainingIgnoreCase(search.trim(), pageable)
                : authUserRepository.findAll(pageable);

        List<AdminUserSummary> items = result.getContent().stream()
                .map(u -> new AdminUserSummary(
                        u.getId(),
                        u.getEmail(),
                        userProfileRepository.findById(u.getId())
                                .map(p -> p.getDisplayName())
                                .orElse(null),
                        u.getRole().name(),
                        u.getStatus().name(),
                        u.getCreatedAt(),
                        u.getLastLoginAt()
                ))
                .toList();

        return new AdminUserListResponse(items, result.getTotalElements(), safePage, safeSize);
    }

    @Override
    public AdminUserDetail getUserDetail(UUID userId) {
        AuthUser user = authUserRepository.findById(userId)
                .orElseThrow(() -> new IllegalArgumentException("User not found"));

        AdminUserDetail.Profile profile = userProfileRepository.findById(userId)
                .map(p -> new AdminUserDetail.Profile(p.getDisplayName(), p.getTimezone(), p.getLocale()))
                .orElse(null);

        AdminUserDetail.Settings settings = userSettingsRepository.findById(userId)
                .map(s -> new AdminUserDetail.Settings(
                        s.getSensitivity().name(),
                        s.getModelMode().name(),
                        s.getLocalModelName(),
                        s.getOllamaBaseUrl(),
                        s.getChatPersona() != null ? s.getChatPersona().name() : "GENERAL_CHAT",
                        s.getWaterGoalMl(),
                        s.getWaterIntervalMin(),
                        s.getExerciseIntervalMin(),
                        s.isNotificationsEnabled()
                ))
                .orElse(null);

        AdminUserDetail.Consents consents = userConsentRepository.findById(userId)
                .map(c -> new AdminUserDetail.Consents(
                        c.isPrivacyPolicyAccepted(),
                        c.isCameraMonitoringAccepted(),
                        c.isRemoteInferenceAccepted()
                ))
                .orElse(null);

        AdminUserDetail.Stats stats = new AdminUserDetail.Stats(
                monitoringSessionRepository.countByUserId(userId),
                analysisJobRepository.countByUserId(userId),
                behaviorEventRepository.countByUserId(userId),
                dailyReportRepository.countByUserId(userId),
                chatMessageRepository.countByUserId(userId)
        );

        AdminUserDetail.Face face = resolveFace(userId);

        return new AdminUserDetail(
                user.getId(),
                user.getEmail(),
                user.getRole().name(),
                user.getStatus().name(),
                user.getCreatedAt(),
                user.getLastLoginAt(),
                profile,
                settings,
                consents,
                stats,
                face
        );
    }

    @Override
    public List<AdminReportSummary> getUserReports(UUID userId, int limit) {
        int safeLimit = Math.min(180, Math.max(1, limit));
        Pageable pageable = PageRequest.of(0, safeLimit);
        return dailyReportRepository.findByUserIdOrderByReportDateDesc(userId, pageable).stream()
                .map(r -> new AdminReportSummary(
                        r.getReportDate(),
                        r.getAnalysesCompleted(),
                        r.getPostureAlertCount(),
                        r.getHandMovementCount(),
                        r.getSmokingLikeCount(),
                        r.getReminderCount(),
                        r.getHydrationProgressMl(),
                        r.getWaterGoalMl(),
                        r.getPoorPostureRatio() == null ? 0.0 : r.getPoorPostureRatio().doubleValue(),
                        r.getSummary(),
                        r.getGeneratedAt()
                ))
                .toList();
    }

    @Override
    public void deleteUser(UUID userId) {
        accountDeletionService.deleteAccountAsAdmin(userId);
    }

    @Override
    public void resetUserData(UUID userId) {
        accountDeletionService.resetUserData(userId);
    }

    @Override
    @org.springframework.transaction.annotation.Transactional(transactionManager = "authTransactionManager")
    public void approveUser(UUID userId) {
        AuthUser user = authUserRepository.findById(userId)
                .orElseThrow(() -> new IllegalArgumentException("User not found"));
        user.activate();
        authUserRepository.save(user);
    }

    @Override
    public void updateUserAiSettings(UUID userId, AdminUserAiSettingsRequest req) {
        AuthUser user = authUserRepository.findById(userId)
                .orElseThrow(() -> new IllegalArgumentException("User not found"));
        UserSettings cur = userSettingsRepository.findById(userId).orElse(null);

        // Mevcut (AI dışı) ayarları koru, yalnızca AI/sohbet alanlarını uygula.
        Sensitivity sensitivity = cur != null ? cur.getSensitivity() : Sensitivity.MEDIUM;
        int waterGoal = cur != null ? cur.getWaterGoalMl() : 2500;
        int waterInterval = cur != null ? cur.getWaterIntervalMin() : 60;
        int exerciseInterval = cur != null ? cur.getExerciseIntervalMin() : 60;
        boolean quietEnabled = cur != null && cur.isQuietHoursEnabled();
        LocalTime quietStart = cur != null ? cur.getQuietHoursStart() : LocalTime.of(22, 0);
        LocalTime quietEnd = cur != null ? cur.getQuietHoursEnd() : LocalTime.of(8, 0);
        boolean notifications = cur == null || cur.isNotificationsEnabled();
        String customPrompt = cur != null ? cur.getCustomSystemPrompt() : null;

        String localModel = (req.localModelName() != null && !req.localModelName().isBlank())
                ? req.localModelName().trim()
                : (cur != null ? cur.getLocalModelName() : "badhabinot-coach:latest");
        String ollamaUrl = (req.ollamaBaseUrl() != null && !req.ollamaBaseUrl().isBlank())
                ? req.ollamaBaseUrl().trim()
                : (cur != null ? cur.getOllamaBaseUrl() : "http://ollama:11434");
        ChatPersona persona = req.chatPersona() != null
                ? req.chatPersona()
                : (cur != null ? cur.getChatPersona() : ChatPersona.GENERAL_CHAT);

        UpdateSettingsRequest full = new UpdateSettingsRequest(
                sensitivity, waterGoal, waterInterval, exerciseInterval,
                quietEnabled, quietStart, quietEnd,
                req.modelMode(), notifications, localModel, ollamaUrl, persona, customPrompt
        );
        userContextService.updateSettingsForUser(userId, user.getEmail(), full);
    }

    @Override
    public AdminStats getStats() {
        return new AdminStats(
                authUserRepository.count(),
                authUserRepository.countByRole(UserRole.ADMIN),
                monitoringSessionRepository.count(),
                analysisJobRepository.count(),
                dailyReportRepository.count(),
                behaviorEventRepository.count()
        );
    }

    /** Yüz kayıt durumunu vision-service'ten al; hata olursa kayıtsız varsay. */
    private AdminUserDetail.Face resolveFace(UUID userId) {
        try {
            FaceRegisterResponse status = visionServiceClient.faceStatus(userId.toString());
            return new AdminUserDetail.Face(status.success(), status.framesEnrolled());
        } catch (Exception ex) {
            return new AdminUserDetail.Face(false, 0);
        }
    }
}
