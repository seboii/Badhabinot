"""VisionAnalysisService global eşzamanlılık kilidi testi.

MediaPipe/DeepFace/YOLO thread-safe olmadığından `analyze()` aynı anda yalnızca
tek kareyi paylaşılan dedektörlerden geçirmeli. Ağır ML init'ini atlamak için
nesne ``object.__new__`` ile kurulur ve yalnızca kilit alanı set edilir.
"""
from __future__ import annotations

import asyncio

import pytest

from app.services.vision_analysis_service import VisionAnalysisService


@pytest.mark.asyncio
async def test_analyze_serializes_concurrent_calls(monkeypatch) -> None:
    service = object.__new__(VisionAnalysisService)
    service._lock = asyncio.Lock()

    active = 0
    max_active = 0

    async def fake_locked(_request, *, render_overlay: bool = False):  # noqa: ANN001
        nonlocal active, max_active
        active += 1
        max_active = max(max_active, active)
        await asyncio.sleep(0.02)  # kritik bölümü taklit et
        active -= 1
        return "ok"

    monkeypatch.setattr(service, "_analyze_locked", fake_locked)

    results = await asyncio.gather(*(service.analyze(object()) for _ in range(6)))

    assert results == ["ok"] * 6
    # Global kilit → kritik bölümde asla 1'den fazla eşzamanlı çağrı olmamalı.
    assert max_active == 1
