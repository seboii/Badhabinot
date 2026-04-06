# Service Catalog

## Public APIs

### `api-gateway`

- Swagger: `http://localhost:8080/swagger-ui.html`
- Health: `http://localhost:8080/actuator/health/readiness`

### `auth-service`

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh`
- `POST /api/v1/auth/logout`
- `GET /api/v1/auth/me`

### `user-service`

- `GET /api/v1/users/me`
- `PUT /api/v1/users/me`
- `GET /api/v1/users/me/settings`
- `PUT /api/v1/users/me/settings`
- `GET /api/v1/users/me/consents`
- `PUT /api/v1/users/me/consents`

### `monitoring-service`

- `POST /api/v1/monitoring/sessions/start`
- `POST /api/v1/monitoring/sessions/{sessionId}/stop`
- `POST /api/v1/monitoring/analyze`
- `GET /api/v1/monitoring/jobs/{analysisId}`
- `GET /api/v1/monitoring/dashboard`
- `GET /api/v1/monitoring/activities`
- `GET /api/v1/monitoring/history/weekly`
- `POST /api/v1/monitoring/hydration/log`
- `POST /api/v1/monitoring/reminders/trigger`

## Internal APIs

### `user-service`

- `POST /internal/users/bootstrap`
- `GET /internal/users/{userId}/analysis-context`

### `vision-service`

- `POST /v1/vision/analyze`

### `ai-service`

- `POST /v1/inference/predict`
