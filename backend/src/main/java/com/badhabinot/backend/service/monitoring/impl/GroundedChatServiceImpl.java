package com.badhabinot.backend.service.monitoring.impl;

import com.badhabinot.backend.dto.monitoring.AiChatRequest;
import com.badhabinot.backend.dto.monitoring.AiChatResponse;
import com.badhabinot.backend.dto.monitoring.ChatHistoryResponse;
import com.badhabinot.backend.dto.monitoring.ChatMessageResponse;
import com.badhabinot.backend.dto.monitoring.ChatRequest;
import com.badhabinot.backend.dto.monitoring.ChatResponse;
import com.badhabinot.backend.dto.monitoring.DailyReportResponse;
import com.badhabinot.backend.dto.monitoring.InternalUserAnalysisContext;
import com.badhabinot.backend.model.monitoring.ChatMessage;
import com.badhabinot.backend.repository.monitoring.ChatMessageRepository;
import com.badhabinot.backend.integration.python.AiChatClient;
import com.badhabinot.backend.service.monitoring.IChatContextBuilderService;
import com.badhabinot.backend.service.monitoring.IDailyReportService;
import com.badhabinot.backend.service.monitoring.IGroundedChatService;
import com.badhabinot.backend.service.user.IUserContextService;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.IOException;
import java.time.Duration;
import java.time.LocalDate;
import java.time.ZoneId;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.UUID;
import java.util.concurrent.atomic.AtomicReference;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.data.domain.PageRequest;
import org.springframework.security.oauth2.jwt.Jwt;
import org.springframework.stereotype.Service;
import org.springframework.transaction.PlatformTransactionManager;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.transaction.support.TransactionSynchronization;
import org.springframework.transaction.support.TransactionSynchronizationManager;
import org.springframework.transaction.support.TransactionTemplate;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;
import reactor.core.scheduler.Schedulers;

@Service
public class GroundedChatServiceImpl implements IGroundedChatService {

    private static final TypeReference<Map<String, Object>> MAP_TYPE = new TypeReference<>() {
    };
    private static final int AI_HISTORY_LIMIT = 12;
    private static final int RECENT_MESSAGES_LIMIT = 50;

    private final ChatMessageRepository chatMessageRepository;
    private final IUserContextService userContextService;
    private final IDailyReportService dailyReportService;
    private final IChatContextBuilderService chatContextBuilderService;
    private final AiChatClient aiChatClient;
    private final ObjectMapper objectMapper;
    private final TransactionTemplate monitoringTx;

    public GroundedChatServiceImpl(
            ChatMessageRepository chatMessageRepository,
            IUserContextService userContextService,
            IDailyReportService dailyReportService,
            IChatContextBuilderService chatContextBuilderService,
            AiChatClient aiChatClient,
            ObjectMapper objectMapper,
            @Qualifier("monitoringTransactionManager") PlatformTransactionManager txManager
    ) {
        this.chatMessageRepository = chatMessageRepository;
        this.userContextService = userContextService;
        this.dailyReportService = dailyReportService;
        this.chatContextBuilderService = chatContextBuilderService;
        this.aiChatClient = aiChatClient;
        this.objectMapper = objectMapper;
        this.monitoringTx = new TransactionTemplate(txManager);
    }

    @Override
    @Transactional(transactionManager = "monitoringTransactionManager", readOnly = true)
    public ChatHistoryResponse history(Jwt jwt, String conversationId, int limit) {
        UUID userId = UUID.fromString(jwt.getSubject());
        int boundedLimit = Math.max(1, Math.min(limit, RECENT_MESSAGES_LIMIT));
        UUID resolvedConversationId = resolveConversationIdForHistory(userId, conversationId);

        if (resolvedConversationId == null) {
            return new ChatHistoryResponse(null, List.of());
        }

        List<ChatMessageResponse> messages = loadConversationMessages(userId, resolvedConversationId, boundedLimit).stream()
                .map(this::toResponse)
                .toList();
        return new ChatHistoryResponse(resolvedConversationId.toString(), messages);
    }

