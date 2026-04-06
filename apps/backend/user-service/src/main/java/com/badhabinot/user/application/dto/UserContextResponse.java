package com.badhabinot.user.application.dto;

import java.util.UUID;

public record UserContextResponse(
        UUID userId,
        String email,
        String displayName,
        String timezone,
        String locale,
        SettingsResponse settings,
        ConsentResponse consents
) {
}

