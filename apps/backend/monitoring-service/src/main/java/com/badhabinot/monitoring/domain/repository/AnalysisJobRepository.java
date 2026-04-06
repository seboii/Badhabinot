package com.badhabinot.monitoring.domain.repository;

import com.badhabinot.monitoring.domain.model.AnalysisJob;
import java.util.UUID;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;

public interface AnalysisJobRepository extends JpaRepository<AnalysisJob, UUID> {
    Optional<AnalysisJob> findByIdAndUserId(UUID id, UUID userId);
}
