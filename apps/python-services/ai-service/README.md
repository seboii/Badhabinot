# BADHABINOT AI Service

FastAPI microservice responsible for higher-level analysis through configurable external AI providers. It expects `X-Internal-Api-Key` on internal analysis requests.

## Endpoints

- `GET /health`
- `GET /ready`
- `POST /v1/analysis/interpret`
- `POST /v1/inference/predict` (deprecated compatibility alias)

## Local run

```powershell
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8092
```

This service reads configuration from the repository root `.env`. For local Docker, `.env.example` defaults to `AI_PROVIDER=mock` so the stack starts without external credentials. Switch the root `.env` to `openai-compatible` and provide `AI_API_KEY` for real API-backed analysis.

## Test

```powershell
pip install -r requirements.txt -r requirements-dev.txt
pytest
```
