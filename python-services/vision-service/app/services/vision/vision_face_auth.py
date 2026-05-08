"""Module A — Face Registration & Authentication.

Stores per-user face embeddings and verifies live frames against them.
Uses DeepFace for embedding extraction (no dlib compile required).
Falls back gracefully if deepface is not installed.

Storage layout:
    data/users/{user_id}/face_embeddings.npy  — shape (N, D) float32
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)

try:
    from deepface import DeepFace  # type: ignore[import-untyped]
    _DEEPFACE_AVAILABLE = True
except ImportError:  # pragma: no cover
    _DEEPFACE_AVAILABLE = False
    logger.warning("deepface not installed — face authentication disabled")

_DATA_ROOT = Path(os.getenv("FACE_DATA_DIR", "data/users"))
_EMBED_FILENAME = "face_embeddings.npy"
_MODEL_NAME = "Facenet"          # compact & fast
_AUTH_THRESHOLD = 0.85           # cosine similarity floor to pass
_MIN_FRAMES_TO_REGISTER = 3      # minimum stored embeddings to consider profile valid
_MAX_FRAMES_PER_USER = 15        # cap to keep npy small


@dataclass
class AuthResult:
    authenticated: bool
    user_id: str
    confidence: float          # 0.0 – 1.0 cosine similarity (best match)
    frames_enrolled: int       # how many frames are in the stored profile
    error: str | None = None   # present when auth could not be run at all


class VisionFaceAuth:
    """Stateless helper — reads/writes embeddings from disk on each call."""

    # ------------------------------------------------------------------ #
    # Public API                                                           #
    # ------------------------------------------------------------------ #

    def register_frame(self, user_id: str, image: np.ndarray) -> bool:
        """Extract embedding from *image* and append it to the user's profile.

        Returns True on success, False if no face found or deepface unavailable.
        """
        if not _DEEPFACE_AVAILABLE:
            return False

        embedding = self._extract_embedding(image)
        if embedding is None:
            return False

        profile_path = self._profile_path(user_id)
        profile_path.parent.mkdir(parents=True, exist_ok=True)

        if profile_path.exists():
            existing: np.ndarray = np.load(str(profile_path))
            combined = np.vstack([existing, embedding[np.newaxis, :]])
        else:
            combined = embedding[np.newaxis, :]

        # Keep only the most recent _MAX_FRAMES_PER_USER embeddings
        if combined.shape[0] > _MAX_FRAMES_PER_USER:
            combined = combined[-_MAX_FRAMES_PER_USER:]

        np.save(str(profile_path), combined.astype(np.float32))
        logger.debug("Face registered for user=%s frames=%d", user_id, combined.shape[0])
        return True

    def verify(self, user_id: str, image: np.ndarray) -> AuthResult:
        """Verify whether the face in *image* belongs to *user_id*.

        Returns an AuthResult.  authenticated=True means confidence >= threshold
        AND the profile has at least _MIN_FRAMES_TO_REGISTER stored embeddings.
        """
        if not _DEEPFACE_AVAILABLE:
            return AuthResult(
                authenticated=False,
                user_id=user_id,
                confidence=0.0,
                frames_enrolled=0,
                error="deepface not installed",
            )

        profile_path = self._profile_path(user_id)
        if not profile_path.exists():
            return AuthResult(
                authenticated=False,
                user_id=user_id,
                confidence=0.0,
                frames_enrolled=0,
                error="no profile registered",
            )

        stored: np.ndarray = np.load(str(profile_path))  # (N, D)
        frames_enrolled = stored.shape[0]

        if frames_enrolled < _MIN_FRAMES_TO_REGISTER:
            return AuthResult(
                authenticated=False,
                user_id=user_id,
                confidence=0.0,
                frames_enrolled=frames_enrolled,
                error="profile incomplete — register more frames",
            )

        live_embedding = self._extract_embedding(image)
        if live_embedding is None:
            return AuthResult(
                authenticated=False,
                user_id=user_id,
                confidence=0.0,
                frames_enrolled=frames_enrolled,
                error="no face detected in live frame",
            )

        best_similarity = float(self._best_cosine_similarity(live_embedding, stored))
        authenticated = best_similarity >= _AUTH_THRESHOLD

        return AuthResult(
            authenticated=authenticated,
            user_id=user_id,
            confidence=round(best_similarity, 4),
            frames_enrolled=frames_enrolled,
        )

    def has_profile(self, user_id: str) -> bool:
        """Return True if the user has at least _MIN_FRAMES_TO_REGISTER enrolled frames."""
        p = self._profile_path(user_id)
        if not p.exists():
            return False
        data: np.ndarray = np.load(str(p))
        return int(data.shape[0]) >= _MIN_FRAMES_TO_REGISTER

    def frame_count(self, user_id: str) -> int:
        """Return number of stored embedding frames for a user (0 if none)."""
        p = self._profile_path(user_id)
        if not p.exists():
            return 0
        data: np.ndarray = np.load(str(p))
        return int(data.shape[0])

    def delete_profile(self, user_id: str) -> bool:
        """Delete stored face profile.  Returns True if a file was deleted."""
        p = self._profile_path(user_id)
        if p.exists():
            p.unlink()
            return True
        return False

    # ------------------------------------------------------------------ #
    # Private helpers                                                      #
    # ------------------------------------------------------------------ #

    def _extract_embedding(self, image: np.ndarray) -> np.ndarray | None:
        try:
            result = DeepFace.represent(
                img_path=image,
                model_name=_MODEL_NAME,
                enforce_detection=False,   # don't throw if face not perfectly detected
                detector_backend="opencv",  # fast
            )
            if not result:
                return None
            vec = np.array(result[0]["embedding"], dtype=np.float32)
            norm = float(np.linalg.norm(vec))
            if norm > 0:
                vec = vec / norm
            return vec
        except Exception:
            logger.debug("DeepFace embedding extraction failed", exc_info=True)
            return None

    @staticmethod
    def _best_cosine_similarity(live: np.ndarray, stored: np.ndarray) -> float:
        """Return the highest cosine similarity between *live* and any row in *stored*."""
        # both should already be L2-normalised → dot product = cosine similarity
        similarities = stored @ live  # (N,)
        best = float(np.max(similarities))
        # clamp to [0, 1] (should be already, but guard against floating point noise)
        return max(0.0, min(1.0, (best + 1.0) / 2.0))  # map [-1,1] → [0,1]

    @staticmethod
    def _profile_path(user_id: str) -> Path:
        # Sanitise user_id to avoid path traversal
        safe_id = "".join(c for c in user_id if c.isalnum() or c in "-_")
        return _DATA_ROOT / safe_id / _EMBED_FILENAME
