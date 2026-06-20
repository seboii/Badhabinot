# ADR 0001: Monorepo Structure

## Status

Accepted

## Decision

The repository is organized by runtime boundary:

- `backend` for the single Spring Boot service
- `python-services` for FastAPI AI/CV services
- `frontend` for the browser application
- `packages` for shared contracts, config fragments, and shared documentation
- `infra` for Docker, nginx, Redis, database bootstrap, and operational scripts

## Rationale

- Technology buckets alone (`services`, `edge`, `clients`) hide domain ownership.
- Infra assets should not be scattered inside application directories.
- Shared contracts and environment fragments need stable, predictable locations.
- Docker and Compose references become easier to understand when build assets live under one operational root.

## Consequences

- Build paths changed to `backend/*` for Maven modules.
- Compose now uses generic Dockerfiles under `infra/docker/dockerfiles`.
- Documentation and scripts reference the new paths.
- Redis and nginx configuration are explicitly discoverable under `infra`.
