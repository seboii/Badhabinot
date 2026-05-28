package com.badhabinot.backend.config;

import com.google.auth.oauth2.GoogleCredentials;
import com.google.firebase.FirebaseApp;
import com.google.firebase.FirebaseOptions;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.core.io.Resource;
import java.io.IOException;
import java.io.InputStream;

@Configuration
public class FirebaseConfiguration {

    private static final Logger log = LoggerFactory.getLogger(FirebaseConfiguration.class);

    @Value("${firebase.service-account-key-path:}")
    private String serviceAccountKeyPath;

    @Bean
    public FirebaseApp firebaseApp() throws IOException {
        if (!FirebaseApp.getApps().isEmpty()) {
            return FirebaseApp.getInstance();
        }

        if (serviceAccountKeyPath == null || serviceAccountKeyPath.isBlank()) {
            log.warn("Firebase service account key not configured (FIREBASE_SERVICE_ACCOUNT_KEY_PATH). " +
                    "Push notifications will be disabled.");
            // Initialize with no credentials — sendToUser will fail gracefully
            return null;
        }

        try {
            Resource resource = new org.springframework.core.io.FileSystemResource(serviceAccountKeyPath);
            if (!resource.exists()) {
                log.warn("Firebase service account key file not found at '{}'. " +
                        "Push notifications will be disabled.", serviceAccountKeyPath);
                return null;
            }
            try (InputStream is = resource.getInputStream()) {
                FirebaseOptions options = FirebaseOptions.builder()
                        .setCredentials(GoogleCredentials.fromStream(is))
                        .build();
                FirebaseApp app = FirebaseApp.initializeApp(options);
                log.info("Firebase initialized from {}", serviceAccountKeyPath);
                return app;
            }
        } catch (IOException e) {
            log.warn("Failed to initialize Firebase: {}. Push notifications will be disabled.", e.getMessage());
            return null;
        }
    }
}
