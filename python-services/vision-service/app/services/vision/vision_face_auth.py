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
except Exception as _deepface_exc:  # pragma: no cover
    # ImportError VEYA bağımlılık zinciri hatası (ör. retinaface/tf-keras uyumsuzluğu).
    # Niyet: opsiyonel deepface kullanılamıyorsa modül import'ta çökmesin, yüz
    # doğrulama zarifçe devre dışı kalsın.
    DeepFace = None  # type: ignore[assignment]
    _DEEPFACE_AVAILABLE = False
    logger.warning("deepface unavailable — face authentication disabled (%s)", _deepface_exc)

_DATA_ROOT = Path(os.getenv("FACE_DATA_DIR", "data/users"))
_EMBED_FILENAME = "face_embeddings.npy"
_MODEL_NAME = "Facenet"          # compact & fast
# Eşikler env ile ayarlanabilir → sahada yeniden derlemeden ince ayar yapılabilir.
_AUTH_THRESHOLD = float(os.getenv("FACE_AUTH_THRESHOLD", "0.85"))           # giriş/doğrulama benzerlik tabanı
_OWNER_ID_THRESHOLD = float(os.getenv("FACE_OWNER_THRESHOLD", "0.75"))      # çoklu-yüz sahip tespiti tabanı
_OWNER_EARLY_EXIT_THRESHOLD = float(os.getenv("FACE_OWNER_EARLY_EXIT", "0.90"))  # tek-yüz erken çıkış
_MIN_FRAMES_TO_REGISTER = 3      # minimum stored embeddings to consider profile valid
_MAX_FRAMES_PER_USER = 15        # cap to keep npy small


