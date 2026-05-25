package com.badhabinot.backend.service.auth;

import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.doThrow;
import static org.mockito.Mockito.inOrder;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.badhabinot.backend.common.exception.auth.AuthenticationFailedException;
import com.badhabinot.backend.common.exception.monitoring.DownstreamServiceException;
import com.badhabinot.backend.integration.python.VisionServiceClient;
import com.badhabinot.backend.model.auth.AccountStatus;
import com.badhabinot.backend.model.auth.AuthUser;
import com.badhabinot.backend.model.auth.UserRole;
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
import com.badhabinot.backend.service.auth.impl.AccountDeletionServiceImpl;
import java.util.Optional;
import java.util.UUID;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InOrder;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.cache.Cache;
import org.springframework.cache.CacheManager;
import org.springframework.security.crypto.password.PasswordEncoder;

@ExtendWith(MockitoExtension.class)
class AccountDeletionServiceTest {

    @Mock private AuthUserRepository authUserRepository;
    @Mock private RefreshTokenRepository refreshTokenRepository;
    @Mock private PasswordEncoder passwordEncoder;
    @Mock private UserProfileRepository userProfileRepository;
    @Mock private UserSettingsRepository userSettingsRepository;
    @Mock private UserConsentRepository userConsentRepository;
    @Mock private ActivityFeedRepository activityFeedRepository;
    @Mock private AnalysisJobRepository analysisJobRepository;
    @Mock private BehaviorEventRepository behaviorEventRepository;
    @Mock private ChatMessageRepository chatMessageRepository;
    @Mock private DailyReportRepository dailyReportRepository;
    @Mock private HydrationLogRepository hydrationLogRepository;
    @Mock private MonitoringSessionRepository monitoringSessionRepository;
    @Mock private ReminderEventRepository reminderEventRepository;
    @Mock private VisionServiceClient visionServiceClient;
    @Mock private CacheManager cacheManager;
    @Mock private Cache mockCache;

    @InjectMocks
    private AccountDeletionServiceImpl AccountDeletionServiceImpl;

    @Test
    void deleteAccountCascadesAllTablesAndDeletesFaceProfile() {
        UUID userId = UUID.randomUUID();
        AuthUser user = AuthUser.create("alice@example.com", "hashed-pw", UserRole.USER, AccountStatus.ACTIVE);

        when(authUserRepository.findById(userId)).thenReturn(Optional.of(user));
        when(passwordEncoder.matches("correct-pw", "hashed-pw")).thenReturn(true);
        when(cacheManager.getCache(any())).thenReturn(mockCache);

        AccountDeletionServiceImpl.deleteAccount(userId, "correct-pw");

        // Verify all monitoring repositories are cleared
        verify(activityFeedRepository).deleteByUserId(userId);
        verify(behaviorEventRepository).deleteByUserId(userId);
        verify(chatMessageRepository).deleteByUserId(userId);
        verify(dailyReportRepository).deleteByUserId(userId);
        verify(hydrationLogRepository).deleteByUserId(userId);
        verify(reminderEventRepository).deleteByUserId(userId);
        verify(analysisJobRepository).deleteByUserId(userId);
        verify(monitoringSessionRepository).deleteByUserId(userId);

        // Verify user DB cleared
        verify(userConsentRepository).deleteById(userId);
        verify(userSettingsRepository).deleteById(userId);
        verify(userProfileRepository).deleteById(userId);

        // Verify auth DB cleared
        verify(refreshTokenRepository).deleteByUserId(userId);
        verify(authUserRepository).deleteById(userId);

        // Verify face profile deletion is called
        verify(visionServiceClient).deleteFaceProfile(userId.toString());

        // Verify cache eviction
        verify(mockCache, org.mockito.Mockito.atLeast(1)).evict(userId.toString());
    }

    @Test
    void deleteAccountRejectsWrongPassword() {
        UUID userId = UUID.randomUUID();
        AuthUser user = AuthUser.create("alice@example.com", "hashed-pw", UserRole.USER, AccountStatus.ACTIVE);

        when(authUserRepository.findById(userId)).thenReturn(Optional.of(user));
        when(passwordEncoder.matches("wrong-pw", "hashed-pw")).thenReturn(false);

        assertThatThrownBy(() -> AccountDeletionServiceImpl.deleteAccount(userId, "wrong-pw"))
                .isInstanceOf(IllegalArgumentException.class);

        // Nothing should be deleted — only the lookup is expected, not any delete
        org.mockito.Mockito.verifyNoInteractions(
                activityFeedRepository, userProfileRepository, visionServiceClient
        );
        org.mockito.Mockito.verify(authUserRepository, org.mockito.Mockito.never()).deleteById(any());
    }

    @Test
    void deleteAccountRejectsUnknownUser() {
        UUID userId = UUID.randomUUID();
        when(authUserRepository.findById(userId)).thenReturn(Optional.empty());

        assertThatThrownBy(() -> AccountDeletionServiceImpl.deleteAccount(userId, "any-pw"))
                .isInstanceOf(AuthenticationFailedException.class);
    }

    @Test
    void deleteAccountContinuesWhenFaceProfileDeletionFails() {
        UUID userId = UUID.randomUUID();
        AuthUser user = AuthUser.create("bob@example.com", "hashed-pw", UserRole.USER, AccountStatus.ACTIVE);

        when(authUserRepository.findById(userId)).thenReturn(Optional.of(user));
        when(passwordEncoder.matches("correct-pw", "hashed-pw")).thenReturn(true);
        when(cacheManager.getCache(any())).thenReturn(mockCache);
        doThrow(new DownstreamServiceException("vision_service_unavailable", "Vision service down"))
                .when(visionServiceClient).deleteFaceProfile(userId.toString());

        // Should not throw — face profile deletion failure is non-fatal
        AccountDeletionServiceImpl.deleteAccount(userId, "correct-pw");

        // All DB deletions should still have been called
        verify(authUserRepository).deleteById(userId);
        verify(refreshTokenRepository).deleteByUserId(userId);
    }
}
