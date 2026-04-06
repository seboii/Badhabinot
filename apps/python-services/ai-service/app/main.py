import logging

from fastapi import FastAPI

from app.api.routes import health, inference
from app.core.config import settings

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)

app = FastAPI(
    title="BADHABINOT AI Service",
    version=settings.app_version,
    description="Behavior inference microservice for BADHABINOT",
)

app.include_router(health.router)
app.include_router(inference.router)
