"""Etiketli kareleri vision pipeline'ından geçirip baskın tahmin sınıfını üretir.

Her kare bağımsız değerlendirilir: kareye özel session_id kullanılır, böylece
duration-tabanlı behavior state'i kareler arası sızmaz (tek-kare sınıflandırma).
"""

from __future__ import annotations

import base64
from datetime import datetime, timezone
from pathlib import Path

from app.schemas.vision import VisionAnalysisRequest
from app.services.vision_analysis_service import VisionAnalysisService
from evaluation.dataset import Sample
from evaluation.labels import dominant_label_from_response


def _encode_image(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode("utf-8")


async def predict_samples(
    samples: list[Sample],
    service: VisionAnalysisService | None = None,
) -> tuple[list[str], list[str]]:
    """Örnekleri pipeline'dan geçirir.

    Returns (y_true, y_pred) — örnek sırasıyla hizalı etiket listeleri.
    """
    service = service or VisionAnalysisService()
    captured_at = datetime.now(tz=timezone.utc)

    y_true: list[str] = []
    y_pred: list[str] = []
    for sample in samples:
        request = VisionAnalysisRequest(
            request_id=f"eval-{sample.frame_id}",
            user_id="eval-user",
            session_id=f"eval-{sample.frame_id}",   # kareye özel — state izolasyonu
            frame_id=sample.frame_id,
            captured_at=captured_at,
            image_base64=_encode_image(sample.image_path),
            image_content_type="image/jpeg",
        )
        response = await service.analyze(request)
        y_true.append(sample.label)
        y_pred.append(dominant_label_from_response(response))

    return y_true, y_pred
