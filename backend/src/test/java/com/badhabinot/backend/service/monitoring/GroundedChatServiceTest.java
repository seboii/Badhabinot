package com.badhabinot.backend.service.monitoring;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.times;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.badhabinot.backend.dto.monitoring.AiChatRequest;
import com.badhabinot.backend.dto.monitoring.AiChatResponse;
import com.badhabinot.backend.dto.monitoring.ChatRequest;
import com.badhabinot.backend.dto.monitoring.DailyReportResponse;
import com.badhabinot.backend.dto.monitoring.InternalUserAnalysisContext;
import com.badhabinot.backend.model.monitoring.ChatMessage;
import com.badhabinot.backend.repository.monitoring.ChatMessageRepository;
import com.badhabinot.backend.service.user.UserContextService;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.time.Instant;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.data.domain.Pageable;
import org.springframework.security.oauth2.jwt.Jwt;
import org.springframework.test.util.ReflectionTestUtils;

@ExtendWith(MockitoExtension.class)
class GroundedChatServiceTest {

    @Mock
    private ChatMessageRepository chatMessageRepository;

    @Mock
    private UserContextService userContextService;

    @Mock
    private DailyReportService dailyReportService;

    @Mock
    private ChatContextBuilderService chatContextBuilderService;

    @Mock
    private com.badhabinot.backend.integration.python.AiChatClient aiChatClient;

    private GroundedChatService groundedChatService;

    @BeforeEach
    void setUp() {
        groundedChatService = new GroundedChatService(
                chatMessageRepository,
                userContextService,
                dailyReportService,
                chatContextBuilderService,
                aiChatClient,
                new ObjectMapper().findAndRegisterModules()
        );
    }

    @Test
    void historyReturnsEmptyWhenUserHasNoConversation() {
        UUID userId = UUID.randomUUID();
        when(chatMessageRepository.findFirstByUserIdOrderByCreatedAtDesc(userId)).thenReturn(Optional.empty());

        var response = groundedChatService.history(jwt(userId), null, 10);

        assertThat(response.conversationId()).isNull();
        assertThat(response.recentMessages()).isEmpty();
    }

    @Test
    void chatRejectsConversationThatDoesNotBelongToUser() {
        UUID userId = UUID.randomUUID();
        UUID foreignConversationId = UUID.randomUUID();
        InternalUserAnalysisContext context = context(userId);
        DailyReportResponse report = report(LocalDate.of(2026, 4, 8));

        when(userContextService.getMonitoringAnalysisContext(userId)).thenReturn(context);
        when(dailyReportService.getDailyReport(eq(userId), any(LocalDate.class), eq(context))).thenReturn(report);
        when(chatMessageRepository.existsByUserIdAndConversationId(userId, foreignConversationId)).thenReturn(false);

        assertThatThrownBy(() -> groundedChatService.chat(
                jwt(userId),
                new ChatRequest(foreignConversationId.toString(), "Show me the trend.")
        )).isInstanceOf(IllegalArgumentException.class)
                .hasMessageContaining("does not belong");

        verify(chatMessageRepository, never()).save(any(ChatMessage.class));
    }

