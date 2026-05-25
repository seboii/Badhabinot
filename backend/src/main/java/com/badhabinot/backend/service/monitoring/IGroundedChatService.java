package com.badhabinot.backend.service.monitoring;

import com.badhabinot.backend.dto.monitoring.ChatHistoryResponse;
import com.badhabinot.backend.dto.monitoring.ChatRequest;
import com.badhabinot.backend.dto.monitoring.ChatResponse;
import org.springframework.security.oauth2.jwt.Jwt;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

public interface IGroundedChatService {
    ChatHistoryResponse history(Jwt jwt, String conversationId, int limit);
    ChatResponse chat(Jwt jwt, ChatRequest request);
    SseEmitter chatStream(Jwt jwt, ChatRequest request);
}
