package com.badhabinot.user.infrastructure.config;

import org.springframework.boot.context.properties.ConfigurationProperties;

@ConfigurationProperties(prefix = "security.internal")
public record InternalSecurityProperties(
        String apiKey
) {
}

