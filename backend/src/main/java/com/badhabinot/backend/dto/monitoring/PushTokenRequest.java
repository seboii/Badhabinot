package com.badhabinot.backend.dto.monitoring;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public class PushTokenRequest {

    @NotBlank
    private String token;

    @Size(max = 16)
    private String platform = "ANDROID";

    @Size(max = 128)
    private String deviceName;

    public String getToken() { return token; }
    public void setToken(String token) { this.token = token; }
    public String getPlatform() { return platform; }
    public void setPlatform(String platform) { this.platform = platform; }
    public String getDeviceName() { return deviceName; }
    public void setDeviceName(String deviceName) { this.deviceName = deviceName; }
}
