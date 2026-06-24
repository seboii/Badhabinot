"""verify_liveness eşik mantığı testleri (ML gerektirmeyen, sahte mesh ile).

Durağan fotoğraf (sabit EAR/yaw) reddedilmeli; göz kırpma / baş hareketi
(ve esnek geri-dönüş) kabul edilmeli.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.services.vision.vision_liveness import verify_liveness


@dataclass
class _MeshResult:
    ear: float
    yaw: float


class _FakeMesh:
    """Her analyze() çağrısında sıradaki sahte sonucu döndürür."""

    def __init__(self, results: list[_MeshResult]) -> None:
        self._results = results
        self._i = 0

    def analyze(self, _frame):  # noqa: ANN001
        r = self._results[self._i]
        self._i += 1
        return r


def _run(action: str, results: list[_MeshResult]):
    mesh = _FakeMesh(results)
    frames = [None] * len(results)  # içerik önemsiz; mesh sonucu sahte
    return verify_liveness(mesh, frames, action)


def test_blink_detected() -> None:
    # Açık göz ~0.30, ortada belirgin kapanma ~0.12
    seq = [_MeshResult(0.30, 2.0), _MeshResult(0.29, 2.0), _MeshResult(0.12, 2.0), _MeshResult(0.30, 2.0)]
    res = _run("BLINK", seq)
    assert res.passed and res.action_detected == "BLINK"


def test_turn_detected() -> None:
    # Yatay baş salınımı 2°→22°, EAR sabit
    seq = [_MeshResult(0.30, 2.0), _MeshResult(0.30, 10.0), _MeshResult(0.30, 22.0), _MeshResult(0.30, 6.0)]
    res = _run("TURN_HEAD", seq)
    assert res.passed and res.action_detected == "TURN_HEAD"


def test_static_photo_rejected() -> None:
    # Sabit EAR ve yaw → ne göz kırpma ne hareket → reddet
    seq = [_MeshResult(0.30, 3.0)] * 6
    res = _run("BLINK", seq)
    assert not res.passed
    res2 = _run("TURN_HEAD", seq)
    assert not res2.passed


def test_blink_satisfies_turn_challenge_fallback() -> None:
    # TURN_HEAD istendi ama kullanıcı göz kırptı (yaw sabit) → esnek geri-dönüşle geçer
    seq = [_MeshResult(0.30, 2.0), _MeshResult(0.11, 2.0), _MeshResult(0.30, 2.0)]
    res = _run("TURN_HEAD", seq)
    assert res.passed and res.action_detected == "BLINK"
