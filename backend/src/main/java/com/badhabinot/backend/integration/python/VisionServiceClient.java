package com.badhabinot.backend.integration.python;

import com.badhabinot.backend.dto.monitoring.FaceRegisterRequest;
import com.badhabinot.backend.dto.monitoring.FaceRegisterResponse;
import com.badhabinot.backend.dto.monitoring.FaceVerificationResponse;
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
        return analyze(request, true);
    }

    /**
     * @param renderOverlay when true, the vision service will render all CV2 overlays
     *                      onto the frame and return the result as annotatedFrameBase64.
     *                      Set to false for lightweight analysis calls (e.g., health checks).
     */
    public VisionAnalysisResponse analyze(VisionAnalysisRequest request, boolean renderOverlay) {
        try {
            return webClient.post()
                    .uri(uriBuilder -> uriBuilder
                            .path("/v1/vision/analyze")
                            .queryParam("render_overlay", renderOverlay)
                            .build())
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

    /** Register one face frame for a user (Phase 2 — face enrolment). */
    public FaceRegisterResponse registerFace(String userId, FaceRegisterRequest request) {
        try {
            var visionRequest = new java.util.HashMap<String, String>();
            visionRequest.put("user_id", userId);
            visionRequest.put("image_base64", request.imageBase64());
            visionRequest.put("image_content_type",
                    request.imageContentType() != null ? request.imageContentType() : "image/jpeg");
            if (request.poseHint() != null) {
                visionRequest.put("pose_hint", request.poseHint());
            }

            return webClient.post()
                    .uri("/v1/vision/face/register")
                    .bodyValue(visionRequest)
                    .retrieve()
                    .onStatus(HttpStatusCode::isError, response -> response.bodyToMono(String.class)
                            .defaultIfEmpty("face-registration error")
                            .flatMap(body -> Mono.error(new DownstreamServiceException("vision_face_error", body))))
                    .bodyToMono(FaceRegisterResponse.class)
                    .block(Duration.ofSeconds(15));
        } catch (DownstreamServiceException exception) {
            throw exception;
        } catch (WebClientRequestException exception) {
            if (isTimeout(exception)) {
                throw new DownstreamTimeoutException("vision_face_timeout", "Timed out during face registration");
            }
            throw new DownstreamServiceException("vision_service_unavailable", "Unable to reach vision-service");
        } catch (Exception exception) {
            throw new DownstreamServiceException("vision_service_unavailable", "Unexpected failure during face registration");
        }
    }

    /** Delete stored face profile for a user. */
    public void deleteFaceProfile(String userId) {
        try {
            webClient.delete()
                    .uri("/v1/vision/face/{userId}", userId)
                    .retrieve()
                    .onStatus(HttpStatusCode::isError, response -> response.bodyToMono(String.class)
                            .defaultIfEmpty("face-delete error")
                            .flatMap(body -> Mono.error(new DownstreamServiceException("vision_face_error", body))))
                    .bodyToMono(Void.class)
                    .block(Duration.ofSeconds(10));
        } catch (DownstreamServiceException exception) {
            throw exception;
        } catch (Exception exception) {
            throw new DownstreamServiceException("vision_service_unavailable", "Unexpected failure during face profile deletion");
        }
    }

    /** Verify a face image against stored embeddings for login. */
    public FaceVerificationResponse verifyFace(String userId, String imageBase64, String contentType) {
        try {
            var body = new java.util.HashMap<String, String>();
            body.put("image_base64", imageBase64);
            body.put("image_content_type", contentType != null ? contentType : "image/jpeg");

            return webClient.post()
                    .uri("/v1/vision/face/{userId}/verify", userId)
                    .bodyValue(body)
                    .retrieve()
                    .onStatus(HttpStatusCode::isError, response -> response.bodyToMono(String.class)
                            .defaultIfEmpty("face-verify error")
                            .flatMap(b -> Mono.error(new DownstreamServiceException("vision_face_error", b))))
                    .bodyToMono(FaceVerificationResponse.class)
                    .block(Duration.ofSeconds(10));
        } catch (DownstreamServiceException exception) {
            throw exception;
        } catch (WebClientRequestException exception) {
            if (isTimeout(exception)) {
                throw new DownstreamTimeoutException("vision_face_timeout", "Timed out during face verification");
            }
            throw new DownstreamServiceException("vision_service_unavailable", "Unable to reach vision-service");
        } catch (Exception exception) {
            throw new DownstreamServiceException("vision_service_unavailable", "Unexpected failure during face verification");
        }
    }

    /** Return enrolment status for a user. */
    public FaceRegisterResponse faceStatus(String userId) {
        try {
            return webClient.get()
                    .uri("/v1/vision/face/{userId}/status", userId)
                    .retrieve()
                    .onStatus(HttpStatusCode::isError, response -> response.bodyToMono(String.class)
                            .defaultIfEmpty("face-status error")
                            .flatMap(body -> Mono.error(new DownstreamServiceException("vision_face_error", body))))
                    .bodyToMono(FaceRegisterResponse.class)
                    .block(Duration.ofSeconds(10));
        } catch (DownstreamServiceException exception) {
            throw exception;
        } catch (Exception exception) {
            throw new DownstreamServiceException("vision_service_unavailable", "Unexpected failure while checking face status");
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

