package com.badhabinot.backend.model.monitoring;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.PrePersist;
import jakarta.persistence.Table;
import java.time.Instant;
import java.util.UUID;

@Entity
@Table(name = "hydration_logs")
public class HydrationLog {

    @Id
    private UUID id;

    @Column(name = "user_id", nullable = false)
    private UUID userId;

    @Column(name = "session_id")
    private UUID sessionId;

    @Column(name = "amount_ml", nullable = false)
    private int amountMl;

    @Column(nullable = false, length = 32)
    private String source;

    @Column(name = "occurred_at", nullable = false)
    private Instant occurredAt;

    @Column(name = "created_at", nullable = false)
    private Instant createdAt;

    protected HydrationLog() {
    }

    private HydrationLog(UUID id, UUID userId, UUID sessionId, int amountMl, String source, Instant occurredAt) {
        this.id = id;
        this.userId = userId;
        this.sessionId = sessionId;
        this.amountMl = amountMl;
        this.source = source;
        this.occurredAt = occurredAt;
    }

    public static HydrationLog create(UUID userId, UUID sessionId, int amountMl, String source, Instant occurredAt) {
        return new HydrationLog(UUID.randomUUID(), userId, sessionId, amountMl, source, occurredAt);
    }

    @PrePersist
    void onCreate() {
        createdAt = Instant.now();
    }

    public int getAmountMl() {
        return amountMl;
    }

    public UUID getId() {
        return id;
    }

    public Instant getOccurredAt() {
        return occurredAt;
    }
}

