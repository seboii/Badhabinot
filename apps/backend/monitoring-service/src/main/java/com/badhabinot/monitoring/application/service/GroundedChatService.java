package com.badhabinot.monitoring.application.service;

import com.badhabinot.monitoring.application.dto.AiChatRequest;
import com.badhabinot.monitoring.application.dto.AiChatResponse;
import com.badhabinot.monitoring.application.dto.ChatMessageResponse;
import com.badhabinot.monitoring.application.dto.ChatRequest;
import com.badhabinot.monitoring.application.dto.ChatResponse;
import com.badhabinot.monitoring.application.dto.DailyReportResponse;
import com.badhabinot.monitoring.application.dto.InternalUserAnalysisContext;
import com.badhabinot.monitoring.domain.model.ChatMessage;
import com.badhabinot.monitoring.domain.repository.ChatMessageRepository;
import com.badhabinot.monitoring.infrastructure.client.AiChatClient;
import com.badhabinot.monitoring.infrastructure.client.UserContextClient;
import java.time.LocalDate;
import java.time.ZoneId;
import java.util.List;
import java.util.UUID;
import org.springframework.security.oauth2.jwt.Jwt;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class GroundedChatService {

    private final ChatMessageRepository chatMessageRepository;
    private final UserContextClient userContextClient;
    private final DailyReportService dailyReportService;
    private final AiChatClient aiChatClient;

    public GroundedChatService(
            ChatMessageRepository chatMessageRepository,
            UserContextClient userContextClient,
            DailyReportService dailyReportService,
            AiChatClient aiChatClient
    ) {
        this.chatMessageRepository = chatMessageRepository;
        this.userContextClient = userContextClient;
        this.dailyReportService = dailyReportService;
        this.aiChatClient = aiChatClient;
    }

    @Transactional
    public ChatResponse chat(Jwt jwt, ChatRequest request) {
        UUID userId = UUID.fromString(jwt.getSubject());
        InternalUserAnalysisContext context = userContextClient.fetch(userId);
        LocalDate reportDate = LocalDate.now(zoneId(context.timezone()));
        DailyReportResponse report = dailyReportService.getDailyReport(userId, reportDate, context);

        UUID conversationId = parseConversationId(request.conversationId());
        if (conversationId == null) {
            conversationId = UUID.randomUUID();
        }

        ChatMessage userMessage = chatMessageRepository.save(ChatMessage.create(conversationId, userId, "user", request.message()));
        List<ChatMessage> history = chatMessageRepository.findByUserIdAndConversationIdOrderByCreatedAtAsc(userId, conversationId);
        List<AiChatRequest.Message> historyItems = history.stream()
                .limit(Math.max(0, history.size() - 1))
                .map(message -> new AiChatRequest.Message(message.getRole(), message.getContent(), message.getCreatedAt()))
                .toList();

        AiChatResponse aiResponse = aiChatClient.respond(new AiChatRequest(
                conversationId.toString(),
                userId.toString(),
                context.timezone(),
                report.reportDate(),
                request.message(),
                historyItems,
                new AiChatRequest.Context(
                        report.hydrationProgressMl(),
                        report.waterGoalMl(),
                        report.analysesCompleted(),
                        report.postureAlertCount(),
                        report.handMovementCount(),
                        report.smokingLikeCount(),
                        report.reminderCount(),
                        report.poorPostureRatio(),
                        report.summary(),
                        report.recommendations(),
                        List.of(
                                new AiChatRequest.Fact("hydration_progress_ml", String.valueOf(report.hydrationProgressMl())),
                                new AiChatRequest.Fact("water_goal_ml", String.valueOf(report.waterGoalMl())),
                                new AiChatRequest.Fact("poor_posture_ratio", String.valueOf(report.poorPostureRatio())),
                                new AiChatRequest.Fact("posture_alert_count", String.valueOf(report.postureAlertCount())),
                                new AiChatRequest.Fact("smoking_like_count", String.valueOf(report.smokingLikeCount()))
                        ),
                        report.keyBehaviorEvents().stream()
                                .map(event -> new AiChatRequest.Event(
                                        event.eventType(),
                                        event.confidence(),
                                        event.severity(),
                                        event.interpretation(),
                                        event.occurredAt(),
                                        event.evidence()
                                ))
                                .toList(),
                        report.reminders().stream()
                                .map(reminder -> new AiChatRequest.Reminder(
                                        reminder.reminderType(),
                                        reminder.message(),
                                        reminder.triggerReason(),
                                        reminder.occurredAt()
                                ))
                                .toList()
                )
        ));

        ChatMessage assistantMessage = chatMessageRepository.save(ChatMessage.create(
                conversationId,
                userId,
                "assistant",
                aiResponse.answer()
        ));

        List<ChatMessageResponse> recentMessages = chatMessageRepository.findByUserIdAndConversationIdOrderByCreatedAtAsc(userId, conversationId).stream()
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
                message.getCreatedAt()
        );
    }

    private ZoneId zoneId(String timezone) {
        try {
            return ZoneId.of(timezone);
        } catch (RuntimeException exception) {
            return ZoneId.of("UTC");
        }
    }

    private UUID parseConversationId(String conversationId) {
        if (conversationId == null || conversationId.isBlank()) {
            return null;
        }
        try {
            return UUID.fromString(conversationId);
        } catch (RuntimeException exception) {
            return null;
        }
    }
}
