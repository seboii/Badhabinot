package com.badhabinot.backend.model.monitoring;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.Id;
import jakarta.persistence.PrePersist;
import jakarta.persistence.Table;
import java.math.BigDecimal;
import java.time.Instant;
import java.util.UUID;

@Entity
@Table(name = "activity_feed")
public class ActivityFeedItem {

    @Id
    private UUID id;

    @Column(name = "user_id", nullable = false)
    private UUID userId;

    @Column(name = "session_id")
    private UUID sessionId;

    @Column(name = "activity_type", nullable = false, length = 64)
    private String activityType;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 32)
    private ActivityCategory category;

    @Column(nullable = false, length = 160)
    private String title;

    @Column(nullable = false, length = 255)
    private String message;

    @Column(precision = 6, scale = 4)
    private BigDecimal confidence;

    @Column(name = "occurred_at", nullable = false)
    private Instant occurredAt;

    @Column(name = "created_at", nullable = false)
    private Instant createdAt;

    protected ActivityFeedItem() {
    }

    private ActivityFeedItem(
            UUID id,
            UUID userId,
            UUID sessionId,
            String activityType,
            ActivityCategory category,
            String title,
            String message,
            BigDecimal confidence,
            Instant occurredAt
    ) {
        this.id = id;
        this.userId = userId;
        this.sessionId = sessionId;
        this.activityType = activityType;
        this.category = category;
        this.title = title;
        this.message = message;
        this.confidence = confidence;
        this.occurredAt = occurredAt;
    }

    public static ActivityFeedItem create(
            UUID userId,
            UUID sessionId,
            String activityType,
            ActivityCategory category,
            String title,
            String message,
            Double confidence,
            Instant occurredAt
    ) {
        return new ActivityFeedItem(
                UUID.randomUUID(),
                userId,
                sessionId,
                activityType,
                category,
                title,
                message,
                confidence == null ? null : BigDecimal.valueOf(confidence),
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

    public String getActivityType() {
        return activityType;
    }

    public ActivityCategory getCategory() {
        return category;
    }

    public String getTitle() {
        return title;
    }

    public String getMessage() {
        return message;
    }

    public BigDecimal getConfidence() {
        return confidence;
    }

    public Instant getOccurredAt() {
        return occurredAt;
    }
}


