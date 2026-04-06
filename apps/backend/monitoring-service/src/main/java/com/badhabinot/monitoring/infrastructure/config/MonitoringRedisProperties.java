package com.badhabinot.monitoring.infrastructure.config;

import java.time.Duration;
import org.springframework.boot.context.properties.ConfigurationProperties;

@ConfigurationProperties(prefix = "monitoring.redis")
public record MonitoringRedisProperties(
        String analysisJobKeyPrefix,
        Duration analysisJobTtl
) {
    public MonitoringRedisProperties {
        analysisJobKeyPrefix = analysisJobKeyPrefix == null || analysisJobKeyPrefix.isBlank()
                ? "badhabinot:monitoring:analysis-job:"
                : analysisJobKeyPrefix;
        analysisJobTtl = analysisJobTtl == null ? Duration.ofMinutes(15) : analysisJobTtl;
    }
}
