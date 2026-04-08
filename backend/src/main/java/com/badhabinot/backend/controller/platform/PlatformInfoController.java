package com.badhabinot.backend.controller.platform;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import java.util.List;
import java.util.Map;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/platform")
@Tag(name = "Platform", description = "Gateway-facing platform metadata")
public class PlatformInfoController {

    @Value("${services.auth-service-uri}")
    private String authServiceUri;

    @Value("${services.user-service-uri}")
    private String userServiceUri;

    @Value("${services.monitoring-service-uri}")
    private String monitoringServiceUri;

    @GetMapping("/info")
    @Operation(summary = "Return gateway service metadata")
    public Map<String, Object> info() {
        return Map.of(
                "platform", "BADHABINOT",
                "phase", "phase-1",
                "services", List.of(
                        Map.of("name", "auth-service", "uri", authServiceUri),
                        Map.of("name", "user-service", "uri", userServiceUri),
                        Map.of("name", "monitoring-service", "uri", monitoringServiceUri)
                )
        );
    }
}

