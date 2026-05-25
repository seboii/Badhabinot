package com.badhabinot.backend.infrastructure.redis;

import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.assertj.core.api.Assertions.assertThatCode;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.badhabinot.backend.common.exception.auth.TooManyLoginAttemptsException;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.data.redis.core.ValueOperations;

@ExtendWith(MockitoExtension.class)
class LoginAttemptServiceTest {

    @Mock
    private StringRedisTemplate redisTemplate;

    @Mock
    private ValueOperations<String, String> valueOps;

    @InjectMocks
    private LoginAttemptService loginAttemptService;

    @Test
    void checkNotBlockedPassesWhenNoAttempts() {
        when(redisTemplate.opsForValue()).thenReturn(valueOps);
        when(valueOps.get("login:attempts:alice@example.com")).thenReturn(null);

        assertThatCode(() -> loginAttemptService.checkNotBlocked("alice@example.com")).doesNotThrowAnyException();
    }

    @Test
    void checkNotBlockedPassesWhenBelowLimit() {
        when(redisTemplate.opsForValue()).thenReturn(valueOps);
        when(valueOps.get("login:attempts:alice@example.com")).thenReturn("3");

        assertThatCode(() -> loginAttemptService.checkNotBlocked("alice@example.com")).doesNotThrowAnyException();
    }

    @Test
    void checkNotBlockedThrowsWhenAtLimit() {
        when(redisTemplate.opsForValue()).thenReturn(valueOps);
        when(valueOps.get("login:attempts:alice@example.com")).thenReturn("5");

        assertThatThrownBy(() -> loginAttemptService.checkNotBlocked("alice@example.com"))
                .isInstanceOf(TooManyLoginAttemptsException.class);
    }

    @Test
    void checkNotBlockedThrowsWhenAboveLimit() {
        when(redisTemplate.opsForValue()).thenReturn(valueOps);
        when(valueOps.get("login:attempts:alice@example.com")).thenReturn("9");

        assertThatThrownBy(() -> loginAttemptService.checkNotBlocked("alice@example.com"))
                .isInstanceOf(TooManyLoginAttemptsException.class);
    }

    @Test
    void checkNotBlockedFailsOpenWhenRedisThrows() {
        when(redisTemplate.opsForValue()).thenReturn(valueOps);
        when(valueOps.get("login:attempts:err@example.com")).thenThrow(new RuntimeException("Redis unavailable"));

        // Should not throw — fail open so login can proceed
        assertThatCode(() -> loginAttemptService.checkNotBlocked("err@example.com")).doesNotThrowAnyException();
    }

    @Test
    void recordFailureSetsExpiryOnFirstIncrement() {
        when(redisTemplate.opsForValue()).thenReturn(valueOps);
        when(valueOps.increment("login:attempts:bob@example.com")).thenReturn(1L);

        loginAttemptService.recordFailure("bob@example.com");

        verify(redisTemplate).expire(
                org.mockito.ArgumentMatchers.eq("login:attempts:bob@example.com"),
                org.mockito.ArgumentMatchers.any()
        );
    }

    @Test
    void recordFailureDoesNotResetExpiryOnSubsequentIncrements() {
        when(redisTemplate.opsForValue()).thenReturn(valueOps);
        when(valueOps.increment("login:attempts:bob@example.com")).thenReturn(3L);

        loginAttemptService.recordFailure("bob@example.com");

        // expire should NOT be called again after first increment
        org.mockito.Mockito.verify(redisTemplate, org.mockito.Mockito.never())
                .expire(
                        org.mockito.ArgumentMatchers.any(),
                        org.mockito.ArgumentMatchers.any()
                );
    }

    @Test
    void resetAttemptsDeletesKey() {
        loginAttemptService.resetAttempts("charlie@example.com");

        verify(redisTemplate).delete("login:attempts:charlie@example.com");
    }
}
