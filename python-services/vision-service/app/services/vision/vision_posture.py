"""Postür değerlendirme çekirdeği — çok sinyalli, kalibrasyonlu, oturum-farkında.

Bu modül postürü TEK bir sinyalden değil, omuz + boyun/kulak + burun + baş
eğikliği + ekrana yakınlık sinyallerinin BİRLEŞİMİNDEN puanlar. Amaç: kullanıcı
düzgün otururken "iyi" demek, gerçek kamburluk/yana yatma/öne eğilmede uyarmak.

Tasarım kararları
-----------------
* Tüm geometri **piksel uzayında** hesaplanır. Normalize (0-1) koordinatlarda
  x ve y farklı ölçeklere bölündüğü için (16:9 karede) açılar bozulur; piksel
  uzayı doğru açıyı verir.
* Tüm mesafeler **omuz genişliğine** göre normalize edilir → kullanıcının
  kameraya uzaklığından bağımsız çalışır.
* **Oturum bazlı taban çizgisi (auto-calibration):** kullanıcının kendi dik
  oturuş "baş yüksekliği" oranı oturum boyunca öğrenilir; öne eğiklik bu kişisel
  tabana göre değerlendirilir. Böylece farklı kamera açıları yüzünden düzgün
  postür yanlışlıkla "kötü" sayılmaz.
* **EMA yumuşatma:** tek karelik gürültü iyi↔kötü sıçraması yaratmaz.

Bu dosya saf Python + math'tir (ML/numpy gerektirmez), bu yüzden kolayca test
edilir; ağır YOLO/MediaPipe katmanından bağımsızdır.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Literal

from app.core.config import settings

# COCO keypoint indeksleri (üst gövde)
_NOSE = 0
_LEFT_EYE = 1
_RIGHT_EYE = 2
_LEFT_EAR = 3
_RIGHT_EAR = 4
_LEFT_SHOULDER = 5
_RIGHT_SHOULDER = 6

# Ceza ağırlıkları — her bir bozukluk türünün skordan düşebileceği maksimum puan.
# (Toplam 100'ü aşabilir; skor [0,100] aralığına kırpılır.)
_W_FORWARD = 55.0    # öne eğik baş / kamburluk — en önemli gösterge
_W_LATERAL = 40.0    # gövdeyi yana yatırma
_W_SHOULDER = 38.0   # omuz eğikliği (asimetri)
_W_ROLL = 22.0       # başı yana eğme
_W_PROXIMITY = 34.0  # ekrana çok yaklaşma
_W_HEAD_DOWN = 35.0  # başı aşağı eğme (ekrana/masaya bakma)

PostureCategory = Literal[
    "good", "forward_head", "leaning", "uneven_shoulders",
    "head_tilt", "too_close", "head_down", "unknown",
]

# Kategori → Türkçe, eyleme dönük öneri.
_CATEGORY_REASON: dict[str, str] = {
    "good": "Postürün düzgün.",
    "forward_head": "Başın öne kaymış — başını omuzlarının üzerine al, sırtını dikleştir.",
    "leaning": "Gövden bir yana yatmış — dik otur ve ağırlığını ortala.",
    "uneven_shoulders": "Omuzların eğik — iki omzunu aynı hizaya getir.",
    "head_tilt": "Başın yana eğik — başını dikleştir.",
    "too_close": "Ekrana çok yaklaşmışsın — biraz geriye yaslan.",
    "head_down": "Başın aşağı eğik — ekranı göz hizasına getir, çeneni geri çek.",
    "unknown": "Postür değerlendirmesi için omuzların net görünmüyor.",
}


@dataclass
class PostureMetrics:
    """Bir kareye ait ham postür geometrisi (piksel uzayında hesaplanmış)."""

    reliable: bool = False               # omuzlar + baş referansı bulundu mu
    shoulder_width_px: float = 0.0       # ölçek normalizasyonu için omuz genişliği
    shoulder_tilt_deg: float = 0.0       # omuz hattının yataydan sapması
    forward_head_ratio: float = 0.0      # (omuz_orta.y - baş.y) / omuz_genişliği
    lateral_offset: float = 0.0          # işaretli: baş x sapması / omuz genişliği
    neck_inclination_deg: float = 0.0    # boyun vektörünün dikeyden sapması
    head_roll_deg: float = 0.0           # göz/kulak hattının yataydan sapması
    head_down_ratio: float = 0.0         # (burun.y - kulak_orta.y) / omuz_genişliği
    proximity_ratio: float = 0.0         # omuz_genişliği / kare_genişliği


@dataclass
class PostureVerdict:
    """Postür değerlendirmesinin nihai çıktısı."""

    state: Literal["good", "poor", "unknown"] = "unknown"
    score: int = 100                     # 0-100 (yumuşatılmış)
    confidence: float = 0.0
    category: PostureCategory = "unknown"
    reason: str = ""
    is_slouching: bool = False
    reliable: bool = False
    components: dict[str, float] = field(default_factory=dict)  # ceza dökümü


# ──────────────────────────────────────────────────────────────────────────
# Saf yardımcılar (rampa fonksiyonları)
# ──────────────────────────────────────────────────────────────────────────

def _ramp_up(value: float, good: float, bad: float) -> float:
    """value <= good → 0, value >= bad → 1, arası doğrusal. (büyük = kötü)"""
    if bad <= good:
        return 0.0
    if value <= good:
        return 0.0
    if value >= bad:
        return 1.0
    return (value - good) / (bad - good)


def _ramp_down(value: float, good: float, bad: float) -> float:
    """value >= good → 0, value <= bad → 1, arası doğrusal. (küçük = kötü)"""
    if good <= bad:
        return 0.0
    if value >= good:
        return 0.0
    if value <= bad:
        return 1.0
    return (good - value) / (good - bad)


def poor_score_for_sensitivity(sensitivity: str | None) -> int:
    """Kullanıcının hassasiyet ayarını postür "poor" eşiğine çevirir.

    Yüksek hassasiyet = daha erken uyarı = daha yüksek eşik (skor daha kolay
    eşiğin altına düşer). Düşük = daha hoşgörülü. Varsayılan (None/MEDIUM) =
    yapılandırılmış ``posture_poor_score``.
    """
    base = settings.posture_poor_score
    key = (sensitivity or "MEDIUM").strip().upper()
    if key == "HIGH":
        return min(95, base + 10)
    if key == "LOW":
        return max(40, base - 10)
    return base


def _line_angle_from_horizontal(p1: tuple[float, float], p2: tuple[float, float]) -> float:
    """İki nokta arasındaki çizginin yataydan sapması (0-90°)."""
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    ang = abs(math.degrees(math.atan2(dy, dx)))
    if ang > 90.0:
        ang = 180.0 - ang
    return ang


# ──────────────────────────────────────────────────────────────────────────
# Geometri çıkarımı
# ──────────────────────────────────────────────────────────────────────────

def compute_metrics_from_pixels(
    points: list[tuple[float, float] | None],
    frame_w: int,
    frame_h: int,
) -> PostureMetrics:
    """COCO üst-gövde keypoint'lerinden (piksel) postür metriklerini hesaplar.

    *points*: en az 7 elemanlı liste; her eleman (x_px, y_px) ya da görünmüyorsa
    None. (0=burun, 1/2=gözler, 3/4=kulaklar, 5/6=omuzlar.)
    """
    if len(points) < 7:
        return PostureMetrics(reliable=False)

    ls = points[_LEFT_SHOULDER]
    rs = points[_RIGHT_SHOULDER]
    # Omuzlar olmadan postür değerlendirilemez.
    if ls is None or rs is None:
        return PostureMetrics(reliable=False)

    sw = math.hypot(rs[0] - ls[0], rs[1] - ls[1])
    if sw < 1e-3:
        return PostureMetrics(reliable=False)

    sm = ((ls[0] + rs[0]) / 2.0, (ls[1] + rs[1]) / 2.0)   # omuz orta noktası

    # Baş referansı: kulak ortası > göz ortası > burun (kararlılık sırası).
    le, re = points[_LEFT_EAR], points[_RIGHT_EAR]
    lye, rye = points[_LEFT_EYE], points[_RIGHT_EYE]
    nose = points[_NOSE]

    ear_mid = ((le[0] + re[0]) / 2.0, (le[1] + re[1]) / 2.0) if (le and re) else None
    eye_mid = ((lye[0] + rye[0]) / 2.0, (lye[1] + rye[1]) / 2.0) if (lye and rye) else None
    head = ear_mid or eye_mid or nose
    if head is None:
        return PostureMetrics(reliable=False)

    # Omuz eğikliği (yataydan sapma).
    shoulder_tilt = _line_angle_from_horizontal(ls, rs)

    # Öne eğik baş: başın omuz üstündeki dikey yüksekliği / omuz genişliği.
    # (y aşağı yönlü → baş yukarıda iken sm.y - head.y > 0.) Küçülmesi kamburluğu
    # gösterir.
    forward_head_ratio = (sm[1] - head[1]) / sw

    # Yana yatma: başın omuz ortasından yatay sapması (işaretli).
    lateral_offset = (head[0] - sm[0]) / sw

    # Boyun eğimi: boyun vektörünün dikeyden sapması (geriye dönük "spine_tilt").
    rise = max(sm[1] - head[1], 1e-3)
    neck_inclination = math.degrees(math.atan2(abs(head[0] - sm[0]), rise))

    # Baş roll: göz hattı (yoksa kulak hattı) yataydan ne kadar eğik.
    if lye and rye:
        head_roll = _line_angle_from_horizontal(lye, rye)
    elif le and re:
        head_roll = _line_angle_from_horizontal(le, re)
    else:
        head_roll = 0.0

    # Başı aşağı eğme: burun, kulak hattının ne kadar altına düşmüş.
    if ear_mid is not None and nose is not None:
        head_down_ratio = (nose[1] - ear_mid[1]) / sw
    else:
        head_down_ratio = 0.0

    proximity_ratio = sw / max(frame_w, 1)

    return PostureMetrics(
        reliable=True,
        shoulder_width_px=round(sw, 2),
        shoulder_tilt_deg=round(shoulder_tilt, 2),
        forward_head_ratio=round(forward_head_ratio, 4),
        lateral_offset=round(lateral_offset, 4),
        neck_inclination_deg=round(neck_inclination, 2),
        head_roll_deg=round(head_roll, 2),
        head_down_ratio=round(head_down_ratio, 4),
        proximity_ratio=round(proximity_ratio, 4),
    )


# ──────────────────────────────────────────────────────────────────────────
# Puanlama
# ──────────────────────────────────────────────────────────────────────────

def score_metrics(
    metrics: PostureMetrics,
    *,
    baseline_ratio: float | None = None,
    face_pitch: float | None = None,
) -> tuple[int, PostureCategory, dict[str, float]]:
    """Metriklerden 0-100 postür skoru + baskın bozukluk kategorisini üretir.

    *baseline_ratio*: kullanıcının kişisel dik-oturuş baş yüksekliği tabanı.
    Verilirse öne eğiklik mutlak eşik yerine bu tabana göre değerlendirilir.
    *face_pitch*: MediaPipe baş eğim açısı (varsa head-down sinyalini güçlendirir).
    """
    if not metrics.reliable:
        return 100, "unknown", {}

    cfg = settings

    # Öne eğik baş eşiği — kişisel tabana göre uyarlanır (taban yoksa mutlak).
    effective_good = cfg.posture_forward_good
    if baseline_ratio is not None:
        # Kullanıcı kendi dik tabanının %80'inin altına inerse cezalanmaya başlar.
        adaptive = baseline_ratio * 0.80
        effective_good = max(cfg.posture_forward_bad + 0.05, min(0.75, adaptive))

    p_forward = _ramp_down(metrics.forward_head_ratio, effective_good, cfg.posture_forward_bad) * _W_FORWARD
    p_lateral = _ramp_up(abs(metrics.lateral_offset), cfg.posture_lateral_good, cfg.posture_lateral_bad) * _W_LATERAL
    p_shoulder = _ramp_up(metrics.shoulder_tilt_deg, cfg.posture_shoulder_good_deg, cfg.posture_shoulder_bad_deg) * _W_SHOULDER
    p_roll = _ramp_up(metrics.head_roll_deg, cfg.posture_roll_good_deg, cfg.posture_roll_bad_deg) * _W_ROLL
    p_prox = _ramp_up(metrics.proximity_ratio, cfg.posture_proximity_close, cfg.posture_proximity_max) * _W_PROXIMITY

    head_down = _ramp_up(metrics.head_down_ratio, cfg.posture_head_down_good, cfg.posture_head_down_bad)
    # Yüz pitch'i aşağı bakışı doğruluyorsa head-down sinyalini güçlendir
    # (solvePnP işaret belirsizliğine karşı yalnızca büyüklük teyit edici olarak).
    if face_pitch is not None and abs(face_pitch) > 22.0:
        head_down = max(head_down, min(1.0, (abs(face_pitch) - 22.0) / 28.0))
    p_head_down = head_down * _W_HEAD_DOWN

    components = {
        "forward_head": round(p_forward, 2),
        "leaning": round(p_lateral, 2),
        "uneven_shoulders": round(p_shoulder, 2),
        "head_tilt": round(p_roll, 2),
        "too_close": round(p_prox, 2),
        "head_down": round(p_head_down, 2),
    }

    total_penalty = sum(components.values())
    score = int(round(max(0.0, min(100.0, 100.0 - total_penalty))))

    # Baskın kategori = en yüksek cezayı veren bozukluk.
    category: PostureCategory = "good"
    if total_penalty > 0:
        dominant = max(components.items(), key=lambda kv: kv[1])
        if dominant[1] >= 1.0:  # ihmal edilebilir cezaları yok say
            category = dominant[0]  # type: ignore[assignment]

    return score, category, components


# ──────────────────────────────────────────────────────────────────────────
# Oturum-farkında değerlendirici (taban çizgisi + yumuşatma)
# ──────────────────────────────────────────────────────────────────────────

@dataclass
class _PostureSessionState:
    baseline_ratio: float = 0.0          # öğrenilen dik-oturuş baş yüksekliği
    smoothed_score: float | None = None  # EMA skoru
    last_seen: datetime = field(default_factory=lambda: datetime.now(tz=timezone.utc))


class PostureEvaluator:
    """Oturum başına taban çizgisi öğrenir ve skoru yumuşatır.

    ``BehaviorStateStore`` ile aynı desende: session_id ile anahtarlanan
    hafif durum; ``expiry_minutes`` hareketsizlikten sonra temizlenir.
    """

    _BASELINE_DECAY = 0.995              # taban çizgisi yavaş "unutma" katsayısı
    _BASELINE_MIN = 0.35
    _BASELINE_MAX = 1.20

    def __init__(self, expiry_minutes: int = 30) -> None:
        self._expiry = timedelta(minutes=expiry_minutes)
        self._states: dict[str, _PostureSessionState] = {}

    def evaluate(
        self,
        session_id: str,
        metrics: PostureMetrics | None,
        *,
        captured_at: datetime,
        face_pitch: float | None = None,
        poor_score: int | None = None,
    ) -> PostureVerdict:
        self._cleanup(captured_at)

        # Pose hiç yok → değerlendirilemez.
        if metrics is None or not metrics.reliable:
            state = "unknown"
            return PostureVerdict(
                state="unknown",
                score=100,
                confidence=0.0,
                category="unknown",
                reason=_CATEGORY_REASON["unknown"],
                is_slouching=False,
                reliable=False,
            )

        st = self._states.setdefault(session_id, _PostureSessionState())
        st.last_seen = captured_at

        # Taban çizgisini güncelle: yavaş unutan koşan-maksimum. Kullanıcının en
        # dik oturuşunu yakalar; kamera/oturuş kalıcı değişirse yavaşça uyum sağlar.
        decayed = st.baseline_ratio * self._BASELINE_DECAY
        st.baseline_ratio = max(metrics.forward_head_ratio, decayed)
        st.baseline_ratio = max(self._BASELINE_MIN, min(self._BASELINE_MAX, st.baseline_ratio))
        baseline = st.baseline_ratio if st.baseline_ratio > self._BASELINE_MIN else None

        raw_score, category, components = score_metrics(
            metrics, baseline_ratio=baseline, face_pitch=face_pitch,
        )

        # EMA yumuşatma.
        alpha = settings.posture_smoothing_alpha
        if st.smoothed_score is None:
            st.smoothed_score = float(raw_score)
        else:
            st.smoothed_score = alpha * raw_score + (1.0 - alpha) * st.smoothed_score
        smoothed = int(round(st.smoothed_score))

        threshold = poor_score if poor_score is not None else settings.posture_poor_score
        poor = smoothed < threshold
        state = "poor" if poor else "good"
        # Kötü ise eşiğe uzaklıkla, iyi ise skorla orantılı güven.
        if poor:
            confidence = round(min(1.0, (threshold - smoothed) / max(threshold, 1)), 4)
        else:
            confidence = round(smoothed / 100.0, 4)

        # İyi durumda kategori "good"; kötüde baskın bozukluk.
        if not poor:
            category = "good"
        reason = _CATEGORY_REASON.get(category, _CATEGORY_REASON["unknown"])

        return PostureVerdict(
            state=state,
            score=smoothed,
            confidence=confidence,
            category=category,
            reason=reason,
            is_slouching=poor,
            reliable=True,
            components=components,
        )

    def _cleanup(self, now: datetime) -> None:
        expired = [sid for sid, s in self._states.items() if (now - s.last_seen) > self._expiry]
        for sid in expired:
            self._states.pop(sid, None)
