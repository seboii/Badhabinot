package com.badhabinot.backend.config;

import java.time.Duration;
import org.springframework.boot.context.properties.ConfigurationProperties;

@ConfigurationProperties(prefix = "integration")
public record IntegrationProperties(
        String internalApiKey,
        Downstream visionService,
        Downstream aiService
) {
    public record Downstream(
            String baseUrl,
            Duration connectTimeout,
            Duration readTimeout
    ) {
    }
}
