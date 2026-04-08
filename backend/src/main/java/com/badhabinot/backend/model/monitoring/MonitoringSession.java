package com.badhabinot.backend.model.monitoring;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.Id;
import jakarta.persistence.PrePersist;
import jakarta.persistence.PreUpdate;
import jakarta.persistence.Table;
import java.time.Instant;
import java.util.UUID;

@Entity
@Table(name = "monitoring_sessions")
public class MonitoringSession {

    @Id
    private UUID id;

    @Column(name = "user_id", nullable = false)
    private UUID userId;

    @Column(name = "client_surface", nullable = false, length = 32)
    private String clientSurface;

    @Column(name = "device_type", nullable = false, length = 32)
    private String deviceType;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 32)
    private MonitoringSessionStatus status;

    @Column(name = "started_at", nullable = false)
    private Instant startedAt;

    @Column(name = "ended_at")
    private Instant endedAt;

    @Column(name = "created_at", nullable = false)
    private Instant createdAt;

    @Column(name = "updated_at", nullable = false)
    private Instant updatedAt;

    protected MonitoringSession() {
    }

    private MonitoringSession(UUID id, UUID userId, String clientSurface, String deviceType) {
        this.id = id;
        this.userId = userId;
        this.clientSurface = clientSurface;
        this.deviceType = deviceType;
        this.status = MonitoringSessionStatus.ACTIVE;
        this.startedAt = Instant.now();
    }

    public static MonitoringSession start(UUID userId, String clientSurface, String deviceType) {
        return new MonitoringSession(UUID.randomUUID(), userId, clientSurface, deviceType);
    }

    @PrePersist
    void onCreate() {
        Instant now = Instant.now();
        createdAt = now;
        updatedAt = now;
    }

    @PreUpdate
    void onUpdate() {
        updatedAt = Instant.now();
    }

    public void stop() {
        this.status = MonitoringSessionStatus.STOPPED;
        this.endedAt = Instant.now();
    }

    public UUID getId() {
        return id;
    }

    public UUID getUserId() {
        return userId;
    }

    public MonitoringSessionStatus getStatus() {
        return status;
    }

    public Instant getStartedAt() {
        return startedAt;
    }

    public Instant getEndedAt() {
        return endedAt;
    }
}