    @Override
    @Transactional(transactionManager = "monitoringTransactionManager")
    public ChatResponse chat(Jwt jwt, ChatRequest request) {
        UUID userId = UUID.fromString(jwt.getSubject());
        InternalUserAnalysisContext context = userContextService.getMonitoringAnalysisContext(userId);
        LocalDate reportDate = LocalDate.now(zoneId(context.timezone()));
        DailyReportResponse report = dailyReportService.getDailyReport(userId, reportDate, context);

        UUID conversationId = resolveConversationIdForChat(userId, request.conversationId());

        ChatMessage userMessage = chatMessageRepository.save(ChatMessage.create(conversationId, userId, "user", request.message()));
        List<AiChatRequest.Message> historyItems = loadConversationMessages(userId, conversationId, AI_HISTORY_LIMIT + 1).stream()
                .filter(message -> !message.getId().equals(userMessage.getId()))
                .map(message -> new AiChatRequest.Message(message.getRole(), message.getContent(), message.getCreatedAt()))
                .toList();

        AiChatRequest.Context aiContext = chatContextBuilderService.build(userId, context, reportDate, report);

        AiChatResponse aiResponse = aiChatClient.respond(new AiChatRequest(
                conversationId.toString(),
                userId.toString(),
                context.timezone(),
                report.reportDate(),
                request.message(),
                historyItems,
                aiContext,
                context.modelMode(),
                context.localModelName(),
                context.ollamaBaseUrl()
        ));

        Map<String, Object> metadata = new LinkedHashMap<>();
        metadata.put("grounded_facts", safeList(aiResponse.groundedFacts()));
        metadata.put("follow_up_suggestions", safeList(aiResponse.followUpSuggestions()));
        Map<String, Object> modelMetadata = new LinkedHashMap<>();
        modelMetadata.put("provider", aiResponse.model().provider());
        modelMetadata.put("name", aiResponse.model().name());
        modelMetadata.put("mode", aiResponse.model().mode());
        metadata.put("model", modelMetadata);

        ChatMessage assistantMessage = chatMessageRepository.save(ChatMessage.create(
                conversationId,
                userId,
                "assistant",
                aiResponse.answer(),
                writeJson(metadata)
        ));

        List<ChatMessageResponse> recentMessages = loadConversationMessages(userId, conversationId, RECENT_MESSAGES_LIMIT).stream()
                .map(this::toResponse)
                .toList();

        return new ChatResponse(
                conversationId.toString(),
                assistantMessage.getId(),
                aiResponse.answer(),
                aiResponse.groundedFacts(),
                aiResponse.followUpSuggestions(),
                recentMessages,
                new ChatResponse.ModelDetails(
                        aiResponse.model().provider(),
                        aiResponse.model().name(),
                        aiResponse.model().mode()
                )
        );
    }

    @Override
    public SseEmitter chatStream(Jwt jwt, ChatRequest request) {
        UUID userId = UUID.fromString(jwt.getSubject());

        // Read context — each service manages its own transaction
        InternalUserAnalysisContext context = userContextService.getMonitoringAnalysisContext(userId);
        LocalDate reportDate = LocalDate.now(zoneId(context.timezone()));
        DailyReportResponse report = dailyReportService.getDailyReport(userId, reportDate, context);

        // Transaction 1: save user message, resolve conversation, load history
        record SetupData(UUID conversationId, AiChatRequest aiRequest) {}
        SetupData setup = Objects.requireNonNull(monitoringTx.execute(status -> {
            UUID conversationId = resolveConversationIdForChat(userId, request.conversationId());
            ChatMessage userMessage = chatMessageRepository.save(
                    ChatMessage.create(conversationId, userId, "user", request.message()));
            List<AiChatRequest.Message> historyItems = loadConversationMessages(userId, conversationId, AI_HISTORY_LIMIT + 1)
                    .stream()
                    .filter(m -> !m.getId().equals(userMessage.getId()))
                    .map(m -> new AiChatRequest.Message(m.getRole(), m.getContent(), m.getCreatedAt()))
                    .toList();
            AiChatRequest.Context aiContext = chatContextBuilderService.build(userId, context, reportDate, report);
            return new SetupData(conversationId, new AiChatRequest(
                    conversationId.toString(), userId.toString(), context.timezone(), report.reportDate(),
                    request.message(), historyItems, aiContext,
                    context.modelMode(), context.localModelName(), context.ollamaBaseUrl()));
        }));

        SseEmitter emitter = new SseEmitter(300_000L);
        emitter.onTimeout(emitter::complete);

        final UUID finalUserId = userId;
        final UUID finalConversationId = setup.conversationId();
        final AtomicReference<StringBuilder> accumulated = new AtomicReference<>(new StringBuilder());
        final AtomicReference<List<String>> finalGroundedFacts = new AtomicReference<>(List.of());
        final AtomicReference<List<String>> finalFollowUps = new AtomicReference<>(List.of());

        Thread.ofVirtual().start(() -> {
            try {
                aiChatClient.respondStream(setup.aiRequest())
                        .publishOn(Schedulers.boundedElastic())
                        .doOnNext(data -> {
                            try {
                                JsonNode node = objectMapper.readTree(data);
                                if (node.has("token")) {
                                    String token = node.get("token").asText();
                                    accumulated.get().append(token);
                                    emitter.send(SseEmitter.event()
                                            .data(objectMapper.writeValueAsString(Map.of("token", token))));
                                } else if (node.path("done").asBoolean(false)) {
                                    finalGroundedFacts.set(extractStringList(node, "grounded_facts"));
                                    finalFollowUps.set(extractStringList(node, "follow_up_suggestions"));
                                }
                            } catch (Exception ignored) {}
                        })
                        .blockLast(Duration.ofSeconds(300));

                // Transaction 2: save assistant message
                Map<String, Object> metadata = new LinkedHashMap<>();
                metadata.put("grounded_facts", finalGroundedFacts.get());
                metadata.put("follow_up_suggestions", finalFollowUps.get());
                monitoringTx.execute(status -> {
                    chatMessageRepository.save(ChatMessage.create(
                            finalConversationId, finalUserId, "assistant",
                            accumulated.get().toString(), writeJson(metadata)));
                    return null;
                });

                emitter.send(SseEmitter.event().data(objectMapper.writeValueAsString(Map.of(
                        "done", true,
                        "conversationId", finalConversationId.toString(),
                        "groundedFacts", finalGroundedFacts.get(),
                        "followUpSuggestions", finalFollowUps.get()
                ))));
                emitter.complete();
            } catch (Exception e) {
                emitter.completeWithError(e);
            }
        });

        return emitter;
    }

