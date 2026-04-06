# BADHABINOT Architecture Blueprint

## Objectives

- Keep Java business services independent from Python AI/CV workloads.
- Keep the frontend standalone and environment-driven.
- Centralize infrastructure and container build assets.
- Use Redis for short-lived acceleration and orchestration support, never as the primary database.

## Runtime topology

```text
frontend-app
  -> api-gateway
      -> auth-service
      -> user-service
      -> monitoring-service
            -> user-service (internal analysis context)
            -> vision-service
                  -> ai-service

auth-service -> user-service (internal bootstrap)
auth-service/user-service/monitoring-service -> PostgreSQL
user-service/monitoring-service -> Redis
```

## Monorepo boundaries

### `apps/backend`

- Spring Boot services only.
- Each service owns its own source set, persistence logic, and service-local configuration.
- `monitoring-service` is the orchestration boundary for CV and AI workflows.

### `apps/python-services`

- FastAPI microservices only.
- `vision-service` owns image decoding, OpenCV analysis, and inference request preparation.
- `ai-service` owns behavior classification and model metadata responses.

### `apps/web`

- SPA-only codebase.
- API integration is isolated behind `src/api`.
- Theme behavior is isolated behind `src/theme`.

### `packages`

- Shared non-runtime assets only.
- Contracts, config fragments, and shared docs live here to avoid leaking them into app folders.

### `infra`

- Docker Compose, generic Dockerfiles, operational scripts, nginx config, Redis config, and database bootstrap assets.

## Data stores

### PostgreSQL

- Source of truth for auth, user, monitoring sessions, activity feeds, hydration logs, and persisted analysis jobs.

### Redis

- `user-service` cache layer for repeated reads.
- `monitoring-service` short-lived orchestration state for analysis jobs.

## Failure model

- PostgreSQL loss is critical for stateful services.
- Redis loss is non-critical:
  - caches are bypassed
  - analysis processing continues
  - job detail queries fall back to persisted summaries

## Build and deployment model

- Root `pom.xml` is the Maven aggregator for Java services.
- Docker builds use generic service Dockerfiles under `infra/docker/dockerfiles`.
- Compose is defined under `infra/docker/compose/docker-compose.yml`.
- Web assets are built once and served by Nginx, with `/api` routed to `api-gateway`.
