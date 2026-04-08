import logging

from fastapi import FastAPI

from app.api.routes import health, vision
from app.core.config import settings

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)

app = FastAPI(
    title="BADHABINOT Vision Service",
    version=settings.app_version,
    description="OpenCV-based preprocessing and vision orchestration service for BADHABINOT",
)

app.include_router(health.router)
app.include_router(vision.router)
