package com.badhabinot.auth.infrastructure.client;

import com.badhabinot.auth.application.exception.UserProvisioningException;
import com.badhabinot.auth.infrastructure.config.UserServiceProperties;
import java.util.Map;
import java.util.UUID;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatusCode;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.web.client.RestClient;

@Component
public class UserProvisioningClient {

    private final RestClient restClient;
    private final UserServiceProperties userServiceProperties;

    public UserProvisioningClient(RestClient.Builder restClientBuilder, UserServiceProperties userServiceProperties) {
        this.userServiceProperties = userServiceProperties;
        SimpleClientHttpRequestFactory requestFactory = new SimpleClientHttpRequestFactory();
        requestFactory.setConnectTimeout((int) userServiceProperties.connectTimeout().toMillis());
        requestFactory.setReadTimeout((int) userServiceProperties.readTimeout().toMillis());
        this.restClient = restClientBuilder
                .baseUrl(userServiceProperties.baseUrl())
                .requestFactory(requestFactory)
                .defaultHeader(HttpHeaders.CONTENT_TYPE, MediaType.APPLICATION_JSON_VALUE)
                .build();
    }

    public void bootstrapUser(UUID userId, String email, String displayName, String timezone, String locale) {
        try {
            restClient.post()
                    .uri("/internal/users/bootstrap")
                    .header("X-Internal-Api-Key", userServiceProperties.internalApiKey())
                    .body(Map.of(
                            "user_id", userId,
                            "email", email,
                            "display_name", displayName,
                            "timezone", timezone,
                            "locale", locale
                    ))
                    .retrieve()
                    .onStatus(HttpStatusCode::isError, (request, response) -> {
                        throw new UserProvisioningException(
                                "user-service bootstrap request failed with status " + response.getStatusCode().value(),
                                new IllegalStateException("Unexpected user-service bootstrap response")
                        );
                    })
                    .toBodilessEntity();
        } catch (RuntimeException exception) {
            throw new UserProvisioningException("User was created in auth-service but provisioning failed in user-service", exception);
        }
    }
}
