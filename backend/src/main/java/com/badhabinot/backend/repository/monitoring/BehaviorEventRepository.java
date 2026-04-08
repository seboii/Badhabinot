package com.badhabinot.backend.repository.monitoring;

import com.badhabinot.backend.model.monitoring.BehaviorEvent;
import java.time.Instant;
import java.util.List;
import java.util.UUID;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;

public interface BehaviorEventRepository extends JpaRepository<BehaviorEvent, UUID> {

    List<BehaviorEvent> findByUserIdAndOccurredAtBetweenOrderByOccurredAtAsc(UUID userId, Instant from, Instant to);

    List<BehaviorEvent> findByUserIdOrderByOccurredAtDesc(UUID userId, Pageable pageable);
}

