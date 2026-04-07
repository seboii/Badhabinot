package com.badhabinot.monitoring.domain.model;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.PrePersist;
import jakarta.persistence.Table;
import java.math.BigDecimal;
import java.time.Instant;
import java.util.UUID;

@Entity
@Table(name = "behavior_events")
public class BehaviorEvent {

    @Id
    private UUID id;

    @Column(name = "analysis_id")
    private UUID analysisId;

    @Column(name = "user_id", nullable = false)
    private UUID userId;

    @Column(name = "session_id")
    private UUID sessionId;

    @Column(name = "event_type", nullable = false, length = 64)
    private String eventType;

    @Column(nullable = false, length = 64)
    private String detector;

    @Column(nullable = false, precision = 6, scale = 4)
    private BigDecimal confidence;

    @Column(nullable = false, length = 16)
    private String severity;

    @Column(nullable = false, length = 255)
    private String interpretation;

    @Column(name = "recommendation_hint", nullable = false, length = 255)
    private String recommendationHint;

    @Column(name = "evidence_json", nullable = false, columnDefinition = "TEXT")
    private String evidenceJson;

    @Column(name = "occurred_at", nullable = false)
    private Instant occurredAt;

    @Column(name = "created_at", nullable = false)
    private Instant createdAt;

    protected BehaviorEvent() {
    }

    private BehaviorEvent(
            UUID id,
            UUID analysisId,
            UUID userId,
            UUID sessionId,
            String eventType,
            String detector,
            double confidence,
            String severity,
            String interpretation,
            String recommendationHint,
            String evidenceJson,
            Instant occurredAt
    ) {
        this.id = id;
        this.analysisId = analysisId;
        this.userId = userId;
        this.sessionId = sessionId;
        this.eventType = eventType;
        this.detector = detector;
        this.confidence = BigDecimal.valueOf(confidence);
        this.severity = severity;
        this.interpretation = interpretation;
        this.recommendationHint = recommendationHint;
        this.evidenceJson = evidenceJson;
        this.occurredAt = occurredAt;
    }

    public static BehaviorEvent create(
            UUID analysisId,
            UUID userId,
            UUID sessionId,
            String eventType,
            String detector,
            double confidence,
            String severity,
            String interpretation,
            String recommendationHint,
            String evidenceJson,
            Instant occurredAt
    ) {
        return new BehaviorEvent(
                UUID.randomUUID(),
                analysisId,
                userId,
                sessionId,
                eventType,
                detector,
                confidence,
                severity,
                interpretation,
                recommendationHint,
                evidenceJson,
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

    public UUID getAnalysisId() {
        return analysisId;
    }

    public UUID getSessionId() {
        return sessionId;
    }

    public String getEventType() {
        return eventType;
    }

    public String getDetector() {
        return detector;
    }

    public BigDecimal getConfidence() {
        return confidence;
    }

    public String getSeverity() {
        return severity;
    }

    public String getInterpretation() {
        return interpretation;
    }

    public String getRecommendationHint() {
        return recommendationHint;
    }

    public String getEvidenceJson() {
        return evidenceJson;
    }

    public Instant getOccurredAt() {
        return occurredAt;
    }
}
