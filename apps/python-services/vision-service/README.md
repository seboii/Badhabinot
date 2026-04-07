# BADHABINOT Vision Service

FastAPI microservice responsible for OpenCV preprocessing and feature extraction. This service is internal-only in the local stack and expects `X-Internal-Api-Key` on analysis requests.

## Endpoints

- `GET /health`
- `GET /ready`
- `POST /v1/vision/analyze`

## Local run

```powershell
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload --port 8091
```

## Test

```powershell
pip install -r requirements.txt -r requirements-dev.txt
pytest
```
