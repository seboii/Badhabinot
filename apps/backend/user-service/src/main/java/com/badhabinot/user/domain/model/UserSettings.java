package com.badhabinot.user.domain.model;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.Id;
import jakarta.persistence.PrePersist;
import jakarta.persistence.PreUpdate;
import jakarta.persistence.Table;
import java.time.Instant;
import java.time.LocalTime;
import java.util.UUID;

@Entity
@Table(name = "user_settings")
public class UserSettings {

    @Id
    @Column(name = "user_id")
    private UUID userId;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 16)
    private Sensitivity sensitivity;

    @Column(name = "water_goal_ml", nullable = false)
    private int waterGoalMl;

    @Column(name = "water_interval_min", nullable = false)
    private int waterIntervalMin;

    @Column(name = "exercise_interval_min", nullable = false)
    private int exerciseIntervalMin;

    @Column(name = "quiet_hours_enabled", nullable = false)
    private boolean quietHoursEnabled;

    @Column(name = "quiet_hours_start", nullable = false)
    private LocalTime quietHoursStart;

    @Column(name = "quiet_hours_end", nullable = false)
    private LocalTime quietHoursEnd;

    @Enumerated(EnumType.STRING)
    @Column(name = "model_mode", nullable = false, length = 16)
    private ModelMode modelMode;

    @Column(name = "notifications_enabled", nullable = false)
    private boolean notificationsEnabled;

    @Column(name = "created_at", nullable = false)
    private Instant createdAt;

    @Column(name = "updated_at", nullable = false)
    private Instant updatedAt;

    protected UserSettings() {
    }

    private UserSettings(UUID userId) {
        this.userId = userId;
        this.sensitivity = Sensitivity.MEDIUM;
        this.waterGoalMl = 2500;
        this.waterIntervalMin = 60;
        this.exerciseIntervalMin = 60;
        this.quietHoursEnabled = false;
        this.quietHoursStart = LocalTime.of(22, 0);
        this.quietHoursEnd = LocalTime.of(8, 0);
        this.modelMode = ModelMode.API;
        this.notificationsEnabled = true;
    }

    public static UserSettings createDefault(UUID userId) {
        return new UserSettings(userId);
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

    public void update(
            Sensitivity sensitivity,
            int waterGoalMl,
            int waterIntervalMin,
            int exerciseIntervalMin,
            boolean quietHoursEnabled,
            LocalTime quietHoursStart,
            LocalTime quietHoursEnd,
            ModelMode modelMode,
            boolean notificationsEnabled
    ) {
        this.sensitivity = sensitivity;
        this.waterGoalMl = waterGoalMl;
        this.waterIntervalMin = waterIntervalMin;
        this.exerciseIntervalMin = exerciseIntervalMin;
        this.quietHoursEnabled = quietHoursEnabled;
        this.quietHoursStart = quietHoursStart;
        this.quietHoursEnd = quietHoursEnd;
        this.modelMode = modelMode;
        this.notificationsEnabled = notificationsEnabled;
    }

    public UUID getUserId() {
        return userId;
    }

    public Sensitivity getSensitivity() {
        return sensitivity;
    }

    public int getWaterIntervalMin() {
        return waterIntervalMin;
    }

    public int getWaterGoalMl() {
        return waterGoalMl;
    }

    public int getExerciseIntervalMin() {
        return exerciseIntervalMin;
    }

    public boolean isQuietHoursEnabled() {
        return quietHoursEnabled;
    }

    public LocalTime getQuietHoursStart() {
        return quietHoursStart;
    }

    public LocalTime getQuietHoursEnd() {
        return quietHoursEnd;
    }

    public ModelMode getModelMode() {
        return modelMode;
    }

    public boolean isNotificationsEnabled() {
        return notificationsEnabled;
    }

    public Instant getUpdatedAt() {
        return updatedAt;
    }
}
