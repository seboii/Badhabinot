# Redis Architecture

## Purpose

Redis is used for low-latency, short-lived runtime data that should not live permanently in PostgreSQL.

## Backend usage

### User cache

- Cache names:
  - `user-context`
  - `user-settings`
  - `user-consents`
  - `analysis-context`
- Key prefix: `badhabinot:user-service:<cache-name>::<user-id>`
- TTL: `USER_CONTEXT_CACHE_TTL`, default `PT5M`
- Invalidation:
  - profile updates evict `user-context` and `analysis-context`
  - settings updates evict `user-context`, `user-settings`, `analysis-context`
  - consent updates evict `user-context`, `user-consents`, `analysis-context`
  - bootstrap evicts all user-scoped caches

### Monitoring job state

- Key pattern: `ANALYSIS_JOB_KEY_PREFIX + <analysis-id>`
- Default prefix: `badhabinot:monitoring:analysis-job:`
- TTL: `ANALYSIS_JOB_CACHE_TTL`, default `PT15M`
- Payload stores:
  - status
  - session/frame identifiers
  - subject presence
  - posture and behavior results
  - confidence
  - processing metrics
  - failure code/message
  - expiration timestamp

## Why Redis fits here

- Repeated user-context lookups happen during dashboard and analysis flows.
- Analysis orchestration state is short-lived and read-heavy.
- The monitoring pipeline benefits from fast retrieval of the latest job status without bloating permanent tables.

## Failure handling

- User cache failures are swallowed by a custom `CacheErrorHandler`; requests fall back to direct database reads.
- Monitoring Redis read/write failures are logged and ignored; persisted job state in PostgreSQL remains available.

## Non-goals

- Redis is not used for permanent history.
- Redis is not used as a document database.
- Redis is not required for service startup correctness when PostgreSQL remains available.
