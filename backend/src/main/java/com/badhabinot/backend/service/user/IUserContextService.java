package com.badhabinot.backend.service.user;

import com.badhabinot.backend.dto.monitoring.InternalUserAnalysisContext;
import com.badhabinot.backend.dto.user.ConsentResponse;
import com.badhabinot.backend.dto.user.InternalUserAnalysisContextResponse;
import com.badhabinot.backend.dto.user.InternalUserBootstrapRequest;
import com.badhabinot.backend.dto.user.SettingsResponse;
import com.badhabinot.backend.dto.user.UpdateConsentsRequest;
import com.badhabinot.backend.dto.user.UpdateProfileRequest;
import com.badhabinot.backend.dto.user.UpdateSettingsRequest;
import com.badhabinot.backend.dto.user.UserContextResponse;
import com.badhabinot.backend.dto.user.UserProfileResponse;
import com.badhabinot.backend.security.CurrentUserClaims;
import java.util.UUID;

public interface IUserContextService {
    UserContextResponse getContext(CurrentUserClaims claims);
    UserProfileResponse updateProfile(CurrentUserClaims claims, UpdateProfileRequest request);
    SettingsResponse getSettings(CurrentUserClaims claims);
    SettingsResponse updateSettings(CurrentUserClaims claims, UpdateSettingsRequest request);
    ConsentResponse getConsents(CurrentUserClaims claims);
    ConsentResponse updateConsents(CurrentUserClaims claims, UpdateConsentsRequest request);
    void bootstrap(InternalUserBootstrapRequest request);
    void bootstrap(UUID userId, String email, String displayName, String timezone, String locale);
    InternalUserAnalysisContextResponse getInternalAnalysisContext(UUID userId);
    InternalUserAnalysisContext getMonitoringAnalysisContext(UUID userId);
}
