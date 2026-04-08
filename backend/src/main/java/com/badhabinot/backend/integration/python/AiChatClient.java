package com.badhabinot.backend.integration.python;

import com.badhabinot.backend.dto.monitoring.AiChatRequest;
import com.badhabinot.backend.dto.monitoring.AiChatResponse;
import com.badhabinot.backend.common.exception.monitoring.DownstreamServiceException;
import com.badhabinot.backend.common.exception.monitoring.DownstreamTimeoutException;
import java.time.Duration;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.http.HttpStatusCode;
import org.springframework.stereotype.Component;
import org.springframework.web.reactive.function.client.WebClient;
import org.springframework.web.reactive.function.client.WebClientRequestException;
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
                    .block(Duration.ofSeconds(20));
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

