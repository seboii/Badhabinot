"""Module E — Postür Analizi (YOLOv8-pose).

Üst gövde keypoint'lerini (COCO pose: burun, gözler, kulaklar, omuzlar, dirsekler)
çıkarır ve çok-sinyalli postür değerlendirmesi için ham geometriyi hesaplar:
- Omuz eğikliği (asimetri)
- Öne eğik baş / kamburluk (baş yüksekliği / omuz genişliği)
- Yana yatma, baş eğikliği (roll), başı aşağı eğme
- Ekrana yakınlık

Puanlama mantığı ``vision_posture`` modülünde toplanmıştır; bu sınıf yalnızca
keypoint'leri çıkarır ve durağan (oturum-bağımsız) bir taban skoru üretir.
Nihai oturum-farkında karar ``PostureEvaluator`` tarafından verilir.

Modeli ilk çağrıda lazy yükler; ``.onnx`` model yolu verilirse ONNX Runtime
üzerinden çalışır (CPU'da PyTorch'tan hızlı olabilir).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

import numpy as np

from app.core.config import settings
from app.services.vision.vision_posture import (
    PostureMetrics,
    compute_metrics_from_pixels,
    score_metrics,
)

logger = logging.getLogger(__name__)

try:
    from ultralytics import YOLO  # type: ignore[import-untyped]
    _ULTRALYTICS_AVAILABLE = True
except ImportError:  # pragma: no cover
    _ULTRALYTICS_AVAILABLE = False
    logger.warning("ultralytics not installed — pose estimation disabled")

# COCO keypoint indices (geriye dönük referans için korunur)
_KP_NOSE = 0
_KP_LEFT_EYE = 1
_KP_RIGHT_EYE = 2
_KP_LEFT_EAR = 3
_KP_RIGHT_EAR = 4
_KP_LEFT_SHOULDER = 5
_KP_RIGHT_SHOULDER = 6
_KP_LEFT_ELBOW = 7
_KP_RIGHT_ELBOW = 8
_KP_LEFT_WRIST = 9
_KP_RIGHT_WRIST = 10

_KP_CONFIDENCE_FLOOR = 0.3      # bu güvenin altındaki keypoint "yok" sayılır
_CONFIDENCE_THRESHOLD = 0.4     # YOLO kişi tespiti güven eşiği

_torch_threads_set = False


@dataclass
class PoseKeypoint:
    x: float            # normalized [0, 1]
    y: float            # normalized [0, 1]
    confidence: float


@dataclass
class PoseResult:
    """Bir kareye ait postür analizi çıktısı."""

    # COCO keypoints 0-16, tespit edilemeyende None
    keypoints: list[PoseKeypoint | None] = field(default_factory=list)

    # ── Geriye dönük uyumlu alanlar (mevcut ML eğitim/şema tüketicileri) ──
    spine_tilt_angle: float = 0.0       # boyun vektörünün dikeyden sapması (derece)
    shoulder_tilt_angle: float = 0.0    # omuz hattının yataydan sapması (derece)
    posture_score: int = 100            # 0-100 taban skoru (oturum-bağımsız)
    is_slouching: bool = False

    person_bbox: tuple[float, float, float, float] | None = None  # normalized

    # ── Yeni alanlar (çok-sinyalli postür) ──────────────────────────────
    posture_category: str = "unknown"
    forward_head_ratio: float = 0.0
    lateral_offset: float = 0.0
    head_roll: float = 0.0
    head_down_ratio: float = 0.0
    proximity_ratio: float = 0.0
    # Ham metrikler — PostureEvaluator tarafından oturum kararı için kullanılır.
    metrics: PostureMetrics | None = None


class VisionPoseEstimator:
    """YOLOv8-pose sarmalayıcısı — üst gövde postür analizi."""

    def __init__(self) -> None:
        self._model: object | None = None

    # ------------------------------------------------------------------ #
    # Public API                                                           #
    # ------------------------------------------------------------------ #

    def analyze(
        self,
        image: np.ndarray,
        owner_bbox: tuple[int, int, int, int] | None = None,
    ) -> PoseResult | None:
        """*image* (BGR, uint8) üzerinde pose tahmini çalıştırır.

        *owner_bbox* (sahibin yüz bbox'ı, piksel) verildiğinde ve birden fazla
        kişi varsa, sahibin yüz merkezini içeren gövde kutusuna sahip kişi analiz
        edilir — böylece bir yabancının postürü sahibe atfedilmez.

        ultralytics yoksa veya kişi yoksa None döner.
        """
        if not _ULTRALYTICS_AVAILABLE:
            return None

        model = self._get_model()
        h, w = image.shape[:2]

        results = model(
            image,
            verbose=False,
            conf=_CONFIDENCE_THRESHOLD,
            imgsz=settings.vision_pose_imgsz,
        )
        if not results or not results[0].keypoints:
            return None

        kps = results[0].keypoints
        boxes = results[0].boxes

        if kps is None or len(kps.xy) == 0:
            return None

        # Hangi kişinin analiz edileceğini seç (varsayılan en güvenli; owner_bbox
        # + çoklu kişi varsa sahibin yüzünü içeren kutu).
        person_idx = 0
        if (
            owner_bbox is not None
            and boxes is not None
            and boxes.xyxyn is not None
            and len(boxes.xyxyn) > 1
        ):
            owner_center = (
                (owner_bbox[0] + owner_bbox[2] / 2.0) / w,
                (owner_bbox[1] + owner_bbox[3] / 2.0) / h,
            )
            person_idx = self._select_person_index(boxes.xyxyn.cpu().numpy(), owner_center)
        if person_idx >= len(kps.xy):
            person_idx = 0

        kp_xy = kps.xy[person_idx].cpu().numpy()   # (17, 2) piksel koordinatları
        kp_conf = kps.conf[person_idx].cpu().numpy() if kps.conf is not None else np.ones(17)

        # Hem normalize keypoint listesini (yanıt/overlay) hem de geometri için
        # piksel-uzayı nokta listesini (None=güvensiz) tek geçişte oluştur.
        keypoints: list[PoseKeypoint | None] = []
        pixel_points: list[tuple[float, float] | None] = []
        for i in range(17):
            if i < len(kp_xy):
                conf = float(kp_conf[i]) if i < len(kp_conf) else 0.0
            else:
                conf = 0.0
            if conf < _KP_CONFIDENCE_FLOOR or i >= len(kp_xy):
                keypoints.append(None)
                pixel_points.append(None)
            else:
                px, py = float(kp_xy[i][0]), float(kp_xy[i][1])
                keypoints.append(PoseKeypoint(
                    x=round(px / w, 4), y=round(py / h, 4), confidence=round(conf, 3),
                ))
                pixel_points.append((px, py))

        # ── Çok-sinyalli postür geometrisi (piksel uzayında) ──────────────
        metrics = compute_metrics_from_pixels(pixel_points, w, h)
        base_score, category, _components = score_metrics(metrics)

        # Kişi sınırlayıcı kutusu (aynı seçilen kişi)
        person_bbox = None
        if boxes is not None and len(boxes.xyxyn) > person_idx:
            b = boxes.xyxyn[person_idx].cpu().numpy()
            person_bbox = (round(float(b[0]), 4), round(float(b[1]), 4),
                           round(float(b[2]), 4), round(float(b[3]), 4))

        is_slouching = metrics.reliable and base_score < settings.posture_poor_score

        return PoseResult(
            keypoints=keypoints,
            spine_tilt_angle=round(metrics.neck_inclination_deg, 2),
            shoulder_tilt_angle=round(metrics.shoulder_tilt_deg, 2),
            posture_score=base_score,
            is_slouching=is_slouching,
            person_bbox=person_bbox,
            posture_category=category,
            forward_head_ratio=metrics.forward_head_ratio,
            lateral_offset=metrics.lateral_offset,
            head_roll=metrics.head_roll_deg,
            head_down_ratio=metrics.head_down_ratio,
            proximity_ratio=metrics.proximity_ratio,
            metrics=metrics,
        )

    # ------------------------------------------------------------------ #
    # Private helpers                                                      #
    # ------------------------------------------------------------------ #

    def _get_model(self) -> object:
        if self._model is None:
            self._apply_torch_threads()
            model_name = settings.vision_pose_model
            logger.info("Loading YOLOv8-pose model (%s)…", model_name)
            self._model = YOLO(model_name)
        return self._model

    @staticmethod
    def _apply_torch_threads() -> None:
        """CPU thread tavanını uygula (eş zamanlı isteklerde oversubscription'ı önler)."""
        global _torch_threads_set
        if _torch_threads_set or settings.vision_torch_threads <= 0:
            return
        try:
            import torch  # type: ignore[import-untyped]
            torch.set_num_threads(settings.vision_torch_threads)
            _torch_threads_set = True
            logger.info("torch CPU threads capped at %d", settings.vision_torch_threads)
        except Exception:  # pragma: no cover
            logger.debug("could not set torch threads", exc_info=True)

    @staticmethod
    def _select_person_index(
        boxes_xyxyn: "np.ndarray",
        owner_center: tuple[float, float],
    ) -> int:
        """Sahibin yüz merkezini içeren kişi kutusunu seç.

        Birden fazla kutu içeriyorsa en küçüğü (en spesifik) seçilir. Hiçbiri
        içermiyorsa merkezi sahibe en yakın kutu seçilir. ``boxes_xyxyn``
        satırları normalize (x1, y1, x2, y2).
        """
        ocx, ocy = owner_center
        containing: list[tuple[int, float]] = []
        for i, b in enumerate(boxes_xyxyn):
            x1, y1, x2, y2 = float(b[0]), float(b[1]), float(b[2]), float(b[3])
            if x1 <= ocx <= x2 and y1 <= ocy <= y2:
                containing.append((i, (x2 - x1) * (y2 - y1)))
        if containing:
            return min(containing, key=lambda t: t[1])[0]

        best_i, best_d = 0, float("inf")
        for i, b in enumerate(boxes_xyxyn):
            cx = (float(b[0]) + float(b[2])) / 2.0
            cy = (float(b[1]) + float(b[3])) / 2.0
            d = (cx - ocx) ** 2 + (cy - ocy) ** 2
            if d < best_d:
                best_d, best_i = d, i
        return best_i