    @Test
    void chatPersistsUserAndAssistantMessagesWithGroundedMetadata() {
        UUID userId = UUID.randomUUID();
        InternalUserAnalysisContext context = context(userId);
        DailyReportResponse report = report(LocalDate.of(2026, 4, 8));
        AiChatRequest.Context aiContext = aiContext();
        List<ChatMessage> storedMessages = new ArrayList<>();
        AtomicInteger sequence = new AtomicInteger();

        when(userContextService.getMonitoringAnalysisContext(userId)).thenReturn(context);
        when(dailyReportService.getDailyReport(eq(userId), any(LocalDate.class), eq(context))).thenReturn(report);
        when(chatContextBuilderService.build(eq(userId), eq(context), any(LocalDate.class), eq(report))).thenReturn(aiContext);
        when(aiChatClient.respond(any(AiChatRequest.class))).thenReturn(new AiChatResponse(
                UUID.randomUUID().toString(),
                "Your posture improved in the second half of the day.",
                List.of("Hydration reached 1500 of 2500 ml."),
                List.of("Schedule one extra hydration reminder after lunch."),
                new AiChatResponse.ModelDetails("openai-compatible", "gpt-4.1-mini", "external_api")
        ));
        when(chatMessageRepository.save(any(ChatMessage.class))).thenAnswer(invocation -> {
            ChatMessage message = invocation.getArgument(0);
            ReflectionTestUtils.setField(
                    message,
                    "createdAt",
                    Instant.parse("2026-04-08T09:00:00Z").plusSeconds(sequence.getAndIncrement())
            );
            storedMessages.add(message);
            return message;
        });
        when(chatMessageRepository.findByUserIdAndConversationIdOrderByCreatedAtDesc(
                eq(userId),
                any(UUID.class),
                any(Pageable.class)
        )).thenAnswer(invocation -> {
            UUID conversationId = invocation.getArgument(1);
            return storedMessages.stream()
                    .filter(message -> message.getConversationId().equals(conversationId))
                    .sorted(Comparator.comparing(ChatMessage::getCreatedAt).reversed())
                    .toList();
        });

        var response = groundedChatService.chat(jwt(userId), new ChatRequest(null, "How did I do today?"));

        assertThat(response.answer()).contains("posture improved");
        assertThat(response.model().provider()).isEqualTo("openai-compatible");
        assertThat(response.recentMessages()).hasSize(2);
        assertThat(response.recentMessages()).extracting("role").containsExactly("user", "assistant");
        assertThat(response.recentMessages().get(1).metadata())
                .containsKey("grounded_facts")
                .containsKey("follow_up_suggestions")
                .containsKey("model");

        ArgumentCaptor<AiChatRequest> aiRequestCaptor = ArgumentCaptor.forClass(AiChatRequest.class);
        verify(aiChatClient).respond(aiRequestCaptor.capture());
        assertThat(aiRequestCaptor.getValue().history()).isEmpty();
        assertThat(aiRequestCaptor.getValue().context()).isEqualTo(aiContext);
        verify(chatMessageRepository, times(2)).save(any(ChatMessage.class));
    }

    private Jwt jwt(UUID userId) {
        Jwt jwt = org.mockito.Mockito.mock(Jwt.class);
        when(jwt.getSubject()).thenReturn(userId.toString());
        return jwt;
    }

    private InternalUserAnalysisContext context(UUID userId) {
        return new InternalUserAnalysisContext(
                userId.toString(),
                "UTC",
                "MEDIUM",
                "API",
                true,
                2500,
                60,
                45,
                true,
                false,
                "22:00",
                "08:00",
                true
        );
    }

    private DailyReportResponse report(LocalDate reportDate) {
        return new DailyReportResponse(
                UUID.randomUUID(),
                reportDate,
                18,
                5,
                3,
                1,
                4,
                1500,
                2500,
                0.32,
                "Posture and hydration need incremental improvements.",
                List.of("Add hydration checkpoints."),
                List.of(),
                List.of(),
                List.of(),
                Instant.parse("2026-04-08T18:00:00Z")
        );
    }

    private AiChatRequest.Context aiContext() {
        return new AiChatRequest.Context(
                1500,
                2500,
                18,
                5,
                3,
                1,
                4,
                0.32,
                "Posture and hydration need incremental improvements.",
                List.of("Add hydration checkpoints."),
                List.of(new AiChatRequest.Fact("posture_alert_count", "5")),
                List.of(),
                List.of(),
                List.of(),
                Map.of("poor_posture", 5),
                Map.of("water_reminder", 2),
                List.of(),
                7,
                430,
                9600,
                124,
                "Compared with 2026-04-07: posture alerts +1, hydration -200 ml, smoking-like cues +0.",
                List.of()
        );
    }
}
