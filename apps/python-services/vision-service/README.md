# BADHABINOT Vision Service

FastAPI microservice responsible for OpenCV preprocessing and feature extraction. This service is internal-only in the local stack and expects `X-Internal-Api-Key` on analysis requests.

## Endpoints

- `GET /health`
- `GET /ready`
- `POST /v1/vision/analyze`

## Local run

```powershell
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8091
```

This service reads configuration from the repository root `.env`.

## Test

```powershell
pip install -r requirements.txt -r requirements-dev.txt
pytest
```
