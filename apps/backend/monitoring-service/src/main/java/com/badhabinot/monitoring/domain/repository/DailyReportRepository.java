package com.badhabinot.monitoring.domain.repository;

import com.badhabinot.monitoring.domain.model.DailyReport;
import java.time.LocalDate;
import java.util.Optional;
import java.util.UUID;
import org.springframework.data.jpa.repository.JpaRepository;

public interface DailyReportRepository extends JpaRepository<DailyReport, UUID> {

    Optional<DailyReport> findByUserIdAndReportDate(UUID userId, LocalDate reportDate);
}
