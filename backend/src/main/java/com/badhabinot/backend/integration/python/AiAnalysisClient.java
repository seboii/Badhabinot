package com.badhabinot.backend.integration.python;

import com.badhabinot.backend.dto.monitoring.AiAnalysisRequest;
import com.badhabinot.backend.dto.monitoring.AiAnalysisResponse;
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
public class AiAnalysisClient {

    private final WebClient webClient;

    public AiAnalysisClient(@Qualifier("aiServiceWebClient") WebClient webClient) {
        this.webClient = webClient;
    }

    public AiAnalysisInvocation analyze(AiAnalysisRequest request) {
        long started = System.nanoTime();
        try {
            AiAnalysisResponse analysisResponse = webClient.post()
                    .uri("/v1/analysis/interpret")
                    .bodyValue(request)
                    .retrieve()
                    .onStatus(HttpStatusCode::isError, clientResponse -> clientResponse.bodyToMono(String.class)
                            .defaultIfEmpty("ai-service error")
                            .flatMap(body -> Mono.error(new DownstreamServiceException("ai_service_error", body))))
                    .bodyToMono(AiAnalysisResponse.class)
                    .block(Duration.ofSeconds(20));
            long latencyMs = (System.nanoTime() - started) / 1_000_000;
            return new AiAnalysisInvocation(analysisResponse, latencyMs);
        } catch (DownstreamServiceException exception) {
            throw exception;
        } catch (WebClientRequestException exception) {
            if (isTimeout(exception)) {
                throw new DownstreamTimeoutException("ai_service_timeout", "Timed out while waiting for ai-service");
            }
            throw new DownstreamServiceException("ai_service_unavailable", "Unable to reach ai-service");
        } catch (Exception exception) {
            throw new DownstreamServiceException("ai_service_unavailable", "Unexpected failure while calling ai-service");
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

    public record AiAnalysisInvocation(
            AiAnalysisResponse response,
            long latencyMs
    ) {
    }
}

