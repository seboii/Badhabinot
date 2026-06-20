"""Çok-sinyalli postür değerlendirmesi — saf geometri + puanlama + oturum mantığı.

Ağır ML (YOLO/MediaPipe) çalıştırmadan, ``vision_posture`` çekirdeğini test eder.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.core.config import settings
from app.services.vision.vision_posture import (
    PostureEvaluator,
    PostureMetrics,
    compute_metrics_from_pixels,
    poor_score_for_sensitivity,
    score_metrics,
)

_FRAME_W = 640
_FRAME_H = 480


def _t(sec: int) -> datetime:
    return datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(seconds=sec)


def _points(
    *,
    shoulders: tuple[tuple[float, float], tuple[float, float]],
    ears: tuple[tuple[float, float], tuple[float, float]] | None,
    eyes: tuple[tuple[float, float], tuple[float, float]] | None = None,
    nose: tuple[float, float] | None = None,
) -> list[tuple[float, float] | None]:
    """17 elemanlı COCO piksel-nokta listesi kurar (kullanılmayanlar None)."""
    pts: list[tuple[float, float] | None] = [None] * 17
    pts[0] = nose
    if eyes:
        pts[1], pts[2] = eyes
    if ears:
        pts[3], pts[4] = ears
    pts[5], pts[6] = shoulders
    return pts


def _upright_points() -> list[tuple[float, float] | None]:
    # Omuzlar düz, baş omuzların üstünde, göz hattı yatay.
    return _points(
        shoulders=((220, 300), (420, 300)),
        ears=((290, 180), (350, 180)),
        eyes=((300, 175), (340, 175)),
        nose=(320, 200),
    )


# ── compute_metrics_from_pixels ──────────────────────────────────────────────

def test_metrics_unreliable_without_shoulders() -> None:
    pts = _points(shoulders=((0, 0), (0, 0)), ears=((290, 180), (350, 180)))
    pts[5] = None  # sol omuz yok
    m = compute_metrics_from_pixels(pts, _FRAME_W, _FRAME_H)
    assert m.reliable is False


def test_metrics_upright_is_reliable_and_balanced() -> None:
    m = compute_metrics_from_pixels(_upright_points(), _FRAME_W, _FRAME_H)
    assert m.reliable is True
    assert m.forward_head_ratio > 0.5         # baş omuzların belirgin üstünde
    assert abs(m.lateral_offset) < 0.05       # ortalanmış
    assert m.shoulder_tilt_deg < 4.0          # omuzlar düz
    assert m.head_roll_deg < 4.0              # baş düz


# ── score_metrics ────────────────────────────────────────────────────────────

def test_score_upright_is_good() -> None:
    m = compute_metrics_from_pixels(_upright_points(), _FRAME_W, _FRAME_H)
    score, category, _ = score_metrics(m)
    assert score >= settings.posture_poor_score
    assert category == "good"


def test_score_forward_head_is_poor() -> None:
    m = PostureMetrics(
        reliable=True, shoulder_width_px=200, shoulder_tilt_deg=2.0,
        forward_head_ratio=0.15, lateral_offset=0.0, neck_inclination_deg=5.0,
        head_roll_deg=2.0, head_down_ratio=0.1, proximity_ratio=0.31,
    )
    score, category, _ = score_metrics(m)
    assert score < settings.posture_poor_score
    assert category == "forward_head"


def test_score_leaning_is_poor() -> None:
    m = PostureMetrics(
        reliable=True, shoulder_width_px=200, shoulder_tilt_deg=2.0,
        forward_head_ratio=0.6, lateral_offset=0.5, neck_inclination_deg=20.0,
        head_roll_deg=2.0, head_down_ratio=0.1, proximity_ratio=0.31,
    )
    score, category, _ = score_metrics(m)
    assert score < settings.posture_poor_score
    assert category == "leaning"


def test_score_uneven_shoulders_is_poor() -> None:
    m = PostureMetrics(
        reliable=True, shoulder_width_px=200, shoulder_tilt_deg=20.0,
        forward_head_ratio=0.6, lateral_offset=0.0, neck_inclination_deg=5.0,
        head_roll_deg=2.0, head_down_ratio=0.1, proximity_ratio=0.31,
    )
    score, category, _ = score_metrics(m)
    assert score < settings.posture_poor_score
    assert category == "uneven_shoulders"


def test_score_too_close_is_poor() -> None:
    m = PostureMetrics(
        reliable=True, shoulder_width_px=540, shoulder_tilt_deg=2.0,
        forward_head_ratio=0.6, lateral_offset=0.0, neck_inclination_deg=5.0,
        head_roll_deg=2.0, head_down_ratio=0.1, proximity_ratio=0.86,
    )
    score, category, _ = score_metrics(m)
    assert score < settings.posture_poor_score
    assert category == "too_close"


def test_score_unreliable_returns_unknown() -> None:
    score, category, comps = score_metrics(PostureMetrics(reliable=False))
    assert category == "unknown"
    assert comps == {}


# ── PostureEvaluator (oturum: taban çizgisi + yumuşatma) ──────────────────────

def test_evaluator_good_posture_stays_good() -> None:
    ev = PostureEvaluator()
    m = compute_metrics_from_pixels(_upright_points(), _FRAME_W, _FRAME_H)
    verdict = ev.evaluate("s-good", m, captured_at=_t(0))
    assert verdict.state == "good"
    assert verdict.reliable is True
    assert verdict.is_slouching is False


def test_evaluator_none_metrics_is_unknown() -> None:
    ev = PostureEvaluator()
    verdict = ev.evaluate("s-none", None, captured_at=_t(0))
    assert verdict.state == "unknown"
    assert verdict.reliable is False


def test_evaluator_sustained_slouch_becomes_poor() -> None:
    ev = PostureEvaluator()
    slouch = PostureMetrics(
        reliable=True, shoulder_width_px=200, shoulder_tilt_deg=2.0,
        forward_head_ratio=0.15, lateral_offset=0.0, neck_inclination_deg=5.0,
        head_roll_deg=2.0, head_down_ratio=0.1, proximity_ratio=0.31,
    )
    states = [ev.evaluate("s-slouch", slouch, captured_at=_t(i)).state for i in range(4)]
    assert states[-1] == "poor"


def test_poor_score_for_sensitivity_ordering() -> None:
    low = poor_score_for_sensitivity("LOW")
    med = poor_score_for_sensitivity("MEDIUM")
    high = poor_score_for_sensitivity("HIGH")
    assert low < med < high
    assert poor_score_for_sensitivity(None) == med
    assert poor_score_for_sensitivity("medium") == med  # büyük/küçük harf duyarsız


def test_high_sensitivity_flags_borderline_posture_as_poor() -> None:
    """Aynı sınırda postür: yüksek hassasiyet 'poor', düşük hassasiyet 'good' demeli."""
    # Hafif öne eğik baş — orta eşikte sınırda kalan bir kare.
    borderline = PostureMetrics(
        reliable=True, shoulder_width_px=200, shoulder_tilt_deg=2.0,
        forward_head_ratio=0.34, lateral_offset=0.0, neck_inclination_deg=10.0,
        head_roll_deg=2.0, head_down_ratio=0.1, proximity_ratio=0.31,
    )
    high_ev = PostureEvaluator()
    low_ev = PostureEvaluator()
    high = high_ev.evaluate("s-h", borderline, captured_at=_t(0),
                            poor_score=poor_score_for_sensitivity("HIGH"))
    low = low_ev.evaluate("s-l", borderline, captured_at=_t(0),
                          poor_score=poor_score_for_sensitivity("LOW"))
    assert high.state == "poor"
    assert low.state == "good"


def test_evaluator_single_bad_frame_does_not_flip_after_good_run() -> None:
    """EMA yumuşatma: uzun iyi seriden sonra tek kötü kare durumu kötüye çevirmemeli."""
    ev = PostureEvaluator()
    good = compute_metrics_from_pixels(_upright_points(), _FRAME_W, _FRAME_H)
    for i in range(6):
        ev.evaluate("s-ema", good, captured_at=_t(i))

    bad = PostureMetrics(
        reliable=True, shoulder_width_px=200, shoulder_tilt_deg=2.0,
        forward_head_ratio=0.15, lateral_offset=0.0, neck_inclination_deg=5.0,
        head_roll_deg=2.0, head_down_ratio=0.1, proximity_ratio=0.31,
    )
    verdict = ev.evaluate("s-ema", bad, captured_at=_t(6))
    assert verdict.state == "good"  # tek karelik gürültü yumuşatıldı
