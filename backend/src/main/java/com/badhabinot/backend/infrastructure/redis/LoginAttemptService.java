package com.badhabinot.backend.infrastructure.redis;

import com.badhabinot.backend.common.exception.auth.TooManyLoginAttemptsException;
import java.time.Duration;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Component;

@Component
public class LoginAttemptService {

    private static final Logger log = LoggerFactory.getLogger(LoginAttemptService.class);

    private static final String KEY_PREFIX = "login:attempts:";
    private static final int MAX_ATTEMPTS = 5;
    private static final Duration WINDOW = Duration.ofMinutes(15);

    private final StringRedisTemplate redisTemplate;

    public LoginAttemptService(StringRedisTemplate redisTemplate) {
        this.redisTemplate = redisTemplate;
    }

    /**
     * Throws TooManyLoginAttemptsException if the email has reached the attempt limit.
     * Call this before any credential validation.
     */
    public void checkNotBlocked(String email) {
        try {
            String value = redisTemplate.opsForValue().get(key(email));
            if (value != null && Integer.parseInt(value) >= MAX_ATTEMPTS) {
                throw new TooManyLoginAttemptsException(
                        "Çok fazla başarısız giriş denemesi. 15 dakika sonra tekrar deneyin."
                );
            }
        } catch (TooManyLoginAttemptsException e) {
            throw e;
        } catch (Exception e) {
            log.warn("Redis login attempt check failed for {}: {}", email, e.getMessage());
            // Fail open: do not block login if Redis is unavailable
        }
    }

    /**
     * Increments the failed attempt counter for the given email.
     * The 15-minute TTL is set on the first increment so the window is anchored
     * to the first failed attempt.
     */
    public void recordFailure(String email) {
        try {
            String k = key(email);
            Long count = redisTemplate.opsForValue().increment(k);
            if (count != null && count == 1L) {
                redisTemplate.expire(k, WINDOW);
            }
        } catch (Exception e) {
            log.warn("Redis login attempt increment failed for {}: {}", email, e.getMessage());
        }
    }

    /**
     * Deletes the attempt counter after a successful login.
     */
    public void resetAttempts(String email) {
        try {
            redisTemplate.delete(key(email));
        } catch (Exception e) {
            log.warn("Redis login attempt reset failed for {}: {}", email, e.getMessage());
        }
    }

    private String key(String email) {
        return KEY_PREFIX + email;
    }
}
