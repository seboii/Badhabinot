# Local Development

## Prerequisites

- Docker Desktop with Compose
- Java 21 and Maven for direct Spring development
- Python 3.11+ for direct FastAPI development
- Node.js 22+ for direct frontend development

## Recommended path

```powershell
Copy-Item .env.example .env
docker compose `
  -f infra/docker/compose/docker-compose.yml `
  -f infra/docker/compose/docker-compose.dev.yml `
  --env-file .env `
  up --build
```

The base file keeps Spring and Python services internal to the Docker network. The dev override publishes only:

- `frontend-app` on `FRONTEND_PORT`
- `api-gateway` on `GATEWAY_PORT`
- PostgreSQL on `POSTGRES_PORT`
- Redis on `REDIS_PORT`

If any of those ports are already taken on your machine, change the values in `.env` before startup.

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
- `Copy-Item .env.example .env`
- `npm install`
- `npm run dev`

## Environment notes

- Docker service-to-service communication uses container DNS names such as `user-service`, `monitoring-service`, `vision-service`, and `ai-service`.
- Direct local development defaults to `localhost` values from each service configuration.
