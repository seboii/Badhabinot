package com.badhabinot.backend.dto.monitoring;

import java.time.Instant;
import java.util.UUID;

public class PushDeviceResponse {

    private UUID id;
    private String platform;
    private String deviceName;
    private boolean active;
    private Instant createdAt;

    public PushDeviceResponse(UUID id, String platform, String deviceName,
                               boolean active, Instant createdAt) {
        this.id = id;
        this.platform = platform;
        this.deviceName = deviceName;
        this.active = active;
        this.createdAt = createdAt;
    }

    public UUID getId() { return id; }
    public String getPlatform() { return platform; }
    public String getDeviceName() { return deviceName; }
    public boolean isActive() { return active; }
    public Instant getCreatedAt() { return createdAt; }
}
