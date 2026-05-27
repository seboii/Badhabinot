package com.badhabinot.backend.integration.python;

import com.badhabinot.backend.dto.monitoring.AiChatRequest;
import com.badhabinot.backend.dto.monitoring.AiChatResponse;
import com.badhabinot.backend.common.exception.monitoring.DownstreamServiceException;
import com.badhabinot.backend.common.exception.monitoring.DownstreamTimeoutException;
import java.time.Duration;
import java.util.Map;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.http.HttpStatusCode;
import org.springframework.http.MediaType;
import org.springframework.http.codec.ServerSentEvent;
import org.springframework.stereotype.Component;
import org.springframework.web.reactive.function.client.WebClient;
import org.springframework.web.reactive.function.client.WebClientRequestException;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

@Component
public class AiChatClient {

    private final WebClient webClient;

    public AiChatClient(@Qualifier("aiServiceWebClient") WebClient webClient) {
        this.webClient = webClient;
    }

    public AiChatResponse respond(AiChatRequest request) {
        try {
            return webClient.post()
                    .uri("/v1/chat/respond")
                    .bodyValue(request)
                    .retrieve()
                    .onStatus(HttpStatusCode::isError, clientResponse -> clientResponse.bodyToMono(String.class)
                            .defaultIfEmpty("ai-service chat error")
                            .flatMap(body -> Mono.error(new DownstreamServiceException("ai_chat_service_error", body))))
                    .bodyToMono(AiChatResponse.class)
                    .block("LOCAL".equals(request.aiMode()) ? Duration.ofSeconds(60) : Duration.ofSeconds(20));
        } catch (DownstreamServiceException exception) {
            throw exception;
        } catch (WebClientRequestException exception) {
            if (isTimeout(exception)) {
                throw new DownstreamTimeoutException("ai_chat_service_timeout", "Timed out while waiting for ai-service chat");
            }
            throw new DownstreamServiceException("ai_chat_service_unavailable", "Unable to reach ai-service chat endpoint");
        } catch (Exception exception) {
            throw new DownstreamServiceException("ai_chat_service_unavailable", "Unexpected failure while calling ai-service chat");
        }
    }

    public Flux<String> respondStream(AiChatRequest request) {
        return webClient.post()
                .uri("/v1/chat/stream")
                .bodyValue(request)
                .accept(MediaType.TEXT_EVENT_STREAM)
                .retrieve()
                .onStatus(HttpStatusCode::isError, clientResponse -> clientResponse.bodyToMono(String.class)
                        .defaultIfEmpty("ai-service stream error")
                        .flatMap(body -> Mono.error(new DownstreamServiceException("ai_chat_stream_error", body))))
                .bodyToFlux(new ParameterizedTypeReference<ServerSentEvent<String>>() {})
                .mapNotNull(ServerSentEvent::data)
                .timeout(Duration.ofSeconds(300));
    }

    public Map<String, Object> ollamaHealth(String baseUrl, String modelName) {
        try {
            return webClient.get()
                    .uri(uriBuilder -> uriBuilder
                            .path("/health/ollama")
                            .queryParam("base_url", baseUrl)
                            .queryParam("model_name", modelName)
                            .build())
                    .retrieve()
                    .onStatus(HttpStatusCode::isError, clientResponse -> clientResponse.bodyToMono(String.class)
                            .defaultIfEmpty("ai-service ollama health error")
                            .flatMap(body -> Mono.error(new DownstreamServiceException("ollama_health_error", body))))
                    .bodyToMono(new ParameterizedTypeReference<Map<String, Object>>() {})
                    .block(Duration.ofSeconds(10));
        } catch (DownstreamServiceException exception) {
            throw exception;
        } catch (WebClientRequestException exception) {
            if (isTimeout(exception)) {
                throw new DownstreamTimeoutException("ollama_health_timeout", "Timed out while checking Ollama health");
            }
            throw new DownstreamServiceException("ollama_health_unavailable", "Unable to reach ai-service Ollama health endpoint");
        } catch (Exception exception) {
            throw new DownstreamServiceException("ollama_health_unavailable", "Unexpected failure while checking Ollama health");
        }
    }

    private boolean isTimeout(Throwable throwable) {
        Throwable cursor = throwable;
        while (cursor != null) {
            String simpleName = cursor.getClass().getSimpleName().toLowerCase();
            if (simpleName.contains("timeout")) {
                return true;
            }
            cursor = cursor.getCause();
        }
        return false;
    }
}

