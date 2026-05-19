# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Badhabinot is a full-stack behavioral monitoring platform with three service tiers:
- **Frontend**: React + Vite + TypeScript SPA (port 3000)
- **Backend**: Spring Boot 3.3.x / Java 21 monolith (port 8080) — auth, user, monitoring
- **Vision Service**: FastAPI + OpenCV / MediaPipe / YOLO (port 8091) — frame preprocessing, face/pose analysis
- **AI Service**: FastAPI OpenAI-compatible adapter (port 8092) — LLM behavior analysis

## Commands

### Run Everything (Docker)
```bash
cp .env.example .env   # fill in required secrets
docker compose up --build
```

### Backend (Spring Boot)
```bash
mvn -B -ntp -f backend/pom.xml verify       # build + test
mvn -B -ntp -f backend/pom.xml test         # tests only
mvn -B -ntp -f backend/pom.xml spring-boot:run  # run locally
```

### Frontend (React/Vite)
```bash
cd frontend
npm ci
npm run dev        # dev server at http://localhost:5173
npm run build      # production build
npm run typecheck  # TypeScript check without emit
```

### Python Services
```bash
cd python-services/vision-service   # or ai-service
pip install -r requirements.txt -r requirements-dev.txt
pytest tests
uvicorn app.main:app --host 0.0.0.0 --port 8091   # vision
uvicorn app.main:app --host 0.0.0.0 --port 8092   # ai
```

## Architecture

### Request Flow
```
Browser → Nginx (frontend) → Backend :8080
                                ├─ Auth (JWT, PostgreSQL: badhabinot_auth)
                                ├─ User (PostgreSQL: badhabinot_user)
                                └─ Monitoring → Vision Service :8091 → AI Service :8092
```

Backend is the sole entry point. Python services are never called directly from the frontend — only via backend HTTP integration (`backend/src/main/java/.../integration/python/`).

### Three-Database Pattern
Spring Boot connects to three PostgreSQL databases (`badhabinot_auth`, `badhabinot_user`, `badhabinot_monitoring`) as separate datasources. Redis is used as a short-lived acceleration layer (user context cache, analysis job state) — loss is non-critical, PostgreSQL is always the source of truth.

### Internal Security
Python services authenticate inbound requests with `X-Internal-Api-Key` header (value: `INTERNAL_API_KEY` env var). Public API routes use JWT bearer tokens validated by the backend's `security/` layer.

### Backend Package Layout
```
controller/      REST endpoints
service/         Business logic (auth, user, monitoring)
repository/      JPA repositories
model/           JPA entities
dto/             Request/response objects
security/        JWT filter chain
integration/     HTTP calls to Python services
infrastructure/  Cache, health checks
config/          Spring configuration
```

### Frontend Package Layout
```
src/api/         API client functions (one file per domain)
src/features/    Feature-scoped components (e.g. dashboard/)
src/pages/       Route-level page components
src/store/       Zustand state slices
src/types/       Shared TypeScript types
src/theme/       MUI theme config
```

## Key Environment Variables

See `.env.example` for the full list. Required at startup:

| Variable | Purpose |
|---|---|
| `POSTGRES_PASSWORD` | PostgreSQL password |
| `SECURITY_JWT_SECRET` | JWT signing key |
| `INTERNAL_API_KEY` | Backend → Python service auth |
| `AI_API_KEY` | LLM provider API key |
| `AI_API_BASE_URL` | OpenAI-compatible endpoint |

Frontend dev proxy target: `VITE_DEV_PROXY_TARGET=http://localhost:8080`

## Git Branching

- `master` — production
- `develop` — integration branch; PRs target here
- Feature branches: `feature/<name>`, hotfixes: `hotfix/<name>`

See `/docs/workflows/git-dallanma-stratejisi.md` for full strategy (Turkish).

## Architecture Docs

Deeper design rationale lives in `/docs/architecture/`:
- `badhabinot-architecture-blueprint.md` — full system design
- `service-communication.md` — inter-service request flows
- `redis-architecture.md` — cache patterns, TTL config, invalidation rules
