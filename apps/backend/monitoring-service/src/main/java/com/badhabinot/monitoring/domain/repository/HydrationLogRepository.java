package com.badhabinot.monitoring.domain.repository;

import com.badhabinot.monitoring.domain.model.HydrationLog;
import java.time.Instant;
import java.util.List;
import java.util.UUID;
import org.springframework.data.jpa.repository.JpaRepository;

public interface HydrationLogRepository extends JpaRepository<HydrationLog, UUID> {

    List<HydrationLog> findByUserIdAndOccurredAtBetweenOrderByOccurredAtAsc(UUID userId, Instant from, Instant to);
}

