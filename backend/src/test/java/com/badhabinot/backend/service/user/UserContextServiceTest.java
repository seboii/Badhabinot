package com.badhabinot.backend.service.user;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.badhabinot.backend.model.user.ModelMode;
import com.badhabinot.backend.model.user.Sensitivity;
import com.badhabinot.backend.model.user.UserConsent;
import com.badhabinot.backend.model.user.UserProfile;
import com.badhabinot.backend.model.user.UserSettings;
import com.badhabinot.backend.repository.user.UserConsentRepository;
import com.badhabinot.backend.repository.user.UserProfileRepository;
import com.badhabinot.backend.repository.user.UserSettingsRepository;
import java.time.LocalTime;
import java.util.Optional;
import java.util.UUID;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

@ExtendWith(MockitoExtension.class)
class UserContextServiceTest {

    @Mock
    private UserProfileRepository userProfileRepository;

    @Mock
    private UserSettingsRepository userSettingsRepository;

    @Mock
    private UserConsentRepository userConsentRepository;

    private UserContextService userContextService;

    @BeforeEach
    void setUp() {
        userContextService = new UserContextService(userProfileRepository, userSettingsRepository, userConsentRepository);
    }

    @Test
    void getMonitoringAnalysisContextMapsStoredUserState() {
        UUID userId = UUID.randomUUID();
        UserProfile profile = UserProfile.create(userId, "alice@example.com", "Alice", "Europe/Istanbul", "tr-TR");
        UserSettings settings = UserSettings.createDefault(userId);
        settings.update(
                Sensitivity.HIGH,
                3200,
                45,
                90,
                true,
                LocalTime.of(22, 30),
                LocalTime.of(7, 15),
                ModelMode.API,
                true
        );
        UserConsent consent = UserConsent.createDefault(userId);
        consent.update(true, true, true);

        when(userProfileRepository.findById(userId)).thenReturn(Optional.of(profile));
        when(userSettingsRepository.findById(userId)).thenReturn(Optional.of(settings));
        when(userConsentRepository.findById(userId)).thenReturn(Optional.of(consent));

        var context = userContextService.getMonitoringAnalysisContext(userId);

        assertThat(context.userId()).isEqualTo(userId.toString());
        assertThat(context.timezone()).isEqualTo("Europe/Istanbul");
        assertThat(context.sensitivity()).isEqualTo("HIGH");
        assertThat(context.modelMode()).isEqualTo("API");
        assertThat(context.quietHoursStart()).isEqualTo("22:30");
        assertThat(context.quietHoursEnd()).isEqualTo("07:15");
        assertThat(context.remoteInferenceAccepted()).isTrue();
    }

    @Test
    void bootstrapCreatesMissingProfileSettingsAndConsent() {
        UUID userId = UUID.randomUUID();

        when(userProfileRepository.findById(userId)).thenReturn(Optional.empty());
        when(userProfileRepository.save(any())).thenAnswer(invocation -> invocation.getArgument(0));
        when(userSettingsRepository.findById(userId)).thenReturn(Optional.empty());
        when(userSettingsRepository.save(any())).thenAnswer(invocation -> invocation.getArgument(0));
        when(userConsentRepository.findById(userId)).thenReturn(Optional.empty());
        when(userConsentRepository.save(any())).thenAnswer(invocation -> invocation.getArgument(0));

        userContextService.bootstrap(userId, "alice@example.com", "Alice", "UTC", "en-US");

        verify(userProfileRepository).save(any(UserProfile.class));
        verify(userSettingsRepository).save(any(UserSettings.class));
        verify(userConsentRepository).save(any(UserConsent.class));
    }
}
