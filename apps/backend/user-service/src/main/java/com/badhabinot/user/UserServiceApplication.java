package com.badhabinot.user;

import com.badhabinot.user.infrastructure.config.InternalSecurityProperties;
import com.badhabinot.user.infrastructure.config.JwtProperties;
import com.badhabinot.user.infrastructure.config.UserCacheProperties;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.cache.annotation.EnableCaching;

@SpringBootApplication
@EnableCaching
@EnableConfigurationProperties({JwtProperties.class, InternalSecurityProperties.class, UserCacheProperties.class})
public class UserServiceApplication {

    public static void main(String[] args) {
        SpringApplication.run(UserServiceApplication.class, args);
    }
}
