# Service Communication

## External entrypoint

- Browsers call `frontend-app`.
- `frontend-app` calls `/api/*` on the same origin.
- Nginx proxies `/api/*` and `/actuator/*` to `api-gateway`.

## Gateway routing

- `/api/v1/auth/**` -> `auth-service`
- `/api/v1/users/**` -> `user-service`
- `/api/v1/monitoring/**` -> `monitoring-service`

## Internal service calls

### `auth-service` -> `user-service`

- Bootstraps user profile data after registration.
- Uses `X-Internal-Api-Key` for service authentication.

### `monitoring-service` -> `user-service`

- Retrieves analysis context needed for sensitivity, privacy mode, reminder preferences, and timezone handling.

### `monitoring-service` -> `vision-service`

- Sends frame payloads, session metadata, and resolved user settings.

### `vision-service` -> `ai-service`

- Sends extracted vision metrics for final behavior inference.

## Security model

- Browser traffic uses JWT bearer tokens through the gateway.
- Internal Java/Python service traffic uses `X-Internal-Api-Key`.
- Python services are not exposed through the public gateway.

## Persistence split

- Auth, user, and monitoring state persists to PostgreSQL.
- Redis holds cache and ephemeral orchestration state only.
