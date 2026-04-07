import logging

from fastapi import FastAPI

from app.api.routes import analysis, chat, health, inference
from app.core.config import settings

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)

app = FastAPI(
    title="BADHABINOT AI Service",
    version=settings.app_version,
    description="External AI provider adapter service for BADHABINOT",
)

app.include_router(health.router)
app.include_router(analysis.router)
app.include_router(chat.router)
app.include_router(inference.router)
