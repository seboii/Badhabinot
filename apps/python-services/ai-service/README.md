# BADHABINOT AI Service

FastAPI microservice responsible for behavior inference. This service is internal-only in the local stack and expects `X-Internal-Api-Key` on inference requests.

## Endpoints

- `GET /health`
- `POST /v1/inference/predict`

## Local run

```powershell
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload --port 8092
```

## Test

```powershell
pip install -r requirements.txt -r requirements-dev.txt
pytest
```
