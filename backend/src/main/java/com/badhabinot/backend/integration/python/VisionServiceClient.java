package com.badhabinot.backend.integration.python;

import com.badhabinot.backend.dto.monitoring.VisionAnalysisRequest;
import com.badhabinot.backend.dto.monitoring.VisionAnalysisResponse;
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
public class VisionServiceClient {

    private final WebClient webClient;

    public VisionServiceClient(@Qualifier("visionServiceWebClient") WebClient webClient) {
        this.webClient = webClient;
    }

    public VisionAnalysisResponse analyze(VisionAnalysisRequest request) {
        try {
            return webClient.post()
                    .uri("/v1/vision/analyze")
                    .bodyValue(request)
                    .retrieve()
                    .onStatus(HttpStatusCode::isError, response -> response.bodyToMono(String.class)
                            .defaultIfEmpty("vision-service error")
                            .flatMap(body -> Mono.error(new DownstreamServiceException("vision_service_error", body))))
                    .bodyToMono(VisionAnalysisResponse.class)
                    .block(Duration.ofSeconds(10));
        } catch (DownstreamServiceException exception) {
            throw exception;
        } catch (WebClientRequestException exception) {
            if (isTimeout(exception)) {
                throw new DownstreamTimeoutException("vision_service_timeout", "Timed out while waiting for vision-service");
            }
            throw new DownstreamServiceException("vision_service_unavailable", "Unable to reach vision-service");
        } catch (Exception exception) {
            throw new DownstreamServiceException("vision_service_unavailable", "Unexpected failure while calling vision-service");
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

