package com.badhabinot.monitoring.domain.repository;

import com.badhabinot.monitoring.domain.model.ChatMessage;
import java.util.List;
import java.util.UUID;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;

public interface ChatMessageRepository extends JpaRepository<ChatMessage, UUID> {

    List<ChatMessage> findByUserIdAndConversationIdOrderByCreatedAtAsc(UUID userId, UUID conversationId);

    List<ChatMessage> findByUserIdOrderByCreatedAtDesc(UUID userId, Pageable pageable);
}
