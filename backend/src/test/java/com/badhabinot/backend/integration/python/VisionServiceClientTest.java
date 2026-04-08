package com.badhabinot.backend.integration.python;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import com.badhabinot.backend.dto.monitoring.VisionAnalysisRequest;
import com.badhabinot.backend.common.exception.monitoring.DownstreamServiceException;
import com.badhabinot.backend.common.exception.monitoring.DownstreamTimeoutException;
import java.net.SocketTimeoutException;
import java.net.URI;
import java.time.Instant;
import org.junit.jupiter.api.Test;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.web.reactive.function.client.ClientResponse;
import org.springframework.web.reactive.function.client.WebClient;
import org.springframework.web.reactive.function.client.WebClientRequestException;
import reactor.core.publisher.Mono;

class VisionServiceClientTest {

    @Test
    void analyzeReturnsResponseWhenVisionServiceSucceeds() {
        VisionServiceClient client = new VisionServiceClient(webClientResponding(HttpStatus.OK, """
                {
                  "requestId": "req-1",
                  "subjectPresent": true,
                  "postureState": "good",
                  "postureConfidence": 0.83,
                  "detections": [],
                  "signals": {
                    "brightnessMean": 122.1,
                    "edgeDensity": 0.2,
                    "centerEdgeDensity": 0.4,
                    "postureRiskScore": 0.31,
                    "handFaceProximityScore": 0.22,
                    "elongatedObjectScore": 0.11,
                    "focusScore": 0.73,
                    "postureConfidence": 0.83,
                    "postureAlignmentScore": 0.62,
                    "handMotionScore": 0.15,
                    "repetitiveMotionScore": 0.08,
                    "smokingGestureScore": 0.02,
                    "faceSizeRatio": 0.19
                  },
                  "processing": {
                    "frameWidth": 1280,
                    "frameHeight": 720,
                    "brightnessMean": 122.1,
                    "edgeDensity": 0.2,
                    "focusScore": 0.73,
                    "visionLatencyMs": 44
                  }
                }
                """));

        var response = client.analyze(request());

        assertThat(response.requestId()).isEqualTo("req-1");
        assertThat(response.subjectPresent()).isTrue();
        assertThat(response.processing().visionLatencyMs()).isEqualTo(44);
        assertThat(response.signals().postureRiskScore()).isEqualTo(0.31);
    }

    @Test
    void analyzeMapsHttpErrorsToDownstreamServiceException() {
        VisionServiceClient client = new VisionServiceClient(webClientResponding(
                HttpStatus.BAD_GATEWAY,
                "vision backend failed",
                MediaType.TEXT_PLAIN
        ));

        assertThatThrownBy(() -> client.analyze(request()))
                .isInstanceOf(DownstreamServiceException.class)
                .satisfies(exception -> {
                    DownstreamServiceException downstream = (DownstreamServiceException) exception;
                    assertThat(downstream.getErrorCode()).isEqualTo("vision_service_error");
                    assertThat(downstream).hasMessageContaining("vision backend failed");
                });
    }

    @Test
    void analyzeMapsTimeoutErrorsToDownstreamTimeoutException() {
        WebClientRequestException timeout = new WebClientRequestException(
                new SocketTimeoutException("read timed out"),
                HttpMethod.POST,
                URI.create("http://vision-service/v1/vision/analyze"),
                HttpHeaders.EMPTY
        );
        WebClient webClient = WebClient.builder()
                .exchangeFunction(request -> Mono.error(timeout))
                .build();

        VisionServiceClient client = new VisionServiceClient(webClient);

        assertThatThrownBy(() -> client.analyze(request()))
                .isInstanceOf(DownstreamTimeoutException.class)
                .satisfies(exception -> {
                    DownstreamTimeoutException downstream = (DownstreamTimeoutException) exception;
                    assertThat(downstream.getErrorCode()).isEqualTo("vision_service_timeout");
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

    private VisionAnalysisRequest request() {
        return new VisionAnalysisRequest(
                "req-1",
                "user-1",
                "session-1",
                "frame-1",
                Instant.parse("2026-04-08T09:00:00Z"),
                "ZmFrZQ==",
                "image/jpeg"
        );
    }
}
