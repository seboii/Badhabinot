"""Değerlendirme sınıfları ve pipeline çıktısından sınıf çıkarımı.

Tek-etiketli (single-label) değerlendirme: her kare tek bir baskın sınıfa atanır.
'normal' = baskın riskli davranış yok. Çok-etiketli (multi-label) değerlendirme
gelecek bir genişlemedir (bkz. README).
"""

from __future__ import annotations

NORMAL = "normal"

# Değerlendirme sınıf kümesi — mevcut detection taksonomisiyle hizalı.
LABELS: list[str] = [
    NORMAL,
    "poor_posture",
    "hand_movement_pattern",
    "smoking_like_gesture",
]

# Vision detection event_type → değerlendirme sınıfı.
_DETECTION_TO_LABEL: dict[str, str] = {
    "poor_posture": "poor_posture",
    "hand_movement_pattern": "hand_movement_pattern",
    "smoking_like_gesture": "smoking_like_gesture",
}


def dominant_label_from_response(response: object) -> str:
    """VisionAnalysisResponse'tan baskın değerlendirme sınıfını çıkarır.

    En yüksek confidence'lı tanınan detection'ı seçer; tanınan detection yoksa
    'normal' döner. (Tek-etiketli değerlendirme için bilinçli sadeleştirme.)
    """
    best_label = NORMAL
    best_conf = -1.0
    for detection in getattr(response, "detections", []) or []:
        label = _DETECTION_TO_LABEL.get(detection.event_type)
        if label is not None and detection.confidence > best_conf:
            best_conf = detection.confidence
            best_label = label
    return best_label
