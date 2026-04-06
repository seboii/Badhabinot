package com.badhabinot.monitoring.domain.model;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.Id;
import jakarta.persistence.PrePersist;
import jakarta.persistence.PreUpdate;
import jakarta.persistence.Table;
import java.math.BigDecimal;
import java.time.Instant;
import java.util.UUID;

@Entity
@Table(name = "analysis_jobs")
public class AnalysisJob {

    @Id
    private UUID id;

    @Column(name = "user_id", nullable = false)
    private UUID userId;

    @Column(name = "session_id", nullable = false, length = 128)
    private String sessionId;

    @Column(name = "frame_id", nullable = false, length = 128)
    private String frameId;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 32)
    private AnalysisStatus status;

    @Column(name = "subject_present")
    private Boolean subjectPresent;

    @Column(name = "posture_state", length = 32)
    private String postureState;

    @Column(name = "behavior_type", length = 64)
    private String behaviorType;

    @Column(precision = 6, scale = 4)
    private BigDecimal confidence;

    @Column(name = "failure_code", length = 64)
    private String failureCode;

    @Column(name = "failure_message", length = 512)
    private String failureMessage;

    @Column(name = "created_at", nullable = false)
    private Instant createdAt;

    @Column(name = "updated_at", nullable = false)
    private Instant updatedAt;

    protected AnalysisJob() {
    }

    private AnalysisJob(UUID id, UUID userId, String sessionId, String frameId) {
        this.id = id;
        this.userId = userId;
        this.sessionId = sessionId;
        this.frameId = frameId;
        this.status = AnalysisStatus.PROCESSING;
    }

    public static AnalysisJob create(UUID userId, String sessionId, String frameId) {
        return new AnalysisJob(UUID.randomUUID(), userId, sessionId, frameId);
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

    public void markCompleted(boolean subjectPresent, String postureState, String behaviorType, double confidence) {
        this.status = AnalysisStatus.COMPLETED;
        this.subjectPresent = subjectPresent;
        this.postureState = postureState;
        this.behaviorType = behaviorType;
        this.confidence = BigDecimal.valueOf(confidence);
        this.failureCode = null;
        this.failureMessage = null;
    }

    public void markFailed(String failureCode, String failureMessage) {
        this.status = AnalysisStatus.FAILED;
        this.failureCode = failureCode;
        this.failureMessage = failureMessage;
    }

    public UUID getId() {
        return id;
    }

    public UUID getUserId() {
        return userId;
    }

    public String getSessionId() {
        return sessionId;
    }

    public String getFrameId() {
        return frameId;
    }

    public AnalysisStatus getStatus() {
        return status;
    }

    public Boolean getSubjectPresent() {
        return subjectPresent;
    }

    public String getPostureState() {
        return postureState;
    }

    public String getBehaviorType() {
        return behaviorType;
    }

    public BigDecimal getConfidence() {
        return confidence;
    }

    public String getFailureCode() {
        return failureCode;
    }

    public String getFailureMessage() {
        return failureMessage;
    }

    public Instant getCreatedAt() {
        return createdAt;
    }

    public Instant getUpdatedAt() {
        return updatedAt;
    }
}
