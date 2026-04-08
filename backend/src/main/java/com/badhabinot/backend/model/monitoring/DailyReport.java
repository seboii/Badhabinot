package com.badhabinot.backend.model.monitoring;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.PrePersist;
import jakarta.persistence.PreUpdate;
import jakarta.persistence.Table;
import java.math.BigDecimal;
import java.time.Instant;
import java.time.LocalDate;
import java.util.UUID;

@Entity
@Table(name = "daily_reports")
public class DailyReport {

    @Id
    private UUID id;

    @Column(name = "user_id", nullable = false)
    private UUID userId;

    @Column(name = "report_date", nullable = false)
    private LocalDate reportDate;

    @Column(name = "analyses_completed", nullable = false)
    private int analysesCompleted;

    @Column(name = "posture_alert_count", nullable = false)
    private int postureAlertCount;

    @Column(name = "hand_movement_count", nullable = false)
    private int handMovementCount;

    @Column(name = "smoking_like_count", nullable = false)
    private int smokingLikeCount;

    @Column(name = "reminder_count", nullable = false)
    private int reminderCount;

    @Column(name = "hydration_progress_ml", nullable = false)
    private int hydrationProgressMl;

    @Column(name = "water_goal_ml", nullable = false)
    private int waterGoalMl;

    @Column(name = "poor_posture_ratio", nullable = false, precision = 6, scale = 4)
    private BigDecimal poorPostureRatio;

    @Column(nullable = false, columnDefinition = "TEXT")
    private String summary;

    @Column(name = "recommendations_json", nullable = false, columnDefinition = "TEXT")
    private String recommendationsJson;

    @Column(name = "generated_at", nullable = false)
    private Instant generatedAt;

    @Column(name = "created_at", nullable = false)
    private Instant createdAt;

    @Column(name = "updated_at", nullable = false)
    private Instant updatedAt;

    protected DailyReport() {
    }

    private DailyReport(UUID id, UUID userId, LocalDate reportDate) {
        this.id = id;
        this.userId = userId;
        this.reportDate = reportDate;
    }

    public static DailyReport create(UUID userId, LocalDate reportDate) {
        return new DailyReport(UUID.randomUUID(), userId, reportDate);
    }

    public void refresh(
            int analysesCompleted,
            int postureAlertCount,
            int handMovementCount,
            int smokingLikeCount,
            int reminderCount,
            int hydrationProgressMl,
            int waterGoalMl,
            double poorPostureRatio,
            String summary,
            String recommendationsJson,
            Instant generatedAt
    ) {
        this.analysesCompleted = analysesCompleted;
        this.postureAlertCount = postureAlertCount;
        this.handMovementCount = handMovementCount;
        this.smokingLikeCount = smokingLikeCount;
        this.reminderCount = reminderCount;
        this.hydrationProgressMl = hydrationProgressMl;
        this.waterGoalMl = waterGoalMl;
        this.poorPostureRatio = BigDecimal.valueOf(poorPostureRatio);
        this.summary = summary;
        this.recommendationsJson = recommendationsJson;
        this.generatedAt = generatedAt;
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

    public UUID getId() {
        return id;
    }

    public LocalDate getReportDate() {
        return reportDate;
    }

    public int getAnalysesCompleted() {
        return analysesCompleted;
    }

    public int getPostureAlertCount() {
        return postureAlertCount;
    }

    public int getHandMovementCount() {
        return handMovementCount;
    }

    public int getSmokingLikeCount() {
        return smokingLikeCount;
    }

    public int getReminderCount() {
        return reminderCount;
    }

    public int getHydrationProgressMl() {
        return hydrationProgressMl;
    }

    public int getWaterGoalMl() {
        return waterGoalMl;
    }

    public BigDecimal getPoorPostureRatio() {
        return poorPostureRatio;
    }

    public String getSummary() {
        return summary;
    }

    public String getRecommendationsJson() {
        return recommendationsJson;
    }

    public Instant getGeneratedAt() {
        return generatedAt;
    }
}

