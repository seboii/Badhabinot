package com.badhabinot.backend.infrastructure.redis;

import java.time.Duration;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Component;

/**
 * Genel amaçlı, Redis tabanlı sabit-pencere hız sınırlayıcı (rate limiter).
 * Kayıt ve şifre-sıfırlama gibi kötüye kullanılabilir uçları korumak için kullanılır.
 * Redis erişilemezse fail-open (izin verir) — istek akışını bozmaz.
 */
@Component
public class RateLimiterService {

    private static final Logger log = LoggerFactory.getLogger(RateLimiterService.class);
    private static final String PREFIX = "ratelimit:";

    private final StringRedisTemplate redisTemplate;

    public RateLimiterService(StringRedisTemplate redisTemplate) {
        this.redisTemplate = redisTemplate;
    }

    /**
     * @return true = izin verildi; false = pencere içinde {@code max} aşıldı.
     */
    public boolean allow(String bucket, int max, Duration window) {
        try {
            String key = PREFIX + bucket;
            Long count = redisTemplate.opsForValue().increment(key);
            if (count != null && count == 1L) {
                redisTemplate.expire(key, window);
            }
            return count == null || count <= max;
        } catch (Exception e) {
            log.warn("Rate limit kontrolu basarisiz ({}): {}", bucket, e.getMessage());
            return true; // fail-open
        }
    }
}
