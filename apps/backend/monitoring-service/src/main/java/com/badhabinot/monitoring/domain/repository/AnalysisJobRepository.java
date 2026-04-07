package com.badhabinot.monitoring.domain.repository;

import com.badhabinot.monitoring.domain.model.AnalysisJob;
import java.time.Instant;
import java.util.List;
import java.util.UUID;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.domain.Pageable;

public interface AnalysisJobRepository extends JpaRepository<AnalysisJob, UUID> {
    Optional<AnalysisJob> findByIdAndUserId(UUID id, UUID userId);

    List<AnalysisJob> findByUserIdAndCreatedAtBetweenOrderByCreatedAtAsc(UUID userId, Instant from, Instant to);

    List<AnalysisJob> findByUserIdOrderByCreatedAtDesc(UUID userId, Pageable pageable);
}
