package com.badhabinot.monitoring.domain.repository;

import com.badhabinot.monitoring.domain.model.MonitoringSession;
import com.badhabinot.monitoring.domain.model.MonitoringSessionStatus;
import java.util.List;
import java.util.Optional;
import java.util.UUID;
import org.springframework.data.jpa.repository.JpaRepository;

public interface MonitoringSessionRepository extends JpaRepository<MonitoringSession, UUID> {

    Optional<MonitoringSession> findFirstByUserIdAndStatusOrderByStartedAtDesc(UUID userId, MonitoringSessionStatus status);

    List<MonitoringSession> findByUserIdOrderByStartedAtDesc(UUID userId);
}
