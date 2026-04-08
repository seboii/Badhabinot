package com.badhabinot.backend;

import com.badhabinot.backend.config.IntegrationProperties;
import com.badhabinot.backend.config.InternalSecurityProperties;
import com.badhabinot.backend.config.JwtProperties;
import com.badhabinot.backend.config.MonitoringRedisProperties;
import com.badhabinot.backend.config.UserCacheProperties;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.cache.annotation.EnableCaching;

@SpringBootApplication
@EnableCaching
@EnableConfigurationProperties({
        JwtProperties.class,
        InternalSecurityProperties.class,
        UserCacheProperties.class,
        MonitoringRedisProperties.class,
        IntegrationProperties.class
})
public class BackendApplication {

    public static void main(String[] args) {
        SpringApplication.run(BackendApplication.class, args);
    }
}
