package com.badhabinot.monitoring.application.service;

import com.badhabinot.monitoring.application.dto.AiChatRequest;
import com.badhabinot.monitoring.application.dto.AiChatResponse;
import com.badhabinot.monitoring.application.dto.ChatHistoryResponse;
import com.badhabinot.monitoring.application.dto.ChatMessageResponse;
import com.badhabinot.monitoring.application.dto.ChatRequest;
import com.badhabinot.monitoring.application.dto.ChatResponse;
import com.badhabinot.monitoring.application.dto.DailyReportResponse;
import com.badhabinot.monitoring.application.dto.InternalUserAnalysisContext;
import com.badhabinot.monitoring.domain.model.ChatMessage;
import com.badhabinot.monitoring.domain.repository.ChatMessageRepository;
import com.badhabinot.monitoring.infrastructure.client.AiChatClient;
import com.badhabinot.monitoring.infrastructure.client.UserContextClient;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.time.LocalDate;
import java.time.ZoneId;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import org.springframework.data.domain.PageRequest;
import org.springframework.security.oauth2.jwt.Jwt;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class GroundedChatService {

    private static final TypeReference<Map<String, Object>> MAP_TYPE = new TypeReference<>() {
    };
    private static final int AI_HISTORY_LIMIT = 12;
    private static final int RECENT_MESSAGES_LIMIT = 50;

    private final ChatMessageRepository chatMessageRepository;
    private final UserContextClient userContextClient;
    private final DailyReportService dailyReportService;
    private final ChatContextBuilderService chatContextBuilderService;
    private final AiChatClient aiChatClient;
    private final ObjectMapper objectMapper;

    public GroundedChatService(
            ChatMessageRepository chatMessageRepository,
            UserContextClient userContextClient,
            DailyReportService dailyReportService,
            ChatContextBuilderService chatContextBuilderService,
            AiChatClient aiChatClient,
            ObjectMapper objectMapper
    ) {
        this.chatMessageRepository = chatMessageRepository;
        this.userContextClient = userContextClient;
        this.dailyReportService = dailyReportService;
        this.chatContextBuilderService = chatContextBuilderService;
        this.aiChatClient = aiChatClient;
        this.objectMapper = objectMapper;
    }

    @Transactional(readOnly = true)
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

    @Transactional
    public ChatResponse chat(Jwt jwt, ChatRequest request) {
        UUID userId = UUID.fromString(jwt.getSubject());
        InternalUserAnalysisContext context = userContextClient.fetch(userId);
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
                aiContext
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