@dataclass
class OwnerFaceResult:
    """Result of multi-face owner identification."""

    owner_found: bool
    owner_bbox: tuple[int, int, int, int] | None  # (x, y, w, h) pixel coordinates
    owner_confidence: float          # 0.0 – 1.0 similarity against stored profile
    total_faces: int                 # total faces detected in the frame
    strangers_count: int             # faces that did not match the owner


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

        # Kayıtta gerçek yüz şart — yüzsüz kareler profili kirletmesin.
        embedding = self._extract_embedding(image, enforce=True)
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

    def identify_owner(self, user_id: str, image: np.ndarray) -> OwnerFaceResult:
        """Detect ALL faces in *image* and find which one belongs to *user_id*.

        For each detected face an embedding is computed and compared against
        the user's stored profile.  The face with the highest cosine similarity
        above ``_OWNER_ID_THRESHOLD`` is claimed as the owner.

        Early-exit optimisation: when exactly one face is detected and its
        similarity exceeds ``_OWNER_EARLY_EXIT_THRESHOLD`` the full multi-face
        scan is skipped and the result is returned immediately.

        Returns an :class:`OwnerFaceResult` with ``owner_found=False`` when:
        - DeepFace is not available
        - No face profile is registered for the user
        - No detected face exceeds the identification threshold
        """
        _not_found = OwnerFaceResult(
            owner_found=False,
            owner_bbox=None,
            owner_confidence=0.0,
            total_faces=0,
            strangers_count=0,
        )

        if not _DEEPFACE_AVAILABLE:
            return _not_found

        profile_path = self._profile_path(user_id)
        if not profile_path.exists():
            return _not_found

        stored: np.ndarray = np.load(str(profile_path))
        if stored.shape[0] < _MIN_FRAMES_TO_REGISTER:
            return _not_found

        try:
            results = DeepFace.represent(
                img_path=image,
                model_name=_MODEL_NAME,
                enforce_detection=False,
                detector_backend="opencv",
            )
        except Exception:
            logger.debug("DeepFace.represent failed in identify_owner", exc_info=True)
            return _not_found

        if not results:
            return _not_found

        total_faces = len(results)

        best_idx = -1
        best_confidence = 0.0

        for i, face_data in enumerate(results):
            vec = np.array(face_data["embedding"], dtype=np.float32)
            norm = float(np.linalg.norm(vec))
            if norm > 0:
                vec = vec / norm

            similarity = float(self._best_cosine_similarity(vec, stored))

            # Early-exit: single face with high confidence — skip remaining scan
            if total_faces == 1 and similarity >= _OWNER_EARLY_EXIT_THRESHOLD:
                bbox = self._extract_bbox(face_data)
                return OwnerFaceResult(
                    owner_found=True,
                    owner_bbox=bbox,
                    owner_confidence=round(similarity, 4),
                    total_faces=1,
                    strangers_count=0,
                )

            if similarity > best_confidence:
                best_confidence = similarity
                best_idx = i

        if best_idx >= 0 and best_confidence >= _OWNER_ID_THRESHOLD:
            bbox = self._extract_bbox(results[best_idx])
            return OwnerFaceResult(
                owner_found=True,
                owner_bbox=bbox,
                owner_confidence=round(best_confidence, 4),
                total_faces=total_faces,
                strangers_count=total_faces - 1,
            )

        return OwnerFaceResult(
            owner_found=False,
            owner_bbox=None,
            owner_confidence=round(best_confidence, 4),
            total_faces=total_faces,
            strangers_count=total_faces,  # all faces are unidentified
        )

    # ------------------------------------------------------------------ #
    # Private helpers                                                      #
    # ------------------------------------------------------------------ #

    def _extract_embedding(self, image: np.ndarray, enforce: bool = False) -> np.ndarray | None:
        """Yüz embedding'i çıkar.

        *enforce*: True ise (kayıt/giriş gibi güvenlik-kritik akışlar) gerçek bir
        yüz yoksa None döner — tüm kareyi yanlışlıkla "yüz" saymaz. İzleme akışı
        (identify_owner) hoşgörülü kalsın diye varsayılan False.
        """
        try:
            result = DeepFace.represent(
                img_path=image,
                model_name=_MODEL_NAME,
                enforce_detection=enforce,
                detector_backend="opencv",  # fast
            )
            if not result:
                return None
            face = self._largest_face(result)
            if face is None:
                return None
            if enforce and not self._is_real_face(face, image.shape):
                return None
            vec = np.array(face["embedding"], dtype=np.float32)
            norm = float(np.linalg.norm(vec))
            if norm > 0:
                vec = vec / norm
            return vec
        except Exception:
            logger.debug("DeepFace embedding extraction failed", exc_info=True)
            return None

    @staticmethod
    def _is_real_face(face_data: dict, image_shape: tuple) -> bool:
        """Sonucun gerçek bir tespit edilmiş yüz olup olmadığını doğrula.

        DeepFace, yüz bulamadığında (enforce_detection kapalı fallback'i) tüm kareyi
        kaplayan bir ``facial_area`` ve ``face_confidence=0`` döndürebilir. Bunları
        reddederek 'yüzsüz giriş' açığını kapatırız.
        """
        area = face_data.get("facial_area") or {}
        try:
            w = float(area.get("w", 0))
            h = float(area.get("h", 0))
        except (TypeError, ValueError):
            return False
        if w <= 0 or h <= 0:
            return False

        img_h = float(image_shape[0]) if len(image_shape) > 0 else 0.0
        img_w = float(image_shape[1]) if len(image_shape) > 1 else 0.0
        # Kutu neredeyse tüm kareyse → no-face fallback → reddet.
        if img_w > 0 and img_h > 0 and (w * h) >= 0.92 * img_w * img_h:
            return False

        conf = face_data.get("face_confidence")
        if conf is not None:
            try:
                if float(conf) <= 0.0:
                    return False
            except (TypeError, ValueError):
                pass
        return True

    @staticmethod
    def _largest_face(results: list[dict]) -> dict | None:
        """En büyük ``facial_area``'ya sahip yüzü seç (kayıt/doğrulamada ilk yüzü
        değil en belirgin/öndeki yüzü al → arkadaki bir yabancıyı yanlışlıkla
        kaydetmemek için). facial_area yoksa listedeki ilk yüze düşer."""
        if not results:
            return None

        def _area(face: dict) -> float:
            area = face.get("facial_area") or {}
            try:
                return float(area.get("w", 0)) * float(area.get("h", 0))
            except (TypeError, ValueError):
                return 0.0

        return max(results, key=_area)

    @staticmethod
    def _best_cosine_similarity(live: np.ndarray, stored: np.ndarray) -> float:
        """Return the highest cosine similarity between *live* and any row in *stored*."""
        # both should already be L2-normalised → dot product = cosine similarity
        similarities = stored @ live  # (N,)
        best = float(np.max(similarities))
        # clamp to [0, 1] (should be already, but guard against floating point noise)
        return max(0.0, min(1.0, (best + 1.0) / 2.0))  # map [-1,1] → [0,1]

    @staticmethod
    def _extract_bbox(
        face_data: dict,
    ) -> tuple[int, int, int, int] | None:
        """Extract (x, y, w, h) pixel bbox from a DeepFace.represent() result dict."""
        area = face_data.get("facial_area")
        if not area:
            return None
        try:
            return (
                int(area.get("x", 0)),
                int(area.get("y", 0)),
                int(area.get("w", 0)),
                int(area.get("h", 0)),
            )
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _profile_path(user_id: str) -> Path:
        # Sanitise user_id to avoid path traversal
        safe_id = "".join(c for c in user_id if c.isalnum() or c in "-_")
        return _DATA_ROOT / safe_id / _EMBED_FILENAME
