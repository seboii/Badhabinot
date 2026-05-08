import logging

from fastapi import FastAPI

from app.api.routes import health, vision
from app.api.routes.face_registration import router as face_router
from app.api.routes.session_export import router as session_export_router
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
app.include_router(face_router)              # Module A — face registration & auth
app.include_router(session_export_router)   # Module H — session log export
