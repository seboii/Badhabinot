package com.badhabinot.user.application.service;

import com.badhabinot.user.application.dto.ConsentResponse;
import com.badhabinot.user.application.dto.InternalUserBootstrapRequest;
import com.badhabinot.user.application.dto.InternalUserAnalysisContextResponse;
import com.badhabinot.user.application.dto.SettingsResponse;
import com.badhabinot.user.application.dto.UpdateConsentsRequest;
import com.badhabinot.user.application.dto.UpdateProfileRequest;
import com.badhabinot.user.application.dto.UpdateSettingsRequest;
import com.badhabinot.user.application.dto.UserContextResponse;
import com.badhabinot.user.application.dto.UserProfileResponse;
import com.badhabinot.user.domain.model.UserConsent;
import com.badhabinot.user.domain.model.UserProfile;
import com.badhabinot.user.domain.model.UserSettings;
import com.badhabinot.user.domain.repository.UserConsentRepository;
import com.badhabinot.user.domain.repository.UserProfileRepository;
import com.badhabinot.user.domain.repository.UserSettingsRepository;
import com.badhabinot.user.infrastructure.security.CurrentUserClaims;
import java.util.UUID;
import org.springframework.cache.annotation.CacheEvict;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.cache.annotation.Caching;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class UserContextService {

    private final UserProfileRepository userProfileRepository;
    private final UserSettingsRepository userSettingsRepository;
    private final UserConsentRepository userConsentRepository;

    public UserContextService(
            UserProfileRepository userProfileRepository,
            UserSettingsRepository userSettingsRepository,
            UserConsentRepository userConsentRepository
    ) {
        this.userProfileRepository = userProfileRepository;
        this.userSettingsRepository = userSettingsRepository;
        this.userConsentRepository = userConsentRepository;
    }

    @Transactional
    @Cacheable(cacheNames = "user-context", key = "#claims.userId.toString()")
    public UserContextResponse getContext(CurrentUserClaims claims) {
        UserProfile profile = ensureProfile(claims.userId(), claims.email());
        UserSettings settings = ensureSettings(claims.userId());
        UserConsent consent = ensureConsent(claims.userId());
        return toContextResponse(profile, settings, consent);
    }

    @Transactional
    @Caching(evict = {
            @CacheEvict(cacheNames = "user-context", key = "#claims.userId.toString()"),
            @CacheEvict(cacheNames = "analysis-context", key = "#claims.userId.toString()")
    })
    public UserProfileResponse updateProfile(CurrentUserClaims claims, UpdateProfileRequest request) {
        UserProfile profile = ensureProfile(claims.userId(), claims.email());
        ensureSettings(claims.userId());
        ensureConsent(claims.userId());

        profile.updateProfile(request.displayName(), request.timezone(), request.locale());
        return toProfileResponse(userProfileRepository.save(profile));
    }

    @Transactional
    @Cacheable(cacheNames = "user-settings", key = "#claims.userId.toString()")
    public SettingsResponse getSettings(CurrentUserClaims claims) {
        ensureProfile(claims.userId(), claims.email());
        return toSettingsResponse(ensureSettings(claims.userId()));
    }

    @Transactional
    @Caching(evict = {
            @CacheEvict(cacheNames = "user-context", key = "#claims.userId.toString()"),
            @CacheEvict(cacheNames = "user-settings", key = "#claims.userId.toString()"),
            @CacheEvict(cacheNames = "analysis-context", key = "#claims.userId.toString()")
    })
    public SettingsResponse updateSettings(CurrentUserClaims claims, UpdateSettingsRequest request) {
        ensureProfile(claims.userId(), claims.email());
        ensureConsent(claims.userId());
        UserSettings settings = ensureSettings(claims.userId());
        settings.update(
                request.sensitivity(),
                request.waterGoalMl(),
                request.waterIntervalMin(),
                request.exerciseIntervalMin(),
                request.quietHoursEnabled(),
                request.quietHoursStart(),
                request.quietHoursEnd(),
                request.modelMode(),
                request.notificationsEnabled()
        );
        return toSettingsResponse(userSettingsRepository.save(settings));
    }

    @Transactional
    @Cacheable(cacheNames = "user-consents", key = "#claims.userId.toString()")
    public ConsentResponse getConsents(CurrentUserClaims claims) {
        ensureProfile(claims.userId(), claims.email());
        ensureSettings(claims.userId());
        return toConsentResponse(ensureConsent(claims.userId()));
    }

    @Transactional
    @Caching(evict = {
            @CacheEvict(cacheNames = "user-context", key = "#claims.userId.toString()"),
            @CacheEvict(cacheNames = "user-consents", key = "#claims.userId.toString()"),
            @CacheEvict(cacheNames = "analysis-context", key = "#claims.userId.toString()")
    })
    public ConsentResponse updateConsents(CurrentUserClaims claims, UpdateConsentsRequest request) {
        ensureProfile(claims.userId(), claims.email());
        ensureSettings(claims.userId());
        UserConsent consent = ensureConsent(claims.userId());
        consent.update(
                request.privacyPolicyAccepted(),
                request.cameraMonitoringAccepted(),
                request.remoteInferenceAccepted()
        );
        return toConsentResponse(userConsentRepository.save(consent));
    }

    @Transactional
    @Caching(evict = {
            @CacheEvict(cacheNames = "user-context", key = "#request.userId.toString()"),
            @CacheEvict(cacheNames = "user-settings", key = "#request.userId.toString()"),
            @CacheEvict(cacheNames = "user-consents", key = "#request.userId.toString()"),
            @CacheEvict(cacheNames = "analysis-context", key = "#request.userId.toString()")
    })
    public void bootstrap(InternalUserBootstrapRequest request) {
        UserProfile profile = userProfileRepository.findById(request.userId())
                .orElseGet(() -> UserProfile.create(
                        request.userId(),
                        request.email(),
                        request.displayName(),
                        request.timezone(),
                        request.locale()
                ));
        profile.updateFromBootstrap(request.email(), request.displayName(), request.timezone(), request.locale());
        userProfileRepository.save(profile);
        ensureSettings(request.userId());
        ensureConsent(request.userId());
    }

    @Transactional
    @Cacheable(cacheNames = "analysis-context", key = "#userId.toString()")
    public InternalUserAnalysisContextResponse getInternalAnalysisContext(UUID userId) {
        UserProfile profile = userProfileRepository.findById(userId)
                .orElseThrow(() -> new IllegalArgumentException("User profile not found"));
        UserSettings settings = ensureSettings(userId);
        UserConsent consent = ensureConsent(userId);
        return new InternalUserAnalysisContextResponse(
                userId,
                profile.getTimezone(),
                settings.getSensitivity(),
                settings.getModelMode(),
                consent.isCameraMonitoringAccepted(),
                settings.getWaterGoalMl(),
                settings.getWaterIntervalMin(),
                settings.getExerciseIntervalMin(),
                settings.isNotificationsEnabled(),
                settings.isQuietHoursEnabled(),
                settings.getQuietHoursStart(),
                settings.getQuietHoursEnd(),
                consent.isRemoteInferenceAccepted()
        );
    }

    private UserProfile ensureProfile(UUID userId, String email) {
        return userProfileRepository.findById(userId)
                .orElseGet(() -> userProfileRepository.save(UserProfile.create(
                        userId,
                        email,
                        deriveDisplayName(email),
                        "Europe/Istanbul",
                        "tr-TR"
                )));
    }

    private UserSettings ensureSettings(UUID userId) {
        return userSettingsRepository.findById(userId)
                .orElseGet(() -> userSettingsRepository.save(UserSettings.createDefault(userId)));
    }

    private UserConsent ensureConsent(UUID userId) {
        return userConsentRepository.findById(userId)
                .orElseGet(() -> userConsentRepository.save(UserConsent.createDefault(userId)));
    }

    private String deriveDisplayName(String email) {
        int atIndex = email.indexOf('@');
        return atIndex > 0 ? email.substring(0, atIndex) : email;
    }

    private UserContextResponse toContextResponse(UserProfile profile, UserSettings settings, UserConsent consent) {
        return new UserContextResponse(
                profile.getUserId(),
                profile.getEmail(),
                profile.getDisplayName(),
                profile.getTimezone(),
                profile.getLocale(),
                toSettingsResponse(settings),
                toConsentResponse(consent)
        );
    }

    private UserProfileResponse toProfileResponse(UserProfile profile) {
        return new UserProfileResponse(
                profile.getUserId(),
                profile.getEmail(),
                profile.getDisplayName(),
                profile.getTimezone(),
                profile.getLocale(),
                profile.getUpdatedAt()
        );
    }

    private SettingsResponse toSettingsResponse(UserSettings settings) {
        return new SettingsResponse(
                settings.getSensitivity(),
                settings.getWaterGoalMl(),
                settings.getWaterIntervalMin(),
                settings.getExerciseIntervalMin(),
                settings.isQuietHoursEnabled(),
                settings.getQuietHoursStart(),
                settings.getQuietHoursEnd(),
                settings.getModelMode(),
                settings.isNotificationsEnabled(),
                settings.getUpdatedAt()
        );
    }

    private ConsentResponse toConsentResponse(UserConsent consent) {
        return new ConsentResponse(
                consent.isPrivacyPolicyAccepted(),
                consent.isCameraMonitoringAccepted(),
                consent.isRemoteInferenceAccepted(),
                consent.getAcceptedAt(),
                consent.getUpdatedAt()
        );
    }
}
