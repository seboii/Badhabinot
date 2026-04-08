package com.badhabinot.backend.config;

import io.netty.channel.ChannelOption;
import io.netty.handler.timeout.ReadTimeoutHandler;
import java.util.concurrent.TimeUnit;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.client.reactive.ReactorClientHttpConnector;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.netty.http.client.HttpClient;

@Configuration
public class ClientConfiguration {

    @Bean("visionServiceWebClient")
    public WebClient visionServiceWebClient(WebClient.Builder builder, IntegrationProperties properties) {
        return build(builder, properties.visionService(), properties.internalApiKey());
    }

    @Bean("aiServiceWebClient")
    public WebClient aiServiceWebClient(WebClient.Builder builder, IntegrationProperties properties) {
        return build(builder, properties.aiService(), properties.internalApiKey());
    }

    @Bean("aiServiceHealthWebClient")
    public WebClient aiServiceHealthWebClient(@Qualifier("aiServiceWebClient") WebClient webClient) {
        return webClient;
    }

    private WebClient build(WebClient.Builder builder, IntegrationProperties.Downstream downstream, String internalApiKey) {
        HttpClient httpClient = HttpClient.create()
                .option(ChannelOption.CONNECT_TIMEOUT_MILLIS, (int) downstream.connectTimeout().toMillis())
                .doOnConnected(connection -> connection.addHandlerLast(
                        new ReadTimeoutHandler(downstream.readTimeout().toMillis(), TimeUnit.MILLISECONDS)
                ));

        return builder
                .baseUrl(downstream.baseUrl())
                .clientConnector(new ReactorClientHttpConnector(httpClient))
                .defaultHeader(HttpHeaders.CONTENT_TYPE, MediaType.APPLICATION_JSON_VALUE)
                .defaultHeader("X-Internal-Api-Key", internalApiKey)
                .build();
    }
}
