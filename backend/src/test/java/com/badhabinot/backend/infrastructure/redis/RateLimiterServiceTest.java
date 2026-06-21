package com.badhabinot.backend.infrastructure.redis;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.Mockito.when;

import java.time.Duration;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.data.redis.core.ValueOperations;

@ExtendWith(MockitoExtension.class)
class RateLimiterServiceTest {

    @Mock
    private StringRedisTemplate redisTemplate;

    @Mock
    private ValueOperations<String, String> valueOps;

    @Test
    void allowsRequestsUpToLimit() {
        when(redisTemplate.opsForValue()).thenReturn(valueOps);
        when(valueOps.increment("ratelimit:bucket")).thenReturn(1L, 2L, 3L);
        RateLimiterService service = new RateLimiterService(redisTemplate);

        assertThat(service.allow("bucket", 3, Duration.ofMinutes(1))).isTrue();
        assertThat(service.allow("bucket", 3, Duration.ofMinutes(1))).isTrue();
        assertThat(service.allow("bucket", 3, Duration.ofMinutes(1))).isTrue();
    }

    @Test
    void blocksRequestsOverLimit() {
        when(redisTemplate.opsForValue()).thenReturn(valueOps);
        when(valueOps.increment("ratelimit:bucket")).thenReturn(4L);
        RateLimiterService service = new RateLimiterService(redisTemplate);

        assertThat(service.allow("bucket", 3, Duration.ofMinutes(1))).isFalse();
    }

    @Test
    void failsOpenWhenRedisUnavailable() {
        when(redisTemplate.opsForValue()).thenThrow(new RuntimeException("redis down"));
        RateLimiterService service = new RateLimiterService(redisTemplate);

        // Redis erişilemezse istek akışı bozulmasın → izin ver.
        assertThat(service.allow("bucket", 3, Duration.ofMinutes(1))).isTrue();
    }
}
