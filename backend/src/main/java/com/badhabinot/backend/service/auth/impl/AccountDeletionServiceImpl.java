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
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.cache.CacheManager;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.PlatformTransactionManager;
import org.springframework.transaction.support.TransactionTemplate;

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

    // Çapraz veritabanı silme atomik değildir; her veritabanının silmeleri kendi
    // transaction'ında çalıştırılmalı (türetilmiş deleteByUserId aktif tx ister).
    private final TransactionTemplate authTx;
    private final TransactionTemplate userTx;
    private final TransactionTemplate monitoringTx;

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
            CacheManager cacheManager,
            @Qualifier("authTransactionManager") PlatformTransactionManager authTxManager,
            @Qualifier("userTransactionManager") PlatformTransactionManager userTxManager,
            @Qualifier("monitoringTransactionManager") PlatformTransactionManager monitoringTxManager
    ) {
        this.authTx = new TransactionTemplate(authTxManager);
        this.userTx = new TransactionTemplate(userTxManager);
        this.monitoringTx = new TransactionTemplate(monitoringTxManager);
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

        purgeAccount(userId);
    }

    @Override
    public void deleteAccountAsAdmin(UUID userId) {
        authUserRepository.findById(userId)
                .orElseThrow(() -> new AuthenticationFailedException("User not found"));
        purgeAccount(userId);
        log.info("Admin deleted account userId={}", userId);
    }

    @Override
    public void resetUserData(UUID userId) {
        authUserRepository.findById(userId)
                .orElseThrow(() -> new AuthenticationFailedException("User not found"));

        // Sadece izleme + sohbet verisini sil; hesap, profil, ayarlar, onaylar kalır.
        deleteMonitoringData(userId);

        // Yüz profilini de sıfırla (non-blocking)
        try {
            visionServiceClient.deleteFaceProfile(userId.toString());
        } catch (Exception ex) {
            log.warn("Face profile reset failed for userId={} — continuing: {}", userId, ex.getMessage());
        }

        evictUserCaches(userId);
        log.info("Admin reset data for userId={}", userId);
    }

    /** Tüm DB'lerde kullanıcıya ait her şeyi siler (kaskad). Şifre doğrulaması ÇAĞIRANIN sorumluluğu. */
    private void purgeAccount(UUID userId) {
        deleteMonitoringData(userId);

        // user-service DB — satır yoksa deleteById hata fırlatır; varlık kontrolüyle koru.
        userTx.executeWithoutResult(status -> {
            if (userConsentRepository.existsById(userId)) {
                userConsentRepository.deleteById(userId);
            }
            if (userSettingsRepository.existsById(userId)) {
                userSettingsRepository.deleteById(userId);
            }
            if (userProfileRepository.existsById(userId)) {
                userProfileRepository.deleteById(userId);
            }
        });

        // auth-service DB
        authTx.executeWithoutResult(status -> {
            refreshTokenRepository.deleteByUserId(userId);
            if (authUserRepository.existsById(userId)) {
                authUserRepository.deleteById(userId);
            }
        });

        // Delete face profile from vision service (non-blocking — deletion must not fail the account removal)
        try {
            visionServiceClient.deleteFaceProfile(userId.toString());
        } catch (Exception ex) {
            log.warn("Face profile deletion failed for userId={} — continuing account deletion: {}", userId, ex.getMessage());
        }

        evictUserCaches(userId);
    }

    private void deleteMonitoringData(UUID userId) {
        // monitoring-service DB — türetilmiş deleteByUserId sorguları aktif tx ister.
        monitoringTx.executeWithoutResult(status -> {
            activityFeedRepository.deleteByUserId(userId);
            behaviorEventRepository.deleteByUserId(userId);
            chatMessageRepository.deleteByUserId(userId);
            dailyReportRepository.deleteByUserId(userId);
            hydrationLogRepository.deleteByUserId(userId);
            reminderEventRepository.deleteByUserId(userId);
            analysisJobRepository.deleteByUserId(userId);
            monitoringSessionRepository.deleteByUserId(userId);
        });
    }

    private void evictUserCaches(UUID userId) {
        String userKey = userId.toString();
        for (String cacheName : USER_CACHE_NAMES) {
            var cache = cacheManager.getCache(cacheName);
            if (cache != null) {
                cache.evict(userKey);
            }
        }
    }
}
