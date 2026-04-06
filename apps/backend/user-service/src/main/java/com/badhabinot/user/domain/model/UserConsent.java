package com.badhabinot.user.domain.model;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.PrePersist;
import jakarta.persistence.PreUpdate;
import jakarta.persistence.Table;
import java.time.Instant;
import java.util.UUID;

@Entity
@Table(name = "user_consents")
public class UserConsent {

    @Id
    @Column(name = "user_id")
    private UUID userId;

    @Column(name = "privacy_policy_accepted", nullable = false)
    private boolean privacyPolicyAccepted;

    @Column(name = "camera_monitoring_accepted", nullable = false)
    private boolean cameraMonitoringAccepted;

    @Column(name = "remote_inference_accepted", nullable = false)
    private boolean remoteInferenceAccepted;

    @Column(name = "accepted_at")
    private Instant acceptedAt;

    @Column(name = "updated_at", nullable = false)
    private Instant updatedAt;

    protected UserConsent() {
    }

    private UserConsent(UUID userId) {
        this.userId = userId;
        this.privacyPolicyAccepted = false;
        this.cameraMonitoringAccepted = false;
        this.remoteInferenceAccepted = false;
    }

    public static UserConsent createDefault(UUID userId) {
        return new UserConsent(userId);
    }

    @PrePersist
    void onCreate() {
        updatedAt = Instant.now();
    }

    @PreUpdate
    void onUpdate() {
        updatedAt = Instant.now();
    }

    public void update(boolean privacyPolicyAccepted, boolean cameraMonitoringAccepted, boolean remoteInferenceAccepted) {
        this.privacyPolicyAccepted = privacyPolicyAccepted;
        this.cameraMonitoringAccepted = cameraMonitoringAccepted;
        this.remoteInferenceAccepted = remoteInferenceAccepted;
        if (privacyPolicyAccepted || cameraMonitoringAccepted || remoteInferenceAccepted) {
            this.acceptedAt = Instant.now();
        }
    }

    public UUID getUserId() {
        return userId;
    }

    public boolean isPrivacyPolicyAccepted() {
        return privacyPolicyAccepted;
    }

    public boolean isCameraMonitoringAccepted() {
        return cameraMonitoringAccepted;
    }

    public boolean isRemoteInferenceAccepted() {
        return remoteInferenceAccepted;
    }

    public Instant getAcceptedAt() {
        return acceptedAt;
    }

    public Instant getUpdatedAt() {
        return updatedAt;
    }
}

