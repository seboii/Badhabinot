import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import analysis, chat, health, inference
from app.core.config import settings

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ARG001
    settings.log_startup()
    yield


app = FastAPI(
    title="BADHABINOT AI Service",
    version=settings.app_version,
    description="External AI provider adapter service for BADHABINOT",
    lifespan=lifespan,
)

app.include_router(health.router)
app.include_router(analysis.router)
app.include_router(chat.router)
app.include_router(inference.router)
