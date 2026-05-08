"""Step 3 / Module F — YOLOv8 Object Detection with COCO class pruning.

Detects only the allowed COCO classes relevant to behavioral monitoring:
    0  person
   39  bottle
   41  cup
   67  cell phone  (extra: distraction)

All other COCO classes are suppressed via the `classes` filter argument.

Cigarette detection is handled heuristically via the existing
elongated_object_score in VisionFeatureExtractor rather than a separate class,
since vanilla YOLOv8 COCO does not have a 'cigarette' class.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

import numpy as np

logger = logging.getLogger(__name__)

try:
    from ultralytics import YOLO  # type: ignore[import-untyped]
    _ULTRALYTICS_AVAILABLE = True
except ImportError:  # pragma: no cover
    _ULTRALYTICS_AVAILABLE = False
    logger.warning("ultralytics not installed — YOLO object detection disabled")

# ── Allowed COCO class IDs ──────────────────────────────────────────────────
ALLOWED_CLASSES: dict[int, str] = {
    0:  "person",
    39: "bottle",
    41: "cup",
    67: "cell_phone",
}
_CLASS_IDS = list(ALLOWED_CLASSES.keys())

_DETECT_MODEL_NAME = "yolov8n.pt"
_CONFIDENCE_THRESHOLD = 0.4


@dataclass
class YoloDetection:
    class_id: int
    class_name: str
    confidence: float
    # Normalized bounding box (x1, y1, x2, y2) in [0, 1]
    bbox_norm: tuple[float, float, float, float]

    @property
    def center_x(self) -> float:
        return (self.bbox_norm[0] + self.bbox_norm[2]) / 2.0

    @property
    def center_y(self) -> float:
        return (self.bbox_norm[1] + self.bbox_norm[3]) / 2.0

    @property
    def width(self) -> float:
        return self.bbox_norm[2] - self.bbox_norm[0]

    @property
    def height(self) -> float:
        return self.bbox_norm[3] - self.bbox_norm[1]


@dataclass
class YoloDetectionResult:
    detections: list[YoloDetection] = field(default_factory=list)

    # Convenience flags
    bottle_near_mouth: bool = False
    cup_near_mouth: bool = False
    phone_detected: bool = False

    def by_class(self, name: str) -> list[YoloDetection]:
        return [d for d in self.detections if d.class_name == name]


class VisionYoloDetector:
    """YOLOv8n object detector restricted to behavioral-monitoring classes."""

    def __init__(self) -> None:
        self._model: object | None = None

    # ------------------------------------------------------------------ #
    # Public API                                                           #
    # ------------------------------------------------------------------ #

    def detect(
        self,
        image: np.ndarray,
        mouth_region: tuple[float, float, float, float] | None = None,
    ) -> YoloDetectionResult | None:
        """Run object detection on *image*.

        *mouth_region*: optional normalized (x1, y1, x2, y2) of the mouth area
        used to compute bottle/cup proximity flags.

        Returns None if ultralytics is not installed.
        """
        if not _ULTRALYTICS_AVAILABLE:
            return None

        model = self._get_model()
        raw = model(
            image,
            verbose=False,
            conf=_CONFIDENCE_THRESHOLD,
            classes=_CLASS_IDS,
        )

        detections: list[YoloDetection] = []
        if raw and raw[0].boxes is not None and len(raw[0].boxes) > 0:
            boxes = raw[0].boxes
            xyxyn = boxes.xyxyn.cpu().numpy()
            confs = boxes.conf.cpu().numpy()
            cls_ids = boxes.cls.cpu().numpy().astype(int)

            for i in range(len(cls_ids)):
                cid = int(cls_ids[i])
                name = ALLOWED_CLASSES.get(cid, str(cid))
                detections.append(YoloDetection(
                    class_id=cid,
                    class_name=name,
                    confidence=round(float(confs[i]), 3),
                    bbox_norm=(
                        round(float(xyxyn[i][0]), 4),
                        round(float(xyxyn[i][1]), 4),
                        round(float(xyxyn[i][2]), 4),
                        round(float(xyxyn[i][3]), 4),
                    ),
                ))

        bottle_near = False
        cup_near = False
        phone_found = any(d.class_name == "cell_phone" for d in detections)

        if mouth_region is not None:
            for det in detections:
                if det.class_name in ("bottle", "cup"):
                    overlap = self._iou(det.bbox_norm, mouth_region)
                    proximity = overlap > 0.05 or self._center_distance(
                        det.bbox_norm, mouth_region
                    ) < 0.12
                    if det.class_name == "bottle":
                        bottle_near = proximity
                    else:
                        cup_near = proximity

        return YoloDetectionResult(
            detections=detections,
            bottle_near_mouth=bottle_near,
            cup_near_mouth=cup_near,
            phone_detected=phone_found,
        )

    # ------------------------------------------------------------------ #
    # Private helpers                                                      #
    # ------------------------------------------------------------------ #

    def _get_model(self) -> object:
        if self._model is None:
            logger.info("Loading YOLOv8n model (%s)…", _DETECT_MODEL_NAME)
            self._model = YOLO(_DETECT_MODEL_NAME)
        return self._model

    @staticmethod
    def _iou(a: tuple[float, float, float, float], b: tuple[float, float, float, float]) -> float:
        ix1 = max(a[0], b[0])
        iy1 = max(a[1], b[1])
        ix2 = min(a[2], b[2])
        iy2 = min(a[3], b[3])
        if ix2 <= ix1 or iy2 <= iy1:
            return 0.0
        inter = (ix2 - ix1) * (iy2 - iy1)
        area_a = (a[2] - a[0]) * (a[3] - a[1])
        area_b = (b[2] - b[0]) * (b[3] - b[1])
        union = area_a + area_b - inter
        return inter / max(union, 1e-6)

    @staticmethod
    def _center_distance(
        a: tuple[float, float, float, float],
        b: tuple[float, float, float, float],
    ) -> float:
        import math
        cx_a = (a[0] + a[2]) / 2.0
        cy_a = (a[1] + a[3]) / 2.0
        cx_b = (b[0] + b[2]) / 2.0
        cy_b = (b[1] + b[3]) / 2.0
        return math.hypot(cx_a - cx_b, cy_a - cy_b)
