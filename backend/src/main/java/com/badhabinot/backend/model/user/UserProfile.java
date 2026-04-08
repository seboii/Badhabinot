package com.badhabinot.backend.model.user;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.PrePersist;
import jakarta.persistence.PreUpdate;
import jakarta.persistence.Table;
import java.time.Instant;
import java.util.UUID;

@Entity
@Table(name = "user_profiles")
public class UserProfile {

    @Id
    @Column(name = "user_id")
    private UUID userId;

    @Column(nullable = false, unique = true, length = 320)
    private String email;

    @Column(name = "display_name", nullable = false, length = 100)
    private String displayName;

    @Column(nullable = false, length = 64)
    private String timezone;

    @Column(nullable = false, length = 16)
    private String locale;

    @Column(name = "created_at", nullable = false)
    private Instant createdAt;

    @Column(name = "updated_at", nullable = false)
    private Instant updatedAt;

    protected UserProfile() {
    }

    private UserProfile(UUID userId, String email, String displayName, String timezone, String locale) {
        this.userId = userId;
        this.email = email;
        this.displayName = displayName;
        this.timezone = timezone;
        this.locale = locale;
    }

    public static UserProfile create(UUID userId, String email, String displayName, String timezone, String locale) {
        return new UserProfile(userId, email, displayName, timezone, locale);
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

    public void updateFromBootstrap(String email, String displayName, String timezone, String locale) {
        this.email = email;
        this.displayName = displayName;
        this.timezone = timezone;
        this.locale = locale;
    }

    public void updateProfile(String displayName, String timezone, String locale) {
        this.displayName = displayName;
        this.timezone = timezone;
        this.locale = locale;
    }

    public UUID getUserId() {
        return userId;
    }

    public String getEmail() {
        return email;
    }

    public String getDisplayName() {
        return displayName;
    }

    public String getTimezone() {
        return timezone;
    }

    public String getLocale() {
        return locale;
    }

    public Instant getUpdatedAt() {
        return updatedAt;
    }
}


