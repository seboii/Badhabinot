# Spring <-> Python Integration Contracts

## Overview

The integration flow is:

1. Client calls `monitoring-service`
2. `monitoring-service` fetches analysis context from `user-service`
3. `monitoring-service` sends the frame payload to `vision-service`
4. `vision-service` preprocesses the image and calls `ai-service`
5. `ai-service` returns behavior inference
6. `vision-service` returns a combined result to `monitoring-service`
7. `monitoring-service` persists the outcome and returns the final response

## Public Spring endpoint

### `POST /api/v1/monitoring/sessions/start`

Request:

```json
{
  "client_surface": "desktop",
  "device_type": "desktop"
}
```

Response:

```json
{
  "session_id": "3aa3ea2f-f4ef-4f7f-813a-c31f1a2113d2",
  "status": "ACTIVE",
  "started_at": "2026-04-06T09:00:00Z"
}
```

### `POST /api/v1/monitoring/analyze`

Request:

```json
{
  "session_id": "session-2026-04-06-01",
  "frame_id": "frame-0001",
  "captured_at": "2026-04-06T09:00:00Z",
  "image_base64": "<base64-image>",
  "image_content_type": "image/jpeg"
}
```

Response:

```json
{
  "analysis_id": "2f1f3b89-2ec0-4f93-9fe1-8cc58d6209ec",
  "session_id": "3aa3ea2f-f4ef-4f7f-813a-c31f1a2113d2",
  "frame_id": "frame-0001",
  "subject_present": true,
  "posture_state": "poor",
  "behavior_type": "nail_biting",
  "confidence": 0.7361,
  "processed_at": "2026-04-06T09:00:00Z",
  "processing": {
    "frame_width": 1280,
    "frame_height": 720,
    "brightness_mean": 117.62,
    "edge_density": 0.1941,
    "vision_latency_ms": 93,
    "ai_latency_ms": 14,
    "scores": {
      "nail_biting": 0.7361,
      "smoking": 0.2912
    }
  }
}
```

### `GET /api/v1/monitoring/dashboard`

Response:

```json
{
  "monitoring_active": true,
  "active_session_id": "3aa3ea2f-f4ef-4f7f-813a-c31f1a2113d2",
  "model_mode": "LOCAL",
  "privacy_mode": "LOCAL_ONLY",
  "streak_days": 3,
  "alert_count_today": 4,
  "reminder_count_today": 1,
  "water_progress_ml": 750,
  "water_goal_ml": 2500,
  "latest_activity": {
    "id": "a9c09b89-2ec0-4f93-9fe1-8cc58d6209ec",
    "activity_type": "poor_posture",
    "category": "ALERT",
    "title": "Kotu Durus Tespit Edildi",
    "message": "Durus bozuklugu icin uyari gosterildi.",
    "confidence": 0.81,
    "occurred_at": "2026-04-06T09:05:10Z"
  },
  "recent_activities": [],
  "generated_at": "2026-04-06T09:05:11Z"
}
```

### `GET /api/v1/monitoring/history/weekly?from=2026-04-01`

Response:

```json
{
  "from": "2026-04-01",
  "to": "2026-04-07",
  "points": [
    { "day": "2026-04-01", "alert_count": 2, "reminder_count": 1, "hydration_count": 1 }
  ]
}
```

### `POST /api/v1/monitoring/hydration/log`

Request:

```json
{
  "amount_ml": 250,
  "source": "manual",
  "session_id": "3aa3ea2f-f4ef-4f7f-813a-c31f1a2113d2"
}
```

### `POST /api/v1/monitoring/reminders/trigger`

Request:

```json
{
  "reminder_type": "water_reminder",
  "message": "Su molasi zamani.",
  "session_id": "3aa3ea2f-f4ef-4f7f-813a-c31f1a2113d2"
}
```

## Spring -> User internal contract

### `GET /internal/users/{userId}/analysis-context`

Response:

