package com.badhabinot.monitoring.domain.repository;

import com.badhabinot.monitoring.domain.model.DailyReport;
import java.time.LocalDate;
import java.util.List;
import java.util.Optional;
import java.util.UUID;
import org.springframework.data.jpa.repository.JpaRepository;

public interface DailyReportRepository extends JpaRepository<DailyReport, UUID> {

    Optional<DailyReport> findByUserIdAndReportDate(UUID userId, LocalDate reportDate);

    List<DailyReport> findByUserIdAndReportDateBetweenOrderByReportDateDesc(UUID userId, LocalDate from, LocalDate to);

    Optional<DailyReport> findFirstByUserIdAndReportDateBeforeOrderByReportDateDesc(UUID userId, LocalDate reportDate);
}
