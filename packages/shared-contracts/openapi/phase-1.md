# OpenAPI Notes

Runtime OpenAPI endpoints:

- Gateway docs: `GET /v3/api-docs`
- Gateway Swagger UI: `GET /swagger-ui.html`
- Auth docs: `GET /v3/api-docs`
- Auth Swagger UI: `GET /swagger-ui.html`
- User docs: `GET /v3/api-docs`
- User Swagger UI: `GET /swagger-ui.html`
- Monitoring docs: `GET /v3/api-docs`
- Monitoring Swagger UI: `GET /swagger-ui.html`
- Vision docs: `GET /docs`
- AI docs: `GET /docs`

Each service publishes its own OpenAPI document. There is no aggregated cross-service OpenAPI document yet; routing remains separated by service ownership.