    private List<String> extractStringList(JsonNode node, String fieldName) {
        JsonNode array = node.get(fieldName);
        if (array == null || !array.isArray()) return List.of();
        List<String> result = new ArrayList<>();
        for (JsonNode item : array) {
            if (item.isTextual()) result.add(item.asText());
        }
        return result;
    }

    private ChatMessageResponse toResponse(ChatMessage message) {
        return new ChatMessageResponse(
                message.getId(),
                message.getConversationId().toString(),
                message.getRole(),
                message.getContent(),
                message.getCreatedAt(),
                readJson(message.getMetadataJson())
        );
    }

    private List<ChatMessage> loadConversationMessages(UUID userId, UUID conversationId, int limit) {
        return chatMessageRepository.findByUserIdAndConversationIdOrderByCreatedAtDesc(
                        userId,
                        conversationId,
                        PageRequest.of(0, Math.max(1, Math.min(limit, RECENT_MESSAGES_LIMIT)))
                ).stream()
                .sorted((left, right) -> left.getCreatedAt().compareTo(right.getCreatedAt()))
                .toList();
    }

    private ZoneId zoneId(String timezone) {
        try {
            return ZoneId.of(timezone);
        } catch (RuntimeException exception) {
            return ZoneId.of("UTC");
        }
    }

    private UUID resolveConversationIdForChat(UUID userId, String conversationId) {
        if (conversationId == null || conversationId.isBlank()) {
            return UUID.randomUUID();
        }
        UUID parsed = parseConversationId(conversationId);
        if (!chatMessageRepository.existsByUserIdAndConversationId(userId, parsed)) {
            throw new IllegalArgumentException("conversation_id does not belong to the authenticated user");
        }
        return parsed;
    }

    private UUID resolveConversationIdForHistory(UUID userId, String conversationId) {
        if (conversationId == null || conversationId.isBlank()) {
            return chatMessageRepository.findFirstByUserIdOrderByCreatedAtDesc(userId)
                    .map(ChatMessage::getConversationId)
                    .orElse(null);
        }
        UUID parsed = parseConversationId(conversationId);
        if (!chatMessageRepository.existsByUserIdAndConversationId(userId, parsed)) {
            throw new IllegalArgumentException("conversation_id does not belong to the authenticated user");
        }
        return parsed;
    }

    private UUID parseConversationId(String conversationId) {
        try {
            return UUID.fromString(conversationId);
        } catch (RuntimeException exception) {
            throw new IllegalArgumentException("conversation_id must be a valid UUID");
        }
    }

    private List<String> safeList(List<String> values) {
        return values == null ? List.of() : values;
    }

    private String writeJson(Map<String, Object> payload) {
        try {
            return objectMapper.writeValueAsString(payload);
        } catch (Exception exception) {
            return "{}";
        }
    }

    private Map<String, Object> readJson(String payload) {
        if (payload == null || payload.isBlank()) {
            return Map.of();
        }
        try {
            return objectMapper.readValue(payload, MAP_TYPE);
        } catch (Exception exception) {
            return Map.of();
        }
    }
}
