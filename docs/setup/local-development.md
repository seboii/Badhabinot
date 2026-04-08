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

This works from the repository root because `compose.yaml` extends the base runtime file under `infra/docker/compose/docker-compose.yml`.

All runtime configuration is centralized in the root `.env`. Do not create per-service `.env` files.

The local compose entrypoint publishes:

- `frontend-app` on `FRONTEND_PORT`
- `backend` on `BACKEND_PORT`
- `vision-service` on `VISION_SERVICE_PORT`
- `ai-service` on `AI_SERVICE_PORT`
- PostgreSQL on `POSTGRES_PORT`
- Redis on `REDIS_PORT`

Access points after startup:

- Web UI: `http://localhost:3000`
- Backend API: `http://localhost:8080`
- Backend readiness: `http://localhost:8080/actuator/health/readiness`
- Vision service readiness: `http://localhost:8091/ready`
- AI service readiness: `http://localhost:8092/ready`
- Frontend health: `http://localhost:3000/healthz`

## Smoke test

```powershell
powershell -ExecutionPolicy Bypass -File infra/docker/scripts/smoke-test.ps1 -GatewayBaseUrl http://localhost:8080
```

## Direct development

### Spring backend

- Build and test: `mvn -B -ntp -f backend/pom.xml verify`
- Run locally: `mvn -f backend/pom.xml spring-boot:run`

### Python services

- AI service:
  - `cd python-services/ai-service`
  - `pip install -r requirements.txt -r requirements-dev.txt`
  - `pytest tests`
  - `uvicorn app.main:app --host 0.0.0.0 --port 8092`
- Vision service:
  - `cd python-services/vision-service`
  - `pip install -r requirements.txt -r requirements-dev.txt`
  - `pytest tests`
  - `uvicorn app.main:app --host 0.0.0.0 --port 8091`

### Frontend

- `cd frontend`
- `npm install`
- `npm run dev`

## Environment notes

- Docker service-to-service communication uses container DNS names such as `backend`, `vision-service`, and `ai-service`.
- Vite reads the repository root `.env`, so frontend and Docker share the same API settings.
- Direct Spring and FastAPI runs should inherit environment values from the same root `.env`.
