package com.badhabinot.backend.service.monitoring;

import com.badhabinot.backend.dto.monitoring.ActivityItemResponse;
import com.badhabinot.backend.dto.monitoring.DashboardResponse;
import com.badhabinot.backend.dto.monitoring.HydrationLogRequest;
import com.badhabinot.backend.dto.monitoring.HydrationLogResponse;
import com.badhabinot.backend.dto.monitoring.ReminderTriggerRequest;
import com.badhabinot.backend.dto.monitoring.SessionStartRequest;
import com.badhabinot.backend.dto.monitoring.SessionStartResponse;
import com.badhabinot.backend.dto.monitoring.SessionStopResponse;
import com.badhabinot.backend.dto.monitoring.WeeklyTrendResponse;
import java.time.LocalDate;
import java.util.List;
import org.springframework.security.oauth2.jwt.Jwt;

public interface IMonitoringExperienceService {
    SessionStartResponse startSession(Jwt jwt, SessionStartRequest request);
    SessionStopResponse stopSession(Jwt jwt, String sessionId);
    DashboardResponse getDashboard(Jwt jwt);
    List<ActivityItemResponse> getRecentActivities(Jwt jwt, int page, int size);
    WeeklyTrendResponse getWeeklyTrend(Jwt jwt, LocalDate from);
    HydrationLogResponse logHydration(Jwt jwt, HydrationLogRequest request);
    ActivityItemResponse triggerReminder(Jwt jwt, ReminderTriggerRequest request);
}
