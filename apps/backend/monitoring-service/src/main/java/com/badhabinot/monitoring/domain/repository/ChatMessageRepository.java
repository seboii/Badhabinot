package com.badhabinot.monitoring.domain.repository;

import com.badhabinot.monitoring.domain.model.ChatMessage;
import java.util.List;
import java.util.Optional;
import java.util.UUID;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;

public interface ChatMessageRepository extends JpaRepository<ChatMessage, UUID> {

    List<ChatMessage> findByUserIdAndConversationIdOrderByCreatedAtAsc(UUID userId, UUID conversationId);

    List<ChatMessage> findByUserIdAndConversationIdOrderByCreatedAtDesc(UUID userId, UUID conversationId, Pageable pageable);

    List<ChatMessage> findByUserIdOrderByCreatedAtDesc(UUID userId, Pageable pageable);

    Optional<ChatMessage> findFirstByUserIdOrderByCreatedAtDesc(UUID userId);

    boolean existsByUserIdAndConversationId(UUID userId, UUID conversationId);
}
