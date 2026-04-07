# BADHABINOT Platform Monorepo

BADHABINOT is organized as a production-style monorepo with clear boundaries between Spring Boot backend services, Python AI/CV microservices, the standalone web application, and shared infrastructure.

## Repository layout

```text
apps/
  backend/
    api-gateway/
    auth-service/
    monitoring-service/
    user-service/
  python-services/
    ai-service/
    vision-service/
  web/
    frontend-app/
packages/
  shared-config/
  shared-contracts/
  shared-docs/
infra/
  db/
    postgres/
      init/
  docker/
    compose/
    dockerfiles/
    scripts/
  monitoring/
  nginx/
  redis/
docs/
  api/
  architecture/
  decisions/
  setup/
.env.example
pom.xml
```

## Service boundaries

### Backend

- `api-gateway`: public edge entrypoint, JWT validation, route forwarding.
- `auth-service`: registration, login, refresh rotation, logout, session token lifecycle.
- `user-service`: profile, settings, consent state, internal bootstrap and analysis context APIs.
- `monitoring-service`: monitoring domain orchestration, dashboard/history APIs, Spring-to-Python coordination, short-lived analysis job state.

### Python microservices

- `ai-service`: external AI provider adapter that normalizes higher-level analysis into a stable JSON contract.
- `vision-service`: OpenCV preprocessing and feature extraction that stays local and returns structured machine signals.

### Web

- `frontend-app`: React + TypeScript SPA with auth flows, onboarding, dashboard, history, settings, and persistent light/dark theme support.

## Redis architecture

Redis is used as a supporting runtime store, not a source of truth.

- `user-service` caches `user-context`, `user-settings`, `user-consents`, and `analysis-context` responses with a short TTL.
- `monitoring-service` stores short-lived analysis job state keyed by analysis ID so Spring-to-Python orchestration state can be queried without hitting PostgreSQL for every poll.
- PostgreSQL remains the system of record for auth, user, and monitoring data.
- If Redis is unavailable, the platform degrades gracefully:
  - `user-service` falls back to direct database reads and logs cache errors.
  - `monitoring-service` continues processing and falls back to persisted job summaries.

More detail: `docs/architecture/redis-architecture.md`

## Docker and local runtime

The repository now exposes a root-level `compose.yaml`, so the full platform including the web UI can be started from the repository root with a single Docker Compose command:

```powershell
Copy-Item .env.example .env
docker compose up --build
```

Docker Desktop must be running before you start the stack.

Published host endpoints after `docker compose up --build`:

- Frontend UI: `http://localhost:3000`
- API Gateway: `http://localhost:8080`
- Auth service: `http://localhost:8081`
- User service: `http://localhost:8082`
- Monitoring service: `http://localhost:8083`
- Vision service: `http://localhost:8091`
- AI service: `http://localhost:8092`
- PostgreSQL: `localhost:5432`
- Redis: `localhost:6379`

Containers communicate internally by service DNS name:

- `auth-service:8081`
- `user-service:8082`
- `monitoring-service:8083`
- `vision-service:8091`
- `ai-service:8092`

Local AI configuration defaults to `AI_PROVIDER=mock` so a first boot works without external credentials. To run real API-backed analysis, set:

- `AI_PROVIDER=openai-compatible`
- `AI_API_KEY=<your provider key>`
- `AI_API_BASE_URL=https://api.openai.com/v1`
- `AI_MODEL_NAME=<provider model>`

Browser-facing routing:

- Open `http://localhost:3000` for the web UI.
- The frontend is served by Nginx and proxies `/api/*` plus `/actuator/*` to `api-gateway:8080` on the Docker network.
- The browser never needs container hostnames; it talks to `localhost:3000`, and Nginx forwards backend traffic internally.

Public health endpoints:

- `http://localhost:8080/actuator/health/readiness`
- `http://localhost:3000/healthz`
- `http://localhost:8081/actuator/health/readiness`
- `http://localhost:8082/actuator/health/readiness`
- `http://localhost:8083/actuator/health/readiness`
- `http://localhost:8091/ready`
- `http://localhost:8092/ready`

If those host ports are already in use, override `GATEWAY_PORT`, `FRONTEND_PORT`, `POSTGRES_PORT`, and `REDIS_PORT` in `.env` before starting the stack.

Run the smoke test after the stack is healthy:

```powershell
powershell -ExecutionPolicy Bypass -File infra/docker/scripts/smoke-test.ps1
```

## Local development without Docker

### Backend

```powershell
mvn clean package
```

Run a single Spring service:

```powershell
mvn -pl apps/backend/monitoring-service spring-boot:run
```

### Python services

`ai-service`

```powershell
cd apps/python-services/ai-service
python -m venv .venv
. .venv\\Scripts\\Activate.ps1
pip install -r requirements.txt -r requirements-dev.txt
uvicorn app.main:app --host 0.0.0.0 --port 8092
```

`vision-service`

```powershell
cd apps/python-services/vision-service
python -m venv .venv
. .venv\\Scripts\\Activate.ps1
pip install -r requirements.txt -r requirements-dev.txt
uvicorn app.main:app --host 0.0.0.0 --port 8091
```

### Frontend

```powershell
cd apps/web/frontend-app
Copy-Item .env.example .env
npm install
npm run dev
```

The Vite app runs on `http://localhost:5173` and proxies `/api` and `/actuator` to the gateway by default.

## Build validation commands

- Backend: `mvn clean package`
- Frontend: `cd apps/web/frontend-app && npm run build`
- Python AI tests: `cd apps/python-services/ai-service && pytest`
- Python Vision tests: `cd apps/python-services/vision-service && pytest`

## Key documentation

- Architecture blueprint: `docs/architecture/badhabinot-architecture-blueprint.md`
- Service communication: `docs/architecture/service-communication.md`
- Redis strategy: `docs/architecture/redis-architecture.md`
- Local setup: `docs/setup/local-development.md`
- API catalog: `docs/api/service-catalog.md`
- Monorepo decision record: `docs/decisions/0001-monorepo-structure.md`
- Contracts: `packages/shared-contracts/`

## Shared packages

- `packages/shared-config`: environment fragments and shared runtime configuration guidance.
- `packages/shared-contracts`: integration and OpenAPI-facing contracts.
- `packages/shared-docs`: shared operational and topology notes used across services.
