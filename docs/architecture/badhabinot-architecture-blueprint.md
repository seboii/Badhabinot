# BADHABINOT Architecture Blueprint

## Objectives

- Keep Java business logic in one maintainable Spring Boot backend.
- Keep Python AI/CV workloads isolated behind HTTP integrations.
- Keep the frontend standalone and environment-driven.
- Use Redis for short-lived acceleration and orchestration support, never as the primary database.

## Runtime topology

```text
frontend-app
  -> backend
        -> auth persistence (PostgreSQL)
        -> user persistence (PostgreSQL)
        -> monitoring persistence (PostgreSQL)
        -> Redis
        -> vision-service
              -> ai-service
```

## Monorepo boundaries

### `backend/src/main/java/com/badhabinot/backend`

- Unified Spring Boot backend.
- Uses controller, service, repository, model, dto, config, exception, and integration package groupings.
- Monitoring orchestration stays inside the backend service layer while Python calls remain isolated under `integration`.

### `python-services`

- FastAPI microservices only.
- `vision-service` owns image decoding, OpenCV analysis, and inference request preparation.
- `ai-service` owns behavior classification and model metadata responses.

### `frontend`

- SPA-only codebase.
- API integration is isolated behind `src/api`.
- Theme behavior is isolated behind `src/theme`.

### `packages`

- Shared non-runtime assets only.
- Contracts, config fragments, and shared docs live here.

### `infra`

- Docker Compose, generic Dockerfiles, operational scripts, nginx config, Redis config, and database bootstrap assets.

## Data stores

### PostgreSQL

- Source of truth for auth, user, monitoring sessions, activity feeds, hydration logs, chat history, and persisted analysis jobs.
- The unified backend keeps separate auth, user, and monitoring databases for migration compatibility.

### Redis

- Cache layer for repeated user-context reads.
- Short-lived orchestration state for analysis jobs.

## Failure model

- PostgreSQL loss is critical for stateful backend behavior.
- Redis loss is non-critical:
  - caches are bypassed
  - analysis processing continues
  - job detail queries fall back to persisted summaries

## Build and deployment model

- `backend/pom.xml` builds the backend application directly.
- Docker builds use the generic backend Dockerfile under `infra/docker/dockerfiles`.
- Compose is defined under `infra/docker/compose/docker-compose.yml`.
- Web assets are built once and served by Nginx, with `/api` routed to `backend`.
