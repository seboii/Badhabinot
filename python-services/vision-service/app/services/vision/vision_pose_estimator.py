"""Module E — Postür Analizi (MediaPipe Pose).

Üst gövde keypoint'lerini **MediaPipe Pose** (33 landmark, her birinde
``visibility`` = güven) ile çıkarır ve çok-sinyalli postür değerlendirmesi için
ham geometriyi hesaplar. Önceki **YOLOv8-pose** yerine MediaPipe Pose kullanılır:

- **torch/ultralytics gerektirmez** (pose tarafında) → CPU'da hafif, yüksek fps.
- Her landmark'ın **``visibility`` güveni** vardır → güven eşiğinin altındaki
  noktalar "yok" sayılır (kullanıcının istediği "conf değerine göre" davranış).
- Mimari netleşir: **MediaPipe = iskelet/yüz/el geometrisi**, **YOLO = nesne
  tespiti** (şişe/bardak/telefon).

Puanlama mantığı ``vision_posture`` modülünde toplanmıştır; bu sınıf yalnızca
keypoint'leri çıkarır ve durağan (oturum-bağımsız) bir taban skoru üretir. Nihai
oturum-farkında **dik / yamuk** kararı ``PostureEvaluator`` tarafından verilir.

MediaPipe Pose 33 landmark'ı, mevcut geometri çekirdeğinin beklediği COCO-17
üst-gövde düzenine eşlenir; böylece ``vision_posture`` ve aşağı akış tüketicileri
(şema, overlay) değişmeden çalışır.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

import cv2
import numpy as np

from app.core.config import settings
from app.services.vision.vision_posture import (
    PostureMetrics,
    compute_metrics_from_pixels,
    score_metrics,
)

logger = logging.getLogger(__name__)

try:
    import mediapipe as mp  # type: ignore[import-untyped]
    _mp_pose = mp.solutions.pose  # type: ignore[attr-defined]
    _MP_AVAILABLE = True
except (ImportError, AttributeError):  # pragma: no cover
    _MP_AVAILABLE = False
    logger.warning("mediapipe not installed or solutions API unavailable — pose estimation disabled")

# COCO keypoint indices (geriye dönük referans / şema uyumu için korunur)
_KP_NOSE = 0
_KP_LEFT_EYE = 1
_KP_RIGHT_EYE = 2
_KP_LEFT_EAR = 3
_KP_RIGHT_EAR = 4
_KP_LEFT_SHOULDER = 5
_KP_RIGHT_SHOULDER = 6

# COCO-17 → MediaPipe Pose 33 landmark eşlemesi.
#   COCO:  0 nose, 1 l_eye, 2 r_eye, 3 l_ear, 4 r_ear, 5 l_shoulder, 6 r_shoulder,
#          7 l_elbow, 8 r_elbow, 9 l_wrist, 10 r_wrist, 11 l_hip, 12 r_hip,
#          13 l_knee, 14 r_knee, 15 l_ankle, 16 r_ankle
#   MP:    0 nose, 2 l_eye, 5 r_eye, 7 l_ear, 8 r_ear, 11/12 shoulders, 13/14 elbows,
#          15/16 wrists, 23/24 hips, 25/26 knees, 27/28 ankles
_COCO_TO_MP: tuple[int, ...] = (0, 2, 5, 7, 8, 11, 12, 13, 14, 15, 16, 23, 24, 25, 26, 27, 28)

# Bu görünürlüğün (visibility) altındaki keypoint "yok" sayılır.
_KP_CONFIDENCE_FLOOR = 0.3


@dataclass
class PoseKeypoint:
    x: float            # normalized [0, 1]
    y: float            # normalized [0, 1]
    confidence: float   # MediaPipe visibility [0, 1]


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

    # ── Çok-sinyalli postür alanları ────────────────────────────────────
    posture_category: str = "unknown"
    forward_head_ratio: float = 0.0
    lateral_offset: float = 0.0
    head_roll: float = 0.0
    head_down_ratio: float = 0.0
    proximity_ratio: float = 0.0
    # Ham metrikler — PostureEvaluator tarafından oturum kararı için kullanılır.
    metrics: PostureMetrics | None = None


class VisionPoseEstimator:
    """MediaPipe Pose sarmalayıcısı — üst gövde postür analizi (dik / yamuk)."""

    def __init__(self) -> None:
        self._pose: object | None = None

    # ------------------------------------------------------------------ #
    # Public API                                                           #
    # ------------------------------------------------------------------ #

    def analyze(
        self,
        image: np.ndarray,
        owner_bbox: tuple[int, int, int, int] | None = None,
    ) -> PoseResult | None:
        """*image* (BGR, uint8) üzerinde MediaPipe Pose tahmini çalıştırır.

        *owner_bbox* (sahibin yüz bbox'ı, piksel) verildiğinde, tespit edilen
        kişinin başı bu kutuyla örtüşmüyorsa ``None`` döner — böylece bir
        yabancının postürü sahibe atfedilmez (DeepFace owner-lock ile uyumlu).

        mediapipe yoksa veya kişi yoksa ``None`` döner.
        """
        if not _MP_AVAILABLE:
            return None

        pose = self._get_pose()
        h, w = image.shape[:2]

        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = pose.process(rgb)
        if not getattr(results, "pose_landmarks", None):
            return None

        landmarks = results.pose_landmarks.landmark  # 33 landmark

        # Hem normalize keypoint listesini (yanıt/overlay) hem de geometri için
        # piksel-uzayı nokta listesini (None=güvensiz) tek geçişte oluştur.
        keypoints: list[PoseKeypoint | None] = []
        pixel_points: list[tuple[float, float] | None] = []
        for mp_idx in _COCO_TO_MP:
            lm = landmarks[mp_idx] if mp_idx < len(landmarks) else None
            vis = float(getattr(lm, "visibility", 0.0)) if lm is not None else 0.0
            if lm is None or vis < _KP_CONFIDENCE_FLOOR:
                keypoints.append(None)
                pixel_points.append(None)
            else:
                px, py = float(lm.x) * w, float(lm.y) * h
                keypoints.append(PoseKeypoint(
                    x=round(float(lm.x), 4), y=round(float(lm.y), 4), confidence=round(vis, 3),
                ))
                pixel_points.append((px, py))

        # Owner-lock: sahip yüz kutusu verildiyse ve tespit edilen kişinin başı
        # o kutuyla örtüşmüyorsa, bu bir yabancı → postürü sahibe atfetme.
        if owner_bbox is not None and not self._head_matches_owner(pixel_points, owner_bbox):
            return None

        # ── Çok-sinyalli postür geometrisi (piksel uzayında) ──────────────
        metrics = compute_metrics_from_pixels(pixel_points, w, h)
        base_score, category, _components = score_metrics(metrics)

        person_bbox = self._bbox_from_points(pixel_points, w, h)

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

    def _get_pose(self) -> object:
        if self._pose is None:
            logger.info("Loading MediaPipe Pose (complexity=%d)…", settings.posture_pose_complexity)
            # static_image_mode=True: her kare bağımsız işlenir. Bu servis tek
            # singleton olduğundan ve farklı oturumların kareleri aynı nesneden
            # geçtiğinden, kareler-arası takip durumunun oturumlar arası sızmasını
            # önlemek için durağan mod doğru seçimdir (face_mesh gaze ile aynı desen).
            self._pose = _mp_pose.Pose(
                static_image_mode=True,
                model_complexity=settings.posture_pose_complexity,
                smooth_landmarks=False,
                enable_segmentation=False,
                min_detection_confidence=settings.posture_pose_min_confidence,
            )
        return self._pose

    @staticmethod
    def _head_matches_owner(
        pixel_points: list[tuple[float, float] | None],
        owner_bbox: tuple[int, int, int, int],
    ) -> bool:
        """Tespit edilen kişinin başı sahibin yüz kutusuyla örtüşüyor mu?

        Baş referansı sırasıyla: burun → göz ortası → omuz ortası. Hiçbiri
        bulunamazsa doğrulanamaz kabul edilip ``True`` döner (aşırı baskılamayı
        önlemek için). ``owner_bbox`` = (x, y, w, h) piksel.
        """
        ox, oy, ow, oh = owner_bbox
        if ow <= 0 or oh <= 0:
            return True  # geçersiz kutu → doğrulayamayız

        head = pixel_points[_KP_NOSE]
        if head is None:
            le, re = pixel_points[_KP_LEFT_EYE], pixel_points[_KP_RIGHT_EYE]
            if le is not None and re is not None:
                head = ((le[0] + re[0]) / 2.0, (le[1] + re[1]) / 2.0)
        if head is None:
            ls, rs = pixel_points[_KP_LEFT_SHOULDER], pixel_points[_KP_RIGHT_SHOULDER]
            if ls is not None and rs is not None:
                # Omuz ortası başın ~bir kutu-boyu altında olur; kutuyu yukarı kaydır.
                head = ((ls[0] + rs[0]) / 2.0, (ls[1] + rs[1]) / 2.0 - oh)
        if head is None:
            return True  # baş referansı yok → baskılama

        cx, cy = ox + ow / 2.0, oy + oh / 2.0
        # Yüz kutusu küçüktür; başın kutunun yakın çevresinde olmasına izin ver.
        pad_x = ow * 1.5
        pad_y = oh * 1.5
        return abs(head[0] - cx) <= pad_x and abs(head[1] - cy) <= pad_y

    @staticmethod
    def _bbox_from_points(
        pixel_points: list[tuple[float, float] | None],
        frame_w: int,
        frame_h: int,
    ) -> tuple[float, float, float, float] | None:
        """Görünür keypoint'lerden normalize kişi sınırlayıcı kutusu üretir."""
        xs = [p[0] for p in pixel_points if p is not None]
        ys = [p[1] for p in pixel_points if p is not None]
        if not xs or not ys:
            return None
        x1 = max(0.0, min(xs) / max(frame_w, 1))
        y1 = max(0.0, min(ys) / max(frame_h, 1))
        x2 = min(1.0, max(xs) / max(frame_w, 1))
        y2 = min(1.0, max(ys) / max(frame_h, 1))
        return (round(x1, 4), round(y1, 4), round(x2, 4), round(y2, 4))