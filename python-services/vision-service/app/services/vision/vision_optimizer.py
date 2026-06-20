"""Performans optimizasyon katmanı — frame skipping, önbellek ve küçültme.

Servis arka planda sürekli çalıştığı için her kareyi tüm ağır modüllerden
geçirmek işlemciyi boğar. Bu modül üç teknik sağlar:

1. **FrameScheduler** — sunucu tarafı "frame skipping". Yavaş değişen ağır
   modülleri (DeepFace yüz kimliği, nesne YOLO'su, iris bakışı) her N karede bir
   çalıştırır; aradaki karelerde önbellekteki son sonuç kullanılır.
2. **DetectorCache** — oturum başına, atlanan modüllerin son sonucunu tutar →
   yanıt sözleşmesi (frontend/backend) kesintisiz veri görmeye devam eder.
3. **downscale_for_inference** — kareyi çıkarım öncesi en uzun kenarı
   ``VISION_MAX_DIM`` olacak şekilde küçültür (asla büyütmez).

Kamera okuma tarayıcıda olduğu ve kareler HTTP ile geldiği için "ayrı thread'de
kamera okuma" burada uygulanamaz; pipeline zaten ``asyncio.to_thread`` ile
dedektörleri paralel çalıştırır. Bu katman gerçek darboğaza —ağır modellerin her
karede tekrar çalışmasına— yöneliktir.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any

import cv2
import numpy as np

from app.core.config import settings


@dataclass
class ScheduleDecision:
    """Bu karede hangi ağır modüllerin yeniden çalışacağını belirten bayraklar."""

    run_owner_id: bool = True
    run_objects: bool = True
    run_gaze: bool = True
    run_pose: bool = True
    run_mesh: bool = True
    run_hands: bool = True


@dataclass
class _SchedulerState:
    frame_index: int = 0
    last_seen: datetime = field(default_factory=lambda: datetime.now(tz=timezone.utc))


class FrameScheduler:
    """Oturum başına kare sayar ve yapılandırılmış aralıklara göre karar verir.

    Her oturumun ilk karesinde (index 0) tüm modüller çalışır; sonrasında modül
    yalnızca ``frame_index % interval == 0`` olduğunda yeniden çalışır.
    """

    def __init__(self, expiry_minutes: int = 30) -> None:
        self._expiry = timedelta(minutes=expiry_minutes)
        self._states: dict[str, _SchedulerState] = {}

    def tick(self, session_id: str, now: datetime | None = None) -> ScheduleDecision:
        now = now or datetime.now(tz=timezone.utc)
        self._cleanup(now)
        st = self._states.get(session_id)
        if st is None:
            st = _SchedulerState()
            self._states[session_id] = st
        else:
            st.frame_index += 1
        st.last_seen = now

        idx = st.frame_index

        def due(interval: int) -> bool:
            interval = max(1, interval)
            return idx % interval == 0

        return ScheduleDecision(
            run_owner_id=due(settings.vision_owner_id_interval),
            run_objects=due(settings.vision_object_interval),
            run_gaze=due(settings.vision_gaze_interval),
            run_pose=due(settings.vision_pose_interval),
            run_mesh=due(settings.vision_mesh_interval),
            run_hands=due(settings.vision_hand_interval),
        )

    def _cleanup(self, now: datetime) -> None:
        expired = [sid for sid, s in self._states.items() if (now - s.last_seen) > self._expiry]
        for sid in expired:
            self._states.pop(sid, None)


@dataclass
class _CacheEntry:
    owner: Any | None = None     # (face_authenticated, auth_confidence, auth_status, owner_result)
    objects: Any | None = None   # YoloDetectionResult
    gaze: Any | None = None      # GazeResult
    last_seen: datetime = field(default_factory=lambda: datetime.now(tz=timezone.utc))


class DetectorCache:
    """Oturum başına, atlanan ağır modüllerin son sonuçlarını tutar."""

    def __init__(self, expiry_minutes: int = 30) -> None:
        self._expiry = timedelta(minutes=expiry_minutes)
        self._entries: dict[str, _CacheEntry] = {}

    def get(self, session_id: str, now: datetime | None = None) -> _CacheEntry:
        now = now or datetime.now(tz=timezone.utc)
        self._cleanup(now)
        entry = self._entries.get(session_id)
        if entry is None:
            entry = _CacheEntry()
            self._entries[session_id] = entry
        entry.last_seen = now
        return entry

    def _cleanup(self, now: datetime) -> None:
        expired = [sid for sid, e in self._entries.items() if (now - e.last_seen) > self._expiry]
        for sid in expired:
            self._entries.pop(sid, None)


def downscale_for_inference(image: np.ndarray, max_dim: int | None = None) -> np.ndarray:
    """Karenin en uzun kenarını *max_dim*'e indirger (asla büyütmez).

    Tüm dedektörler aynı küçültülmüş kare üzerinde çalıştığı için bbox/keypoint
    piksel koordinatları kendi içinde tutarlı kalır; yanıttaki tüm koordinatlar
    normalize (0-1) olduğu için downstream tüketiciler etkilenmez.
    """
    max_dim = max_dim or settings.vision_max_dim
    h, w = image.shape[:2]
    long_edge = max(h, w)
    if max_dim <= 0 or long_edge <= max_dim:
        return image
    scale = max_dim / float(long_edge)
    new_w = max(1, int(round(w * scale)))
    new_h = max(1, int(round(h * scale)))
    return cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
