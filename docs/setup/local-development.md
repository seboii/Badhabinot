# Local Development

## Prerequisites

- Docker Desktop with Compose
- Java 21 and Maven for direct Spring development
- Python 3.11+ for direct FastAPI development
- Node.js 22+ for direct frontend development

## Recommended path

```powershell
Copy-Item .env.example .env
docker compose up --build
```

This works from the repository root because `compose.yaml` is the local entrypoint that extends the base service mesh under `infra/docker/compose/docker-compose.yml`. Docker Desktop must be running before you invoke the command.

All runtime configuration is centralized in the root `.env`. Do not create per-service `.env` files.

The local compose entrypoint publishes:

- `frontend-app` on `FRONTEND_PORT`
- `api-gateway` on `GATEWAY_PORT`
- `auth-service` on `AUTH_SERVICE_PORT`
- `user-service` on `USER_SERVICE_PORT`
- `monitoring-service` on `MONITORING_SERVICE_PORT`
- `vision-service` on `VISION_SERVICE_PORT`
- `ai-service` on `AI_SERVICE_PORT`
- PostgreSQL on `POSTGRES_PORT`
- Redis on `REDIS_PORT`

If any of those ports are already taken on your machine, change the values in `.env` before startup.

Access points after startup:

- Web UI: `http://localhost:3000`
- API Gateway: `http://localhost:8080`
- Auth service readiness: `http://localhost:8081/actuator/health/readiness`
- User service readiness: `http://localhost:8082/actuator/health/readiness`
- Monitoring service readiness: `http://localhost:8083/actuator/health/readiness`
- Vision service readiness: `http://localhost:8091/ready`
- AI service readiness: `http://localhost:8092/ready`
- Frontend health: `http://localhost:3000/healthz`
- Gateway readiness: `http://localhost:8080/actuator/health/readiness`

The default path is external API-backed AI. Ensure `.env` contains:

- `AI_PROVIDER=openai-compatible`
- `AI_API_KEY=<your key>`
- `AI_API_BASE_URL=https://api.openai.com/v1`
- `AI_MODEL_NAME=<model name>`

Optional local fallback (not production): set `AI_PROVIDER=mock`.

## Smoke test

```powershell
powershell -ExecutionPolicy Bypass -File infra/docker/scripts/smoke-test.ps1
```

## Direct service development

### Spring services

- Build all: `mvn clean package`
- Run one service: `mvn -pl apps/backend/user-service spring-boot:run`

### Python services

- AI service:
  - `cd apps/python-services/ai-service`
  - `pip install -r requirements.txt -r requirements-dev.txt`
  - `uvicorn app.main:app --host 0.0.0.0 --port 8092`
- Vision service:
  - `cd apps/python-services/vision-service`
  - `pip install -r requirements.txt -r requirements-dev.txt`
  - `uvicorn app.main:app --host 0.0.0.0 --port 8091`

### Frontend

- `cd apps/web/frontend-app`
- `npm install`
- `npm run dev`

## Environment notes

- Docker service-to-service communication uses container DNS names such as `user-service`, `monitoring-service`, `vision-service`, and `ai-service`.
- Vite reads the repository root `.env`, so frontend and Docker share the same API settings.
- Direct Spring and FastAPI runs should inherit environment values from the same root `.env`.
