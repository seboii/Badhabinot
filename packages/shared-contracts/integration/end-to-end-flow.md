# Example End-to-End Flow

## 1. Register a user

```http
POST /api/v1/auth/register
```

```json
{
  "email": "demo@badhabinot.local",
  "password": "ChangeMe123!",
  "display_name": "Demo User",
  "timezone": "Europe/Istanbul",
  "locale": "tr-TR"
}
```

The response returns `access_token` and `refresh_token`.

## 2. Start a monitoring session

```http
POST /api/v1/monitoring/sessions/start
Authorization: Bearer <access-token>
```

```json
{
  "client_surface": "desktop",
  "device_type": "desktop"
}
```

The response returns a `session_id`.

## 3. Send a frame for analysis

```http
POST /api/v1/monitoring/analyze
Authorization: Bearer <access-token>
```

```json
{
  "session_id": "<session-id-from-start>",
  "frame_id": "frame-0001",
  "captured_at": "2026-04-06T09:00:00Z",
  "image_base64": "<base64-image>",
  "image_content_type": "image/jpeg"
}
```

## 4. Runtime flow inside the platform

```text
client
  -> api-gateway
  -> monitoring-service
  -> user-service (/internal/users/{userId}/analysis-context)
  -> vision-service (/v1/vision/analyze)
  -> ai-service (/v1/inference/predict)
  -> vision-service
  -> monitoring-service
  -> api-gateway
  -> client
```

## 5. Failure example

If `ai-service` times out:

- `vision-service` returns `504`
- `monitoring-service` marks the analysis job as `FAILED`
- client receives:

```json
{
  "status": 504,
  "code": "vision_service_timeout",
  "message": "Timed out while waiting for vision-service"
}
```

All internal calls from Spring to `vision-service` and from `vision-service` to `ai-service` include `X-Internal-Api-Key`.

## 6. Screen refresh

After analysis, the dashboard and history screens call:

- `GET /api/v1/monitoring/dashboard`
- `GET /api/v1/monitoring/activities?limit=10`
- `GET /api/v1/monitoring/history/weekly`

## 7. Health verification

- Public gateway: `GET http://localhost:8080/actuator/health/readiness`
- Public frontend: `GET http://localhost:3000/healthz`
- Internal auth: `GET http://auth-service:8081/actuator/health/readiness`
- Internal user: `GET http://user-service:8082/actuator/health/readiness`
- Internal monitoring: `GET http://monitoring-service:8083/actuator/health/readiness`
- Internal vision: `GET http://vision-service:8091/health`
- Internal AI: `GET http://ai-service:8092/health`

## 8. Automated smoke test

With the Docker Compose stack running:

```powershell
powershell -ExecutionPolicy Bypass -File infra/docker/scripts/smoke-test.ps1
```