```json
{
  "user_id": "5fa06206-e0ff-4552-80fe-a41dc4ea45ef",
  "timezone": "Europe/Istanbul",
  "sensitivity": "MEDIUM",
  "model_mode": "LOCAL",
  "water_goal_ml": 2500,
  "notifications_enabled": true,
  "quiet_hours_enabled": false,
  "quiet_hours_start": "22:00",
  "quiet_hours_end": "08:00",
  "remote_inference_accepted": false
}
```

Headers:

- `X-Internal-Api-Key: <internal-api-key>`

## Spring -> Vision contract

### `POST /v1/vision/analyze`

Request:

```json
{
  "request_id": "2f1f3b89-2ec0-4f93-9fe1-8cc58d6209ec",
  "user_id": "5fa06206-e0ff-4552-80fe-a41dc4ea45ef",
  "session_id": "session-2026-04-06-01",
  "frame_id": "frame-0001",
  "captured_at": "2026-04-06T09:00:00Z",
  "image_base64": "<base64-image>",
  "image_content_type": "image/jpeg",
  "settings": {
    "sensitivity": "MEDIUM",
    "model_mode": "LOCAL",
    "remote_inference_accepted": false
  }
}
```

Response:

```json
{
  "request_id": "2f1f3b89-2ec0-4f93-9fe1-8cc58d6209ec",
  "subject_present": true,
  "posture_state": "poor",
  "inference": {
    "behavior_type": "nail_biting",
    "confidence": 0.7361,
    "scores": {
      "nail_biting": 0.7361,
      "smoking": 0.2912
    }
  },
  "processing": {
    "frame_width": 1280,
    "frame_height": 720,
    "brightness_mean": 117.62,
    "edge_density": 0.1941,
    "vision_latency_ms": 93,
    "ai_latency_ms": 14
  }
}
```

Headers:

- `X-Internal-Api-Key: <internal-api-key>`

## Vision -> AI contract

### `POST /v1/inference/predict`

Request:

```json
{
  "request_id": "2f1f3b89-2ec0-4f93-9fe1-8cc58d6209ec",
  "user_id": "5fa06206-e0ff-4552-80fe-a41dc4ea45ef",
  "session_id": "session-2026-04-06-01",
  "frame_id": "frame-0001",
  "captured_at": "2026-04-06T09:00:00Z",
  "metrics": {
    "brightness_mean": 117.62,
    "edge_density": 0.1941,
    "center_edge_density": 0.3014,
    "posture_risk_score": 0.6622,
    "hand_face_proximity_score": 0.7127,
    "elongated_object_score": 0.2912
  },
  "settings": {
    "sensitivity": "MEDIUM",
    "model_mode": "LOCAL",
    "remote_inference_accepted": false
  }
}
```

Response:

```json
{
  "request_id": "2f1f3b89-2ec0-4f93-9fe1-8cc58d6209ec",
  "behavior_type": "nail_biting",
  "confidence": 0.7361,
  "scores": {
    "nail_biting": 0.7361,
    "smoking": 0.2912
  },
  "model": {
    "name": "heuristic-behavior-classifier",
    "version": "phase-2.1",
    "mode": "local"
  }
}
```

Headers:

- `X-Internal-Api-Key: <internal-api-key>`

## Timeout and error policy

- `monitoring-service` -> `user-service`
  - connect timeout: 2s
  - read timeout: 5s
  - timeout result: `504 user_service_timeout`

- `monitoring-service` -> `vision-service`
  - connect timeout: 2s
  - read timeout: 8s
  - timeout result: `504 vision_service_timeout`

- `vision-service` -> `ai-service`
  - timeout: 5s
  - timeout result: HTTP `504 ai-service timeout`

- Downstream 4xx/5xx responses are normalized to `502` on the caller side.

## Health checks

- `GET /actuator/health/readiness` on all Spring services
- `GET /health` on `vision-service`
- `GET /health` on `ai-service`
- `monitoring-service` contributes a `pythonServices` health indicator that checks both Python services
