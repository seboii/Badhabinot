import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import health, vision
from app.api.routes.face_registration import router as face_router
from app.api.routes.session_export import router as session_export_router
from app.core.config import settings

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)

logger = logging.getLogger(__name__)


def _warm_up_models() -> None:
    """Load the heavy ML models once, single-threaded, at startup.

    Niyet: ilk istekte (özellikle eşzamanlı ilk isteklerde) modellerin tembel
    yüklenmesini/indirilmesini önlemek. Bu yarış geçmişte worker'ı çökertiyordu
    (paralel ağırlık indirmeleri belleği bozup core-dump'a yol açıyordu). Ağırlıklar
    imaja gömülü olduğundan burada indirme olmaz; sadece tek seferlik yükleme yapılır.
    """
    try:
        from deepface import DeepFace  # type: ignore[import-untyped]

        DeepFace.build_model("Facenet")
        logger.info("DeepFace Facenet model warmed up at startup")
    except Exception:  # pragma: no cover - warm-up is best-effort
        logger.warning("DeepFace warm-up skipped/failed; will lazy-load on demand", exc_info=True)

    # Aynı pipeline singleton'unun gerçek dedektörlerini ısıt (ilk-kare gecikmesini önle).
    # Her biri ayrı try ile: biri ısınamazsa diğerleri yine ısınır.
    from app.api.routes.vision import service as vision_service

    for name, warm in (
        ("YOLOv8 object detector", lambda: vision_service.yolo_detector._get_model()),
        ("MediaPipe Pose", lambda: vision_service.pose_estimator._get_pose()),
        ("MediaPipe FaceMesh", lambda: vision_service.face_mesh._get_mesh()),
    ):
        try:
            warm()
            logger.info("%s warmed up at startup", name)
        except Exception:  # pragma: no cover - warm-up is best-effort
            logger.warning("%s warm-up skipped/failed; will lazy-load on demand", name, exc_info=True)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    await asyncio.to_thread(_warm_up_models)
    yield


app = FastAPI(
    title="BADHABINOT Vision Service",
    version=settings.app_version,
    description="OpenCV-based preprocessing and vision orchestration service for BADHABINOT",
    lifespan=lifespan,
)

app.include_router(health.router)
app.include_router(vision.router)
app.include_router(face_router)              # Module A — face registration & auth
app.include_router(session_export_router)   # Module H — session log export
