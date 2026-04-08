# Service Communication

## External entrypoint

- Browsers call `frontend-app`.
- `frontend-app` calls `/api/*` and `/actuator/*` on the same origin.
- Nginx proxies those paths to the single Spring Boot `backend` service.

## Backend responsibility split

- `/api/v1/auth/**` is handled inside the backend auth controller/service/repository flow.
- `/api/v1/users/**` is handled inside the backend user controller/service/repository flow.
- `/api/v1/monitoring/**` is handled inside the backend monitoring controller/service/repository flow.
- `/internal/users/**` remains available for internal-only flows protected by `X-Internal-Api-Key`.

## Internal integrations

- Auth registration bootstraps user profile state through direct Java service collaboration inside the same application.
- Monitoring reads user analysis context through direct Java service collaboration inside the same application.
- Monitoring calls `vision-service` over HTTP.
- `vision-service` calls `ai-service` over HTTP for higher-level inference.

## Security model

- Browser traffic uses JWT bearer tokens validated by the unified backend.
- Internal-only endpoints use `X-Internal-Api-Key`.
- Python services are not exposed through the public Nginx entrypoint.

## Persistence split

- The backend keeps three PostgreSQL databases for auth, user, and monitoring persistence compatibility.
- Redis still holds user cache entries and short-lived monitoring job state.
