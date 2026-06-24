"""Aktif challenge tabanlı canlılık (liveness) doğrulaması.

Yüz ile giriş tek durağan kareyle yapıldığında, kullanıcının bir fotoğrafı
(baskı veya ekran) saklı embedding ile aynı benzerliği üretip girişi geçebilir.
Bu modül, kullanıcıdan istenen rastgele bir eylemin (göz kırpma / baş çevirme)
KISA BİR KARE DİZİSİ boyunca gerçekten yapıldığını doğrular — durağan bir
fotoğraf komutla göz kırpamaz / başını çeviremez.

Sinyaller mevcut ``VisionFaceMesh``'ten gelir (EAR = göz açıklığı, yaw = baş
yatay dönüşü). Yeni ML modeli gerektirmez.

Tasarım notu (yanlış-ret azaltma):
- Eşikler KİŞİYE GÖRELİ. EAR mutlak değeri kişiden kişiye (0.18–0.35) ve kamera
  açısına göre değişir; bu yüzden göz kırpma, kullanıcının kendi açık-göz
  tabanına göre oransal düşüşle tespit edilir.
- İstenen eylem yapılmadıysa bile, kare dizisinde BELİRGİN bir canlılık sinyali
  (göz kırpma ya da baş hareketi) varsa geçer. Durağan fotoğraf ikisini de
  üretemediğinden hâlâ reddedilir; ama gerçek kullanıcı kilitlenmez.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # yalnız tip; runtime'da mediapipe/numpy import etme (test edilebilirlik)
    import numpy as np

    from app.services.vision.vision_face_mesh import VisionFaceMesh

# ── Eşikler (kişiye göreli; yanlış-ret düşük olacak şekilde gevşetildi) ──────
_MIN_FACE_FRAMES = 2          # dizide en az bu kadar karede yüz olmalı

# BLINK — kullanıcının kendi açık-göz tabanına göre oransal düşüş
_BLINK_MIN_OPEN = 0.14        # geçerli sinyal için minimum açık-göz EAR'ı
_BLINK_REL_DROP = 0.80        # min_ear <= max_ear * 0.80  (≈ %20 kapanma)
_BLINK_ABS_DROP = 0.035       # ek mutlak düşüş güvencesi (gürültüye karşı)

# TURN_HEAD — baş yatay hareketi (merkez şartı yok, salınım yeterli)
_TURN_OFF_YAW = 12.0          # bir karede ulaşılması gereken |yaw| (derece)
_TURN_MIN_SWING = 8.0         # min(|yaw|)→max(|yaw|) minimum salınım

ACTIONS = ("BLINK", "TURN_HEAD")


@dataclass
class LivenessResult:
    passed: bool
    action_detected: str | None
    detail: str


def _detect_blink(ears: list[float]) -> bool:
    """Açık-göz tabanına göre oransal bir EAR düşüşü var mı?"""
    if len(ears) < _MIN_FACE_FRAMES:
        return False
    max_ear = max(ears)
    min_ear = min(ears)
    return (
        max_ear >= _BLINK_MIN_OPEN
        and min_ear <= max_ear * _BLINK_REL_DROP
        and (max_ear - min_ear) >= _BLINK_ABS_DROP
    )


def _detect_turn(yaws: list[float]) -> bool:
    """Baş yatay olarak yeterince hareket etti mi (salınım)?"""
    if len(yaws) < _MIN_FACE_FRAMES:
        return False
    abs_yaws = [abs(y) for y in yaws]
    return max(abs_yaws) >= _TURN_OFF_YAW and (max(abs_yaws) - min(abs_yaws)) >= _TURN_MIN_SWING


def verify_liveness(mesh: VisionFaceMesh, frames: list[np.ndarray], action: str) -> LivenessResult:
    """Kare dizisinde canlılığı doğrular.

    Önce istenen eylem aranır; bulunmazsa diziye yansıyan herhangi belirgin bir
    canlılık sinyali (göz kırpma veya baş hareketi) kabul edilir (yanlış-ret
    azaltma). İki sinyal de yoksa (durağan fotoğraf) reddedilir.
    """
    requested = (action or "").upper()

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

    blink = _detect_blink(ears)
    turn = _detect_turn(yaws)

    # 1) İstenen eylem yapıldıysa
    if requested == "BLINK" and blink:
        return LivenessResult(True, "BLINK", "Göz kırpma algılandı")
    if requested == "TURN_HEAD" and turn:
        return LivenessResult(True, "TURN_HEAD", "Baş çevirme algılandı")

    # 2) Esnek geri-dönüş: herhangi belirgin canlılık sinyali yeterli
    if blink:
        return LivenessResult(True, "BLINK", "Canlılık algılandı (göz kırpma)")
    if turn:
        return LivenessResult(True, "TURN_HEAD", "Canlılık algılandı (baş hareketi)")

    return LivenessResult(False, None, "Canlılık algılanamadı — istenen hareketi yapın")
