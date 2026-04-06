# Redis Infra

`redis.conf` defines the local Redis runtime used by the platform.

- persistence is disabled
- `allkeys-lfu` is used because the data is cache-like and ephemeral
- memory is capped to keep local development predictable

Redis is intentionally treated as a transient acceleration layer, not a durable database.
