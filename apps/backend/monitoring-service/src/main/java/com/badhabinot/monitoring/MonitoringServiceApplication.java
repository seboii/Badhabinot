package com.badhabinot.monitoring;

import com.badhabinot.monitoring.infrastructure.config.IntegrationProperties;
import com.badhabinot.monitoring.infrastructure.config.JwtProperties;
import com.badhabinot.monitoring.infrastructure.config.MonitoringRedisProperties;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.context.properties.EnableConfigurationProperties;

@SpringBootApplication
@EnableConfigurationProperties({IntegrationProperties.class, JwtProperties.class, MonitoringRedisProperties.class})
public class MonitoringServiceApplication {

    public static void main(String[] args) {
        SpringApplication.run(MonitoringServiceApplication.class, args);
    }
}
