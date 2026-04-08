package com.badhabinot.backend.integration.python;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import com.badhabinot.backend.dto.monitoring.AiAnalysisRequest;
import com.badhabinot.backend.common.exception.monitoring.DownstreamServiceException;
import com.badhabinot.backend.common.exception.monitoring.DownstreamTimeoutException;
import java.net.SocketTimeoutException;
import java.net.URI;
import java.time.Instant;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.web.reactive.function.client.ClientResponse;
import org.springframework.web.reactive.function.client.WebClient;
import org.springframework.web.reactive.function.client.WebClientRequestException;
import reactor.core.publisher.Mono;

class AiAnalysisClientTest {

    @Test
    void analyzeReturnsInvocationWithModelData() {
        AiAnalysisClient client = new AiAnalysisClient(webClientResponding(HttpStatus.OK, """
                {
                  "requestId": "req-77",
                  "behaviorType": "hand_movement_pattern",
                  "confidence": 0.81,
                  "scores": {
                    "hand_movement_pattern": 0.81,
                    "smoking_like_gesture": 0.12
                  },
                  "summary": "Repeated hand movement is likely.",
                  "recommendation": "Take a short break.",
                  "groundedFacts": ["Hand motion score exceeded baseline."],
                  "model": {
                    "provider": "openai-compatible",
                    "name": "gpt-4.1-mini",
                    "mode": "external_api"
                  }
                }
                """));

        var invocation = client.analyze(request());

        assertThat(invocation.response().behaviorType()).isEqualTo("hand_movement_pattern");
        assertThat(invocation.response().model().provider()).isEqualTo("openai-compatible");
        assertThat(invocation.latencyMs()).isGreaterThanOrEqualTo(0L);
    }

    @Test
    void analyzeMapsHttpErrorsToDownstreamServiceException() {
        AiAnalysisClient client = new AiAnalysisClient(webClientResponding(
                HttpStatus.SERVICE_UNAVAILABLE,
                "provider unavailable",
                MediaType.TEXT_PLAIN
        ));

        assertThatThrownBy(() -> client.analyze(request()))
                .isInstanceOf(DownstreamServiceException.class)
                .satisfies(exception -> {
                    DownstreamServiceException downstream = (DownstreamServiceException) exception;
                    assertThat(downstream.getErrorCode()).isEqualTo("ai_service_error");
                    assertThat(downstream).hasMessageContaining("provider unavailable");
                });
    }

    @Test
    void analyzeMapsTimeoutToDownstreamTimeoutException() {
        WebClientRequestException timeout = new WebClientRequestException(
                new SocketTimeoutException("read timeout"),
                HttpMethod.POST,
                URI.create("http://ai-service/v1/analysis/interpret"),
                HttpHeaders.EMPTY
        );
        WebClient webClient = WebClient.builder()
                .exchangeFunction(request -> Mono.error(timeout))
                .build();

        AiAnalysisClient client = new AiAnalysisClient(webClient);

        assertThatThrownBy(() -> client.analyze(request()))
                .isInstanceOf(DownstreamTimeoutException.class)
                .satisfies(exception -> {
                    DownstreamTimeoutException downstream = (DownstreamTimeoutException) exception;
                    assertThat(downstream.getErrorCode()).isEqualTo("ai_service_timeout");
                });
    }

    private WebClient webClientResponding(HttpStatus status, String body) {
        return webClientResponding(status, body, MediaType.APPLICATION_JSON);
    }

    private WebClient webClientResponding(HttpStatus status, String body, MediaType contentType) {
        ClientResponse response = ClientResponse.create(status)
                .header(HttpHeaders.CONTENT_TYPE, contentType.toString())
                .body(body)
                .build();
        return WebClient.builder()
                .exchangeFunction(request -> Mono.just(response))
                .build();
    }

    private AiAnalysisRequest request() {
        return new AiAnalysisRequest(
                "req-77",
                "user-1",
                "session-1",
                "frame-1",
                Instant.parse("2026-04-08T09:00:00Z"),
                "UTC",
                "ZmFrZQ==",
                "image/jpeg",
                new AiAnalysisRequest.AnalysisSettings("MEDIUM", "API", true),
                new AiAnalysisRequest.VisionContext(
                        true,
                        "good",
                        1280,
                        720,
                        List.of(),
                        new AiAnalysisRequest.VisionSignals(
                                120.0,
                                0.3,
                                0.4,
                                0.2,
                                0.3,
                                0.1,
                                0.8,
                                0.7,
                                0.6,
                                0.2,
                                0.1,
                                0.05,
                                0.2
                        )
                )
        );
    }
}
