package com.badhabinot.backend.infrastructure.health;

import java.time.Duration;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.boot.actuate.health.Health;
import org.springframework.boot.actuate.health.HealthIndicator;
import org.springframework.http.HttpStatusCode;
import org.springframework.stereotype.Component;
import org.springframework.web.reactive.function.client.WebClient;

@Component("pythonServices")
public class DownstreamServicesHealthIndicator implements HealthIndicator {

    private final WebClient visionClient;
    private final WebClient aiClient;

    public DownstreamServicesHealthIndicator(
            @Qualifier("visionServiceWebClient") WebClient visionClient,
            @Qualifier("aiServiceHealthWebClient") WebClient aiClient
    ) {
        this.visionClient = visionClient;
        this.aiClient = aiClient;
    }

    @Override
    public Health health() {
        try {
            String vision = visionClient.get()
                    .uri("/ready")
                    .retrieve()
                    .onStatus(HttpStatusCode::isError, response -> response.createException())
                    .bodyToMono(String.class)
                    .block(Duration.ofSeconds(5));

            String ai = aiClient.get()
                    .uri("/ready")
                    .retrieve()
                    .onStatus(HttpStatusCode::isError, response -> response.createException())
                    .bodyToMono(String.class)
                    .block(Duration.ofSeconds(5));

            return Health.up()
                    .withDetail("visionService", vision)
                    .withDetail("aiService", ai)
                    .build();
        } catch (Exception exception) {
            return Health.down(exception).build();
        }
    }
}
