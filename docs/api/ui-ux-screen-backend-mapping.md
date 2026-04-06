# BADHABINOT UI/UX to Backend Mapping

This mapping is derived from the uploaded BADHABINOT dashboard, onboarding, mockup, history, and settings designs.

## 1. Onboarding / Camera Permission Screen

Design cues:

- welcome text
- camera permission CTA
- local processing / privacy emphasis
- medical disclaimer

Backend mapping:

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `GET /api/v1/users/me/consents`
- `PUT /api/v1/users/me/consents`
- `GET /api/v1/users/me/settings`
- `POST /api/v1/monitoring/sessions/start`

Primary DTOs:

- `RegisterRequest`
- `LoginRequest`
- `ConsentResponse`
- `UpdateConsentsRequest`
- `SettingsResponse`
- `SessionStartRequest`
- `SessionStartResponse`

Workflow:

1. User authenticates.
2. UI loads consents and settings.
3. User accepts privacy and camera-related consents.
4. UI starts a monitoring session before live analysis begins.

Domain actions:

- create identity
- record consent state
- initialize live monitoring session

## 2. Dashboard / Live Monitoring Screen

Design cues:

- active monitoring badge
- camera preview
- model mode local/api
- streak
- water goal progress
- recent activities
- privacy mode info

Backend mapping:

- `GET /api/v1/monitoring/dashboard`
- `GET /api/v1/monitoring/activities?limit=...`
- `POST /api/v1/monitoring/analyze`
- `POST /api/v1/monitoring/hydration/log`
- `POST /api/v1/monitoring/reminders/trigger`
- `POST /api/v1/monitoring/sessions/{sessionId}/stop`

Primary DTOs:

- `DashboardResponse`
- `ActivityItemResponse`
- `AnalyzeFrameRequest`
- `AnalyzeFrameResponse`
- `HydrationLogRequest`
- `HydrationLogResponse`
- `ReminderTriggerRequest`
- `SessionStopResponse`

Workflow:

1. UI loads dashboard aggregate payload.
2. Edge client sends frame analysis requests while monitoring is active.
3. Successful detections are persisted as activity feed items.
4. Manual water intake and reminder events update the same feed.
5. UI refreshes recent activity and water progress from the dashboard endpoint.

Domain actions:

- orchestrate frame analysis
- create alert activities
- create reminder activities
- log hydration progress
- stop monitoring session

## 3. History / Weekly Trend Screen

Design cues:

- weekly trend chart
- daily or time-stamped event list
- alert history

Backend mapping:

- `GET /api/v1/monitoring/history/weekly?from=YYYY-MM-DD`
- `GET /api/v1/monitoring/activities?limit=...`

Primary DTOs:

- `WeeklyTrendResponse`
- `WeeklyTrendPointResponse`
- `ActivityItemResponse`

Workflow:

1. UI requests weekly summary points.
2. UI separately requests recent activities for the detailed list.
3. Chart and list are rendered from monitoring-service aggregates.

Domain actions:

- aggregate alerts/reminders/hydration by day
- fetch recent timeline entries

## 4. Settings Screen

Design cues:

- sensitivity
- water reminder interval
- exercise or break interval
- quiet hours
- model mode local/api
- logout

Backend mapping:

- `GET /api/v1/users/me/settings`
- `PUT /api/v1/users/me/settings`
- `GET /api/v1/users/me/consents`
- `PUT /api/v1/users/me/consents`
- `POST /api/v1/auth/logout`

Primary DTOs:

- `SettingsResponse`
- `UpdateSettingsRequest`
- `ConsentResponse`
- `UpdateConsentsRequest`
- `LogoutRequest`

Workflow:

1. UI loads persisted settings and consent state.
2. User updates detection and reminder preferences.
3. If API mode is selected, UI can require remote inference consent.
4. Logout revokes the refresh token.

Domain actions:

- update user preferences
- update privacy consent
- revoke login session

## 5. Mobile Summary / Sidebar Navigation

Design cues:

- same dashboard data model on mobile
- sidebar links to dashboard, analysis/history, settings, logout

Backend mapping:

- same endpoints as dashboard, history, settings, and logout

No separate domain model is needed. The mobile screen consumes the same DTOs as web/desktop summary views.

