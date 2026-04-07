package com.badhabinot.monitoring.domain.model;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.PrePersist;
import jakarta.persistence.Table;
import java.time.Instant;
import java.util.UUID;

@Entity
@Table(name = "reminder_events")
public class ReminderEvent {

    @Id
    private UUID id;

    @Column(name = "user_id", nullable = false)
    private UUID userId;

    @Column(name = "session_id")
    private UUID sessionId;

    @Column(name = "reminder_type", nullable = false, length = 64)
    private String reminderType;

    @Column(nullable = false, length = 32)
    private String source;

    @Column(nullable = false, length = 16)
    private String severity;

    @Column(nullable = false, length = 255)
    private String message;

    @Column(name = "trigger_reason", nullable = false, length = 255)
    private String triggerReason;

    @Column(name = "metadata_json", nullable = false, columnDefinition = "TEXT")
    private String metadataJson;

    @Column(name = "occurred_at", nullable = false)
    private Instant occurredAt;

    @Column(name = "created_at", nullable = false)
    private Instant createdAt;

    protected ReminderEvent() {
    }

    private ReminderEvent(
            UUID id,
            UUID userId,
            UUID sessionId,
            String reminderType,
            String source,
            String severity,
            String message,
            String triggerReason,
            String metadataJson,
            Instant occurredAt
    ) {
        this.id = id;
        this.userId = userId;
        this.sessionId = sessionId;
        this.reminderType = reminderType;
        this.source = source;
        this.severity = severity;
        this.message = message;
        this.triggerReason = triggerReason;
        this.metadataJson = metadataJson;
        this.occurredAt = occurredAt;
    }

    public static ReminderEvent create(
            UUID userId,
            UUID sessionId,
            String reminderType,
            String source,
            String severity,
            String message,
            String triggerReason,
            String metadataJson,
            Instant occurredAt
    ) {
        return new ReminderEvent(
                UUID.randomUUID(),
                userId,
                sessionId,
                reminderType,
                source,
                severity,
                message,
                triggerReason,
                metadataJson,
                occurredAt
        );
    }

    @PrePersist
    void onCreate() {
        createdAt = Instant.now();
    }

    public UUID getId() {
        return id;
    }

    public UUID getSessionId() {
        return sessionId;
    }

    public String getReminderType() {
        return reminderType;
    }

    public String getSource() {
        return source;
    }

    public String getSeverity() {
        return severity;
    }

    public String getMessage() {
        return message;
    }

    public String getTriggerReason() {
        return triggerReason;
    }

    public String getMetadataJson() {
        return metadataJson;
    }

    public Instant getOccurredAt() {
        return occurredAt;
    }
}
