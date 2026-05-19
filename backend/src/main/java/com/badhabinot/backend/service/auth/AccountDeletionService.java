package com.badhabinot.backend.service.auth;

import com.badhabinot.backend.common.exception.auth.AuthenticationFailedException;
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
import java.util.UUID;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

@Service
public class AccountDeletionService {

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

    public AccountDeletionService(
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
            ReminderEventRepository reminderEventRepository
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
    }

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
    }
}
