package com.badhabinot.backend.service.monitoring;

import java.util.UUID;

public interface IPushNotificationService {

    void registerToken(UUID userId, String token, String platform, String deviceName);

    void unregisterToken(String token);

    void sendToUser(UUID userId, String title, String body, java.util.Map<String, String> data);
}
