package com.badhabinot.backend.service.auth;

import com.badhabinot.backend.common.exception.auth.InvalidPasswordResetTokenException;
import com.badhabinot.backend.dto.auth.PasswordResetConfirmDto;
import com.badhabinot.backend.dto.auth.PasswordResetRequestDto;
import com.badhabinot.backend.model.auth.AuthUser;
import com.badhabinot.backend.repository.auth.AuthUserRepository;
import java.time.Duration;
import java.util.Locale;
import java.util.UUID;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class PasswordResetService {

    private static final Logger log = LoggerFactory.getLogger(PasswordResetService.class);

    private static final String KEY_PREFIX = "pwd:reset:";
    private static final Duration TOKEN_TTL = Duration.ofHours(1);

    private final StringRedisTemplate redisTemplate;
    private final AuthUserRepository authUserRepository;
    private final PasswordEncoder passwordEncoder;
    private final MailService mailService;

    public PasswordResetService(
            StringRedisTemplate redisTemplate,
            AuthUserRepository authUserRepository,
            PasswordEncoder passwordEncoder,
            MailService mailService
    ) {
        this.redisTemplate = redisTemplate;
        this.authUserRepository = authUserRepository;
        this.passwordEncoder = passwordEncoder;
        this.mailService = mailService;
    }

    /**
     * Generates a reset token and sends a reset email if the address is registered.
     * Always completes silently to avoid revealing whether an email exists.
     */
    @Transactional(transactionManager = "authTransactionManager", readOnly = true)
    public void requestReset(PasswordResetRequestDto request) {
        String normalizedEmail = request.email().trim().toLowerCase(Locale.ROOT);
        authUserRepository.findByEmail(normalizedEmail).ifPresent(user -> {
            String token = UUID.randomUUID().toString();
            try {
                redisTemplate.opsForValue().set(KEY_PREFIX + token, normalizedEmail, TOKEN_TTL);
            } catch (Exception e) {
                log.warn("Redis unavailable while storing password reset token for {}: {}", normalizedEmail, e.getMessage());
                return;
            }
            mailService.sendPasswordResetEmail(normalizedEmail, token);
        });
    }

    /**
     * Validates the token, updates the password, and invalidates the token.
     * Throws InvalidPasswordResetTokenException if the token is missing or expired.
     */
    @Transactional(transactionManager = "authTransactionManager")
    public void confirmReset(PasswordResetConfirmDto request) {
        String key = KEY_PREFIX + request.token();
        String email;
        try {
            email = redisTemplate.opsForValue().get(key);
        } catch (Exception e) {
            log.warn("Redis unavailable during password reset confirm: {}", e.getMessage());
            throw new InvalidPasswordResetTokenException("Password reset token is invalid or expired");
        }

        if (email == null) {
            throw new InvalidPasswordResetTokenException("Password reset token is invalid or expired");
        }

        AuthUser user = authUserRepository.findByEmail(email)
                .orElseThrow(() -> new InvalidPasswordResetTokenException("Password reset token is invalid or expired"));

        user.updatePassword(passwordEncoder.encode(request.newPassword()));
        authUserRepository.save(user);

        try {
            redisTemplate.delete(key);
        } catch (Exception e) {
            log.warn("Redis unavailable while deleting password reset token: {}", e.getMessage());
        }
    }
}
