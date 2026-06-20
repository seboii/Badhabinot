"""Optimizasyon katmanı — kare küçültme, frame scheduler ve dedektör önbelleği."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import numpy as np
import pytest

from app.core.config import settings
from app.services.vision.vision_optimizer import (
    DetectorCache,
    FrameScheduler,
    downscale_for_inference,
)


def _t(sec: int) -> datetime:
    return datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(seconds=sec)


# ── downscale_for_inference ──────────────────────────────────────────────────

def test_downscale_shrinks_long_edge_and_keeps_aspect() -> None:
    img = np.zeros((720, 1280, 3), dtype=np.uint8)
    out = downscale_for_inference(img, max_dim=640)
    h, w = out.shape[:2]
    assert max(h, w) == 640
    # En-boy oranı korunur (yuvarlama toleransı).
    assert abs((w / h) - (1280 / 720)) < 0.01


def test_downscale_never_upscales_small_frame() -> None:
    img = np.zeros((64, 64, 3), dtype=np.uint8)
    out = downscale_for_inference(img, max_dim=640)
    assert out.shape[:2] == (64, 64)


# ── FrameScheduler ───────────────────────────────────────────────────────────

def test_scheduler_first_frame_runs_everything() -> None:
    sched = FrameScheduler()
    decision = sched.tick("s1", now=_t(0))
    assert decision.run_owner_id
    assert decision.run_objects
    assert decision.run_gaze
    assert decision.run_pose


def test_scheduler_honours_owner_interval(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "vision_owner_id_interval", 3)
    sched = FrameScheduler()
    flags = [sched.tick("s2", now=_t(i)).run_owner_id for i in range(5)]
    # index 0,3 → True ; 1,2,4 → False
    assert flags == [True, False, False, True, False]


def test_scheduler_sessions_are_independent() -> None:
    sched = FrameScheduler()
    sched.tick("a", now=_t(0))
    sched.tick("a", now=_t(1))
    # Yeni oturum sıfırdan başlar → ilk karede her şey çalışır.
    assert sched.tick("b", now=_t(2)).run_owner_id is True


# ── DetectorCache ────────────────────────────────────────────────────────────

def test_cache_persists_entry_per_session() -> None:
    cache = DetectorCache()
    entry = cache.get("s1", now=_t(0))
    entry.owner = ("x",)
    assert cache.get("s1", now=_t(1)).owner == ("x",)


def test_cache_isolates_sessions() -> None:
    cache = DetectorCache()
    cache.get("s1", now=_t(0)).objects = "obj"
    assert cache.get("s2", now=_t(0)).objects is None
