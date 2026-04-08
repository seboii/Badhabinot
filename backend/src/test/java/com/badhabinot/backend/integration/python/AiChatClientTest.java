package com.badhabinot.backend.integration.python;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import com.badhabinot.backend.dto.monitoring.AiChatRequest;
import com.badhabinot.backend.common.exception.monitoring.DownstreamServiceException;
import java.io.IOException;
import java.net.URI;
import java.time.Instant;
import java.time.LocalDate;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.web.reactive.function.client.ClientResponse;
import org.springframework.web.reactive.function.client.WebClient;
import org.springframework.web.reactive.function.client.WebClientRequestException;
import reactor.core.publisher.Mono;

class AiChatClientTest {

    @Test
    void respondReturnsGroundedAnswerOnSuccess() {
        AiChatClient client = new AiChatClient(webClientResponding(HttpStatus.OK, """
                {
                  "conversationId": "conv-1",
                  "answer": "Hydration is behind your daily goal.",
                  "groundedFacts": ["Hydration reached 1400/2500 ml."],
                  "followUpSuggestions": ["Add one reminder at 15:00."],
                  "model": {
                    "provider": "openai-compatible",
                    "name": "gpt-4.1-mini",
                    "mode": "external_api"
                  }
                }
                """));

        var response = client.respond(request());

        assertThat(response.answer()).contains("Hydration is behind");
        assertThat(response.groundedFacts()).containsExactly("Hydration reached 1400/2500 ml.");
        assertThat(response.model().provider()).isEqualTo("openai-compatible");
    }

    @Test
    void respondMapsHttpErrorsToDownstreamServiceException() {
        AiChatClient client = new AiChatClient(webClientResponding(
                HttpStatus.BAD_GATEWAY,
                "ai chat backend failed",
                MediaType.TEXT_PLAIN
        ));

        assertThatThrownBy(() -> client.respond(request()))
                .isInstanceOf(DownstreamServiceException.class)
                .satisfies(exception -> {
                    DownstreamServiceException downstream = (DownstreamServiceException) exception;
                    assertThat(downstream.getErrorCode()).isEqualTo("ai_chat_service_error");
                    assertThat(downstream).hasMessageContaining("ai chat backend failed");
                });
    }

    @Test
    void respondMapsNetworkErrorsToUnavailableException() {
        WebClientRequestException requestException = new WebClientRequestException(
                new IOException("connection reset"),
                HttpMethod.POST,
                URI.create("http://ai-service/v1/chat/respond"),
                HttpHeaders.EMPTY
        );
        WebClient webClient = WebClient.builder()
                .exchangeFunction(request -> Mono.error(requestException))
                .build();

        AiChatClient client = new AiChatClient(webClient);

        assertThatThrownBy(() -> client.respond(request()))
                .isInstanceOf(DownstreamServiceException.class)
                .satisfies(exception -> {
                    DownstreamServiceException downstream = (DownstreamServiceException) exception;
                    assertThat(downstream.getErrorCode()).isEqualTo("ai_chat_service_unavailable");
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

    private AiChatRequest request() {
        return new AiChatRequest(
                "conv-1",
                "user-1",
                "UTC",
                LocalDate.of(2026, 4, 8),
                "Summarize my posture trend.",
                List.of(new AiChatRequest.Message("user", "How was my day?", Instant.parse("2026-04-08T08:00:00Z"))),
                new AiChatRequest.Context(
                        1400,
                        2500,
                        18,
                        6,
                        3,
                        1,
                        4,
                        0.38,
                        "Posture and hydration gaps were observed.",
                        List.of("Increase hydration checkpoints."),
                        List.of(new AiChatRequest.Fact("posture_alert_count", "6")),
                        List.of(),
                        List.of(),
                        List.of(),
                        Map.of("poor_posture", 6),
                        Map.of("water_reminder", 2),
                        List.of(),
                        7,
                        420,
                        9800,
                        120,
                        "Compared with 2026-04-07: posture alerts +2, hydration -300 ml, smoking-like cues +1.",
                        List.of()
                )
        );
    }
}
