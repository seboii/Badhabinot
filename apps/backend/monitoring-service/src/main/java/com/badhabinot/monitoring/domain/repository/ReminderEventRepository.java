package com.badhabinot.monitoring.domain.repository;

import com.badhabinot.monitoring.domain.model.ReminderEvent;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.UUID;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;

public interface ReminderEventRepository extends JpaRepository<ReminderEvent, UUID> {

    List<ReminderEvent> findByUserIdAndOccurredAtBetweenOrderByOccurredAtAsc(UUID userId, Instant from, Instant to);

    List<ReminderEvent> findByUserIdOrderByOccurredAtDesc(UUID userId, Pageable pageable);

    Optional<ReminderEvent> findFirstByUserIdAndReminderTypeOrderByOccurredAtDesc(UUID userId, String reminderType);
}
