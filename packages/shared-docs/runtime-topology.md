# Runtime Topology

```text
frontend-app -> api-gateway
api-gateway -> auth-service
api-gateway -> user-service
api-gateway -> monitoring-service
auth-service -> user-service
monitoring-service -> user-service
monitoring-service -> vision-service -> ai-service
user-service -> Redis
monitoring-service -> Redis
auth-service/user-service/monitoring-service -> PostgreSQL
```
