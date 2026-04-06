package com.badhabinot.monitoring.infrastructure.client;

import com.badhabinot.monitoring.application.dto.InternalUserAnalysisContext;
import com.badhabinot.monitoring.application.exception.DownstreamServiceException;
import com.badhabinot.monitoring.application.exception.DownstreamTimeoutException;
import java.time.Duration;
import java.util.UUID;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.http.HttpStatusCode;
import org.springframework.stereotype.Component;
import org.springframework.web.reactive.function.client.WebClient;
import org.springframework.web.reactive.function.client.WebClientRequestException;
import reactor.core.publisher.Mono;

@Component
public class UserContextClient {

    private final WebClient webClient;

    public UserContextClient(@Qualifier("userServiceWebClient") WebClient webClient) {
        this.webClient = webClient;
    }

    public InternalUserAnalysisContext fetch(UUID userId) {
        try {
            return webClient.get()
                    .uri("/internal/users/{userId}/analysis-context", userId)
                    .retrieve()
                    .onStatus(HttpStatusCode::isError, response -> response.bodyToMono(String.class)
                            .defaultIfEmpty("user-service error")
                            .flatMap(body -> Mono.error(new DownstreamServiceException("user_service_error", body))))
                    .bodyToMono(InternalUserAnalysisContext.class)
                    .block(Duration.ofSeconds(6));
        } catch (DownstreamServiceException exception) {
            throw exception;
        } catch (WebClientRequestException exception) {
            if (isTimeout(exception)) {
                throw new DownstreamTimeoutException("user_service_timeout", "Timed out while retrieving analysis context from user-service");
            }
            throw new DownstreamServiceException("user_service_unavailable", "Unable to reach user-service");
        } catch (Exception exception) {
            throw new DownstreamServiceException("user_service_unavailable", "Unexpected failure while calling user-service");
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
