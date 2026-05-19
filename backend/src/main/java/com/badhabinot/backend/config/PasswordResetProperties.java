package com.badhabinot.backend.config;

import org.springframework.boot.context.properties.ConfigurationProperties;

@ConfigurationProperties(prefix = "app.password-reset")
public record PasswordResetProperties(String resetUrlTemplate) {
}
