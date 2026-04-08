package com.badhabinot.backend.repository.monitoring;

import com.badhabinot.backend.model.monitoring.HydrationLog;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.UUID;
import org.springframework.data.jpa.repository.JpaRepository;

public interface HydrationLogRepository extends JpaRepository<HydrationLog, UUID> {

    List<HydrationLog> findByUserIdAndOccurredAtBetweenOrderByOccurredAtAsc(UUID userId, Instant from, Instant to);

    Optional<HydrationLog> findFirstByUserIdOrderByOccurredAtDesc(UUID userId);
}

