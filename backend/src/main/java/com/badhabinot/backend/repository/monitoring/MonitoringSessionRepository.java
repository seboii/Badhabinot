package com.badhabinot.backend.repository.monitoring;

import com.badhabinot.backend.model.monitoring.MonitoringSession;
import com.badhabinot.backend.model.monitoring.MonitoringSessionStatus;
import java.util.List;
import java.util.Optional;
import java.util.UUID;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;

public interface MonitoringSessionRepository extends JpaRepository<MonitoringSession, UUID> {

    Optional<MonitoringSession> findFirstByUserIdAndStatusOrderByStartedAtDesc(UUID userId, MonitoringSessionStatus status);

    Optional<MonitoringSession> findByIdAndUserId(UUID id, UUID userId);

    List<MonitoringSession> findByUserIdOrderByStartedAtDesc(UUID userId);

    List<MonitoringSession> findByUserIdOrderByStartedAtDesc(UUID userId, Pageable pageable);
}

