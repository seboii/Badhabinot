package com.badhabinot.user.infrastructure.config;

import java.time.Duration;
import org.springframework.boot.context.properties.ConfigurationProperties;

@ConfigurationProperties(prefix = "user.cache")
public record UserCacheProperties(Duration ttl) {

    public UserCacheProperties {
        ttl = ttl == null ? Duration.ofMinutes(5) : ttl;
    }
}
