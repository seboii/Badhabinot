"""Aktif challenge tabanlı canlılık (liveness) doğrulaması.

Yüz ile giriş tek durağan kareyle yapıldığında, kullanıcının bir fotoğrafı
(baskı veya ekran) saklı embedding ile aynı benzerliği üretip girişi geçebilir.
Bu modül, kullanıcıdan istenen rastgele bir eylemin (göz kırpma / baş çevirme)
KISA BİR KARE DİZİSİ boyunca gerçekten yapıldığını doğrular — durağan bir
fotoğraf komutla göz kırpamaz / başını çeviremez.

Sinyaller mevcut ``VisionFaceMesh``'ten gelir (EAR = göz açıklığı, yaw = baş
yatay dönüşü). Yeni ML modeli gerektirmez.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from app.services.vision.vision_face_mesh import VisionFaceMesh

# ── Eşikler (env ile değil; sahada ince ayar için sabit tutuldu) ────────────
_MIN_FACE_FRAMES = 3          # dizide en az bu kadar karede yüz olmalı
_BLINK_OPEN_EAR = 0.22        # "göz açık" sayılması için EAR tabanı
_BLINK_CLOSED_EAR = 0.18      # "göz kapalı" sayılması için EAR tavanı
_BLINK_MIN_DROP = 0.08        # açık→kapalı minimum EAR düşüşü
_TURN_CENTER_YAW = 12.0       # "merkeze yakın" baş açısı (derece)
_TURN_OFF_YAW = 18.0          # "çevrilmiş" sayılması için minimum açı
_TURN_MIN_SWING = 12.0        # min(|yaw|)→max(|yaw|) minimum salınım

ACTIONS = ("BLINK", "TURN_HEAD")


@dataclass
class LivenessResult:
    passed: bool
    action_detected: str | None
    detail: str


def verify_liveness(mesh: VisionFaceMesh, frames: list[np.ndarray], action: str) -> LivenessResult:
    """Kare dizisinde istenen *action*'ın yapılıp yapılmadığını doğrular."""
    action = (action or "").upper()
    if action not in ACTIONS:
        return LivenessResult(False, None, f"Bilinmeyen eylem: {action}")

    ears: list[float] = []
    yaws: list[float] = []
    for frame in frames:
        result = mesh.analyze(frame)
        if result is None:
            continue
        ears.append(float(result.ear))
        yaws.append(float(result.yaw))

    if len(ears) < _MIN_FACE_FRAMES:
        return LivenessResult(False, None, "Yeterli sayıda karede yüz algılanamadı")

    if action == "BLINK":
        max_ear = max(ears)
        min_ear = min(ears)
        blinked = (
            max_ear >= _BLINK_OPEN_EAR
            and min_ear <= _BLINK_CLOSED_EAR
            and (max_ear - min_ear) >= _BLINK_MIN_DROP
        )
        if blinked:
            return LivenessResult(True, "BLINK", "Göz kırpma algılandı")
        return LivenessResult(False, None, "Göz kırpma algılanmadı")

    # TURN_HEAD — merkeze yakın bir kare + yeterince çevrilmiş bir kare
    abs_yaws = [abs(y) for y in yaws]
    has_center = min(abs_yaws) <= _TURN_CENTER_YAW
    has_turn = max(abs_yaws) >= _TURN_OFF_YAW
    swing = max(abs_yaws) - min(abs_yaws)
    if has_center and has_turn and swing >= _TURN_MIN_SWING:
        return LivenessResult(True, "TURN_HEAD", "Baş çevirme algılandı")
    return LivenessResult(False, None, "Baş çevirme algılanmadı")
