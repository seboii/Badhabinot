# BADHABINOT AI Service

FastAPI microservice responsible for higher-level analysis through configurable external AI providers. It expects `X-Internal-Api-Key` on internal analysis requests.

## Endpoints

- `GET /health`
- `GET /ready`
- `POST /v1/analysis/interpret`
- `POST /v1/chat/respond`
- `POST /v1/inference/predict` (deprecated compatibility alias)

## Local run

```powershell
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8092
```

This service reads configuration from the repository root `.env`. The production path is API-based (`AI_PROVIDER=openai-compatible`) and requires `AI_API_KEY`.

Optional local fallback for offline debugging only:

- `AI_PROVIDER=mock`
- `AI_MODEL_NAME=mock-behavior-analyzer`

## Test

```powershell
pip install -r requirements.txt -r requirements-dev.txt
pytest
```
