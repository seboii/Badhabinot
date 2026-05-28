package com.badhabinot.backend.service.monitoring.impl;

import com.badhabinot.backend.model.monitoring.PushToken;
import com.badhabinot.backend.repository.monitoring.PushTokenRepository;
import com.badhabinot.backend.service.monitoring.IPushNotificationService;
import com.google.firebase.messaging.FirebaseMessaging;
import com.google.firebase.messaging.Message;
import com.google.firebase.messaging.Notification;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import java.util.List;
import java.util.Map;
import java.util.UUID;

@Service
public class PushNotificationServiceImpl implements IPushNotificationService {

    private static final Logger log = LoggerFactory.getLogger(PushNotificationServiceImpl.class);

    private final PushTokenRepository pushTokenRepository;

    public PushNotificationServiceImpl(PushTokenRepository pushTokenRepository) {
        this.pushTokenRepository = pushTokenRepository;
    }

    @Override
    @Transactional("monitoringTransactionManager")
    public void registerToken(UUID userId, String token, String platform, String deviceName) {
        pushTokenRepository.findByToken(token).ifPresentOrElse(
                existing -> {
                    existing.setUserId(userId);
                    existing.setActive(true);
                    existing.setDeviceName(deviceName);
                    pushTokenRepository.save(existing);
                },
                () -> {
                    PushToken pt = new PushToken();
                    pt.setUserId(userId);
                    pt.setToken(token);
                    pt.setPlatform(platform != null ? platform : "ANDROID");
                    pt.setDeviceName(deviceName);
                    pushTokenRepository.save(pt);
                }
        );
        log.info("Push token registered for user={}", userId);
    }

    @Override
    @Transactional("monitoringTransactionManager")
    public void unregisterToken(String token) {
        pushTokenRepository.deactivateByToken(token);
        log.info("Push token unregistered");
    }

    @Override
    public void sendToUser(UUID userId, String title, String body, Map<String, String> data) {
        if (com.google.firebase.FirebaseApp.getApps().isEmpty()) {
            log.debug("Firebase not configured — skipping push to user={}", userId);
            return;
        }

        List<PushToken> tokens = pushTokenRepository.findByUserIdAndActiveTrue(userId);
        if (tokens.isEmpty()) {
            log.debug("No active push tokens for user={}", userId);
            return;
        }

        for (PushToken pt : tokens) {
            try {
                Message.Builder builder = Message.builder()
                        .setToken(pt.getToken())
                        .setNotification(Notification.builder()
                                .setTitle(title)
                                .setBody(body)
                                .build());
                if (data != null) {
                    data.forEach(builder::putData);
                }
                String result = FirebaseMessaging.getInstance().send(builder.build());
                log.debug("FCM sent to user={}, messageId={}", userId, result);
            } catch (Exception e) {
                log.warn("FCM send failed for token={}: {}", pt.getToken(), e.getMessage());
                if (e.getMessage() != null && e.getMessage().contains("registration-token-not-registered")) {
                    pushTokenRepository.deactivateByToken(pt.getToken());
                }
            }
        }
    }
}
