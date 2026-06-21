"""Tests for Module A: VisionFaceAuth — registration, identification, deletion."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pytest

from app.services.vision.vision_face_auth import (
    VisionFaceAuth,
    _AUTH_THRESHOLD,
    _MIN_FRAMES_TO_REGISTER,
    _MAX_FRAMES_PER_USER,
    _OWNER_ID_THRESHOLD,
    _OWNER_EARLY_EXIT_THRESHOLD,
)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _blank_image(h: int = 64, w: int = 64) -> np.ndarray:
    return np.zeros((h, w, 3), dtype=np.uint8)


def _unit_vec(dim: int = 128, direction: int = 0, sign: float = 1.0) -> np.ndarray:
    """Return a unit vector in a given dimension."""
    v = np.zeros(dim, dtype=np.float32)
    v[direction] = sign
    return v


def _write_profile(user_dir: Path, embeddings: np.ndarray) -> None:
    user_dir.mkdir(parents=True, exist_ok=True)
    np.save(str(user_dir / "face_embeddings.npy"), embeddings)


# ─────────────────────────────────────────────────────────────────────────────
# 1. Registration
# ─────────────────────────────────────────────────────────────────────────────

def test_register_frame_fails_gracefully_when_deepface_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import app.services.vision.vision_face_auth as m
    monkeypatch.setattr(m, "_DEEPFACE_AVAILABLE", False)
    auth = VisionFaceAuth()
    assert auth.register_frame("user1", _blank_image()) is False


def test_register_frame_appends_embedding(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import app.services.vision.vision_face_auth as m
    monkeypatch.setattr(m, "_DATA_ROOT", tmp_path)
    monkeypatch.setattr(m, "_DEEPFACE_AVAILABLE", True)

    embedding = _unit_vec()

    class FakeDeepFace:
        @staticmethod
        def represent(**_: Any) -> list[dict]:
            # Gerçekçi (görüntü içinde, tam kareyi kaplamayan) yüz kutusu →
            # _is_real_face guard'ını geçer (kayıtta gerçek yüz zorunlu).
            return [{"embedding": embedding.tolist(), "facial_area": {"x": 8, "y": 8, "w": 30, "h": 40}}]

    monkeypatch.setattr(m, "DeepFace", FakeDeepFace, raising=False)
    auth = VisionFaceAuth()

    result = auth.register_frame("user1", _blank_image())
    assert result is True
    assert auth.frame_count("user1") == 1

    # Second registration appends
    auth.register_frame("user1", _blank_image())
    assert auth.frame_count("user1") == 2


def test_register_frame_caps_at_max_frames(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import app.services.vision.vision_face_auth as m
    monkeypatch.setattr(m, "_DATA_ROOT", tmp_path)
    monkeypatch.setattr(m, "_DEEPFACE_AVAILABLE", True)
    cap = 5
    monkeypatch.setattr(m, "_MAX_FRAMES_PER_USER", cap)

    embedding = _unit_vec()

    class FakeDeepFace:
        @staticmethod
        def represent(**_: Any) -> list[dict]:
            # Gerçekçi (görüntü içinde, tam kareyi kaplamayan) yüz kutusu →
            # _is_real_face guard'ını geçer (kayıtta gerçek yüz zorunlu).
            return [{"embedding": embedding.tolist(), "facial_area": {"x": 8, "y": 8, "w": 30, "h": 40}}]

    monkeypatch.setattr(m, "DeepFace", FakeDeepFace, raising=False)
    auth = VisionFaceAuth()

    for _ in range(cap + 3):
        auth.register_frame("u2", _blank_image())

    assert auth.frame_count("u2") == cap


# ─────────────────────────────────────────────────────────────────────────────
# 2. has_profile / frame_count
# ─────────────────────────────────────────────────────────────────────────────

def test_has_profile_false_when_no_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import app.services.vision.vision_face_auth as m
    monkeypatch.setattr(m, "_DATA_ROOT", tmp_path)
    auth = VisionFaceAuth()
    assert auth.has_profile("nobody") is False
    assert auth.frame_count("nobody") == 0


def test_has_profile_false_below_min_frames(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import app.services.vision.vision_face_auth as m
    monkeypatch.setattr(m, "_DATA_ROOT", tmp_path)
    monkeypatch.setattr(m, "_MIN_FRAMES_TO_REGISTER", 3)

    user_dir = tmp_path / "partial"
    _write_profile(user_dir, np.random.randn(2, 128).astype(np.float32))

    auth = VisionFaceAuth()
    assert auth.has_profile("partial") is False


def test_has_profile_true_at_min_frames(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import app.services.vision.vision_face_auth as m
    monkeypatch.setattr(m, "_DATA_ROOT", tmp_path)
    monkeypatch.setattr(m, "_MIN_FRAMES_TO_REGISTER", 3)

    user_dir = tmp_path / "ready"
    _write_profile(user_dir, np.random.randn(3, 128).astype(np.float32))

    auth = VisionFaceAuth()
    assert auth.has_profile("ready") is True


# ─────────────────────────────────────────────────────────────────────────────
# 3. verify (legacy full-image auth)
# ─────────────────────────────────────────────────────────────────────────────

def test_verify_fails_when_deepface_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import app.services.vision.vision_face_auth as m
    monkeypatch.setattr(m, "_DEEPFACE_AVAILABLE", False)
    auth = VisionFaceAuth()
    result = auth.verify("u", _blank_image())
    assert result.authenticated is False
    assert result.error is not None


def test_verify_fails_with_no_profile(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import app.services.vision.vision_face_auth as m
    monkeypatch.setattr(m, "_DATA_ROOT", tmp_path)
    monkeypatch.setattr(m, "_DEEPFACE_AVAILABLE", True)
    auth = VisionFaceAuth()
    result = auth.verify("ghost", _blank_image())
    assert result.authenticated is False


# ─────────────────────────────────────────────────────────────────────────────
# 4. identify_owner — multi-face owner matching
# ─────────────────────────────────────────────────────────────────────────────

def test_identify_owner_matches_owner_single_face(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import app.services.vision.vision_face_auth as m
    monkeypatch.setattr(m, "_DATA_ROOT", tmp_path)
    monkeypatch.setattr(m, "_DEEPFACE_AVAILABLE", True)
    monkeypatch.setattr(m, "_MIN_FRAMES_TO_REGISTER", 1)
    # Similarity threshold: cosine sim of unit vectors pointing same direction = 1.0
    monkeypatch.setattr(m, "_OWNER_ID_THRESHOLD", 0.75)

    owner_emb = _unit_vec(direction=0, sign=1.0)
    _write_profile(tmp_path / "owner", np.array([owner_emb]))

    class FakeDeepFace:
        @staticmethod
        def represent(**_: Any) -> list[dict]:
            return [{"embedding": owner_emb.tolist(), "facial_area": {"x": 10, "y": 10, "w": 80, "h": 80}}]

    monkeypatch.setattr(m, "DeepFace", FakeDeepFace, raising=False)

    auth = VisionFaceAuth()
    result = auth.identify_owner("owner", _blank_image())
    assert result.owner_found is True
    assert result.owner_confidence >= 0.75
    assert result.total_faces == 1
    assert result.strangers_count == 0


def test_identify_owner_no_match_returns_all_as_strangers(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import app.services.vision.vision_face_auth as m
    monkeypatch.setattr(m, "_DATA_ROOT", tmp_path)
    monkeypatch.setattr(m, "_DEEPFACE_AVAILABLE", True)
    monkeypatch.setattr(m, "_MIN_FRAMES_TO_REGISTER", 1)

    owner_emb = _unit_vec(direction=0, sign=1.0)
    stranger_emb = _unit_vec(direction=0, sign=-1.0)  # maximally dissimilar
    _write_profile(tmp_path / "owner2", np.array([owner_emb]))

    class FakeDeepFace:
        @staticmethod
        def represent(**_: Any) -> list[dict]:
            return [{"embedding": stranger_emb.tolist(), "facial_area": {"x": 0, "y": 0, "w": 50, "h": 50}}]

    monkeypatch.setattr(m, "DeepFace", FakeDeepFace, raising=False)

    auth = VisionFaceAuth()
    result = auth.identify_owner("owner2", _blank_image())
    assert result.owner_found is False
    assert result.total_faces == 1
    assert result.strangers_count == 1


def test_identify_owner_early_exit_on_high_confidence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import app.services.vision.vision_face_auth as m
    monkeypatch.setattr(m, "_DATA_ROOT", tmp_path)
    monkeypatch.setattr(m, "_DEEPFACE_AVAILABLE", True)
    monkeypatch.setattr(m, "_MIN_FRAMES_TO_REGISTER", 1)
    monkeypatch.setattr(m, "_OWNER_EARLY_EXIT_THRESHOLD", 0.90)

    owner_emb = _unit_vec(direction=0, sign=1.0)
    _write_profile(tmp_path / "earlyexit", np.array([owner_emb]))

    class FakeDeepFace:
        @staticmethod
        def represent(**_: Any) -> list[dict]:
            # Single face, same embedding → similarity = 1.0 (mapped from cosine)
            return [{"embedding": owner_emb.tolist(), "facial_area": {"x": 5, "y": 5, "w": 60, "h": 60}}]

    monkeypatch.setattr(m, "DeepFace", FakeDeepFace, raising=False)

    auth = VisionFaceAuth()
    result = auth.identify_owner("earlyexit", _blank_image())
    assert result.owner_found is True
    assert result.owner_confidence >= 0.90


# ─────────────────────────────────────────────────────────────────────────────
# 5. delete_profile
# ─────────────────────────────────────────────────────────────────────────────

def test_delete_profile_removes_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import app.services.vision.vision_face_auth as m
    monkeypatch.setattr(m, "_DATA_ROOT", tmp_path)
    monkeypatch.setattr(m, "_MIN_FRAMES_TO_REGISTER", 1)

    user_dir = tmp_path / "todelete"
    _write_profile(user_dir, np.random.randn(3, 128).astype(np.float32))

    auth = VisionFaceAuth()
    assert auth.has_profile("todelete") is True

    deleted = auth.delete_profile("todelete")
    assert deleted is True
    assert auth.has_profile("todelete") is False


def test_delete_profile_returns_false_when_no_profile(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import app.services.vision.vision_face_auth as m
    monkeypatch.setattr(m, "_DATA_ROOT", tmp_path)

    auth = VisionFaceAuth()
    assert auth.delete_profile("nobody") is False


# ─────────────────────────────────────────────────────────────────────────────
# 6. Path sanitisation (security — path traversal prevention)
# ─────────────────────────────────────────────────────────────────────────────

def test_profile_path_sanitises_user_id(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import app.services.vision.vision_face_auth as m
    monkeypatch.setattr(m, "_DATA_ROOT", tmp_path)

    auth = VisionFaceAuth()
    # Path traversal attempt — should be stripped to safe characters
    auth.delete_profile("../../../etc/passwd")
    # No exception means sanitisation didn't crash; the traversal was neutralised
    assert auth.frame_count("../../../etc/passwd") == 0


# ─────────────────────────────────────────────────────────────────────────────
# 7. Faz A — multi-face: registration/verification picks the LARGEST face,
#    not whichever DeepFace returns first (avoids enrolling a stranger).
# ─────────────────────────────────────────────────────────────────────────────

def test_largest_face_picks_biggest_area() -> None:
    faces = [
        {"embedding": [1.0], "facial_area": {"x": 0, "y": 0, "w": 10, "h": 10}},
        {"embedding": [2.0], "facial_area": {"x": 0, "y": 0, "w": 50, "h": 40}},  # biggest
        {"embedding": [3.0], "facial_area": {"x": 0, "y": 0, "w": 20, "h": 20}},
    ]
    assert VisionFaceAuth._largest_face(faces)["embedding"] == [2.0]


def test_largest_face_empty_returns_none() -> None:
    assert VisionFaceAuth._largest_face([]) is None


def test_largest_face_missing_area_does_not_crash() -> None:
    faces = [{"embedding": [1.0]}, {"embedding": [2.0]}]  # no facial_area → area 0
    assert VisionFaceAuth._largest_face(faces) is not None


def test_register_frame_enrolls_largest_face_not_first(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """İki yüz varsa kayıt, listedeki ilk (küçük/yabancı) yüzü değil en büyük
    (öndeki/sahip) yüzü kaydetmeli."""
    import app.services.vision.vision_face_auth as m
    monkeypatch.setattr(m, "_DATA_ROOT", tmp_path)
    monkeypatch.setattr(m, "_DEEPFACE_AVAILABLE", True)

    small_stranger = _unit_vec(direction=1, sign=1.0)  # ilk sırada, küçük alan
    large_owner = _unit_vec(direction=0, sign=1.0)      # ikinci sırada, en büyük alan

    class FakeDeepFace:
        @staticmethod
        def represent(**_: Any) -> list[dict]:
            # Her iki kutu da 64x64 görüntü içinde ve tam kareyi kaplamıyor
            # (_is_real_face guard'ını geçer); büyük olan "owner" en geniş alan.
            return [
                {"embedding": small_stranger.tolist(), "facial_area": {"x": 0, "y": 0, "w": 12, "h": 12}},
                {"embedding": large_owner.tolist(), "facial_area": {"x": 20, "y": 20, "w": 40, "h": 40}},
            ]

    monkeypatch.setattr(m, "DeepFace", FakeDeepFace, raising=False)
    auth = VisionFaceAuth()

    assert auth.register_frame("multi", _blank_image()) is True
    stored = np.load(str(tmp_path / "multi" / "face_embeddings.npy"))
    assert stored.shape[0] == 1
    # Kaydedilen embedding büyük (sahip) yüz olmalı: onunla kosinüs ~1, yabancıyla ~0.
    assert float(stored[0] @ large_owner) > 0.99
    assert abs(float(stored[0] @ small_stranger)) < 0.01
