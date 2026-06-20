package com.badhabinot.backend.dto.admin;

/** Admin paneli genel özet istatistikleri. */
public record AdminStats(
        long totalUsers,
        long adminCount,
        long totalSessions,
        long totalAnalyses,
        long totalReports,
        long totalEvents
) {
}
