package com.badhabinot.backend.service.auth.impl;

import com.badhabinot.backend.common.exception.auth.AuthenticationFailedException;
import com.badhabinot.backend.integration.python.VisionServiceClient;
import com.badhabinot.backend.model.auth.AuthUser;
import com.badhabinot.backend.repository.auth.AuthUserRepository;
import com.badhabinot.backend.repository.auth.RefreshTokenRepository;
import com.badhabinot.backend.repository.monitoring.ActivityFeedRepository;
import com.badhabinot.backend.repository.monitoring.AnalysisJobRepository;
import com.badhabinot.backend.repository.monitoring.BehaviorEventRepository;
import com.badhabinot.backend.repository.monitoring.ChatMessageRepository;
import com.badhabinot.backend.repository.monitoring.DailyReportRepository;
import com.badhabinot.backend.repository.monitoring.HydrationLogRepository;
import com.badhabinot.backend.repository.monitoring.MonitoringSessionRepository;
import com.badhabinot.backend.repository.monitoring.ReminderEventRepository;
import com.badhabinot.backend.repository.user.UserConsentRepository;
import com.badhabinot.backend.repository.user.UserProfileRepository;
import com.badhabinot.backend.repository.user.UserSettingsRepository;
import com.badhabinot.backend.service.auth.IAccountDeletionService;
import java.util.List;
import java.util.UUID;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.cache.CacheManager;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

@Service
public class AccountDeletionServiceImpl implements IAccountDeletionService {

    private static final Logger log = LoggerFactory.getLogger(AccountDeletionServiceImpl.class);

    private static final List<String> USER_CACHE_NAMES = List.of(
            "user-context", "user-settings", "user-consents", "analysis-context"
    );

    private final AuthUserRepository authUserRepository;
    private final RefreshTokenRepository refreshTokenRepository;
    private final PasswordEncoder passwordEncoder;
    private final UserProfileRepository userProfileRepository;
    private final UserSettingsRepository userSettingsRepository;
    private final UserConsentRepository userConsentRepository;
    private final ActivityFeedRepository activityFeedRepository;
    private final AnalysisJobRepository analysisJobRepository;
    private final BehaviorEventRepository behaviorEventRepository;
    private final ChatMessageRepository chatMessageRepository;
    private final DailyReportRepository dailyReportRepository;
    private final HydrationLogRepository hydrationLogRepository;
    private final MonitoringSessionRepository monitoringSessionRepository;
    private final ReminderEventRepository reminderEventRepository;
    private final VisionServiceClient visionServiceClient;
    private final CacheManager cacheManager;

    public AccountDeletionServiceImpl(
            AuthUserRepository authUserRepository,
            RefreshTokenRepository refreshTokenRepository,
            PasswordEncoder passwordEncoder,
            UserProfileRepository userProfileRepository,
            UserSettingsRepository userSettingsRepository,
            UserConsentRepository userConsentRepository,
            ActivityFeedRepository activityFeedRepository,
            AnalysisJobRepository analysisJobRepository,
            BehaviorEventRepository behaviorEventRepository,
            ChatMessageRepository chatMessageRepository,
            DailyReportRepository dailyReportRepository,
            HydrationLogRepository hydrationLogRepository,
            MonitoringSessionRepository monitoringSessionRepository,
            ReminderEventRepository reminderEventRepository,
            VisionServiceClient visionServiceClient,
            CacheManager cacheManager
    ) {
        this.authUserRepository = authUserRepository;
        this.refreshTokenRepository = refreshTokenRepository;
        this.passwordEncoder = passwordEncoder;
        this.userProfileRepository = userProfileRepository;
        this.userSettingsRepository = userSettingsRepository;
        this.userConsentRepository = userConsentRepository;
        this.activityFeedRepository = activityFeedRepository;
        this.analysisJobRepository = analysisJobRepository;
        this.behaviorEventRepository = behaviorEventRepository;
        this.chatMessageRepository = chatMessageRepository;
        this.dailyReportRepository = dailyReportRepository;
        this.hydrationLogRepository = hydrationLogRepository;
        this.monitoringSessionRepository = monitoringSessionRepository;
        this.reminderEventRepository = reminderEventRepository;
        this.visionServiceClient = visionServiceClient;
        this.cacheManager = cacheManager;
    }

    @Override
    public void deleteAccount(UUID userId, String password) {
        AuthUser user = authUserRepository.findById(userId)
                .orElseThrow(() -> new AuthenticationFailedException("User not found"));

        if (!passwordEncoder.matches(password, user.getPasswordHash())) {
            throw new IllegalArgumentException("Şifre hatalı");
        }

        // Delete monitoring data
        activityFeedRepository.deleteByUserId(userId);
        behaviorEventRepository.deleteByUserId(userId);
        chatMessageRepository.deleteByUserId(userId);
        dailyReportRepository.deleteByUserId(userId);
        hydrationLogRepository.deleteByUserId(userId);
        reminderEventRepository.deleteByUserId(userId);
        analysisJobRepository.deleteByUserId(userId);
        monitoringSessionRepository.deleteByUserId(userId);

        // Delete user data
        userConsentRepository.deleteById(userId);
        userSettingsRepository.deleteById(userId);
        userProfileRepository.deleteById(userId);

        // Delete auth data
        refreshTokenRepository.deleteByUserId(userId);
        authUserRepository.deleteById(userId);

        // Delete face profile from vision service (non-blocking — deletion must not fail the account removal)
        try {
            visionServiceClient.deleteFaceProfile(userId.toString());
        } catch (Exception ex) {
            log.warn("Face profile deletion failed for userId={} — continuing account deletion: {}", userId, ex.getMessage());
        }

        // Evict all user-scoped cache entries
        String userKey = userId.toString();
        for (String cacheName : USER_CACHE_NAMES) {
            var cache = cacheManager.getCache(cacheName);
            if (cache != null) {
                cache.evict(userKey);
            }
        }
    }
}
