"""Module A — Face Registration & Authentication API routes.

Endpoints:
    POST /v1/vision/face/register   — submit a frame to enrol user's face
    DELETE /v1/vision/face/{user_id} — remove stored face profile
    GET /v1/vision/face/{user_id}/status — check enrolment status
"""

from __future__ import annotations

import base64
import threading

import cv2
import numpy as np
from fastapi import APIRouter, Depends, HTTPException

from app.core.security import require_internal_api_key
from app.schemas.vision import (
    FaceDeleteResponse,
    FaceLiveVerifyRequest,
    FaceLiveVerifyResponse,
    FaceRegisterRequest,
    FaceRegisterResponse,
    FaceVerifyRequest,
    FaceVerifyResponse,
)
from app.services.vision.vision_face_auth import VisionFaceAuth
from app.services.vision.vision_face_mesh import VisionFaceMesh
from app.services.vision.vision_liveness import verify_liveness

router = APIRouter(prefix="/v1/vision/face", tags=["face-registration"])
_auth = VisionFaceAuth()
_mesh = VisionFaceMesh()
# DeepFace ve MediaPipe thread-safe değil; giriş düşük eşzamanlılıklı olduğundan
# canlılık doğrulamasını basitçe serileştiriyoruz.
_live_lock = threading.Lock()
_MAX_LIVE_FRAMES = 12


def _decode_image(image_base64: str) -> np.ndarray:
    try:
        normalized = image_base64.split(",", maxsplit=1)[-1]
        raw = base64.b64decode(normalized)
        array = np.frombuffer(raw, dtype=np.uint8)
        image = cv2.imdecode(array, cv2.IMREAD_COLOR)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="invalid base64 image payload") from exc
    if image is None:
        raise HTTPException(status_code=400, detail="image could not be decoded")
    return image


@router.post("/register", response_model=FaceRegisterResponse)
async def register_face(
    request: FaceRegisterRequest,
    _: None = Depends(require_internal_api_key),
) -> FaceRegisterResponse:
    """Submit one frame to enrol (or extend) a user's face profile.

    Call this endpoint 5-10 times with different facial angles/expressions
    to build a robust profile.  At least 3 frames are required before
    verification becomes active.
    """
    image = _decode_image(request.image_base64)
    success = _auth.register_frame(request.user_id, image)

    if not success:
        return FaceRegisterResponse(
            user_id=request.user_id,
            success=False,
            frames_enrolled=_auth.frame_count(request.user_id),
            message="No face detected in frame — try again with better lighting",
        )

    frames = _auth.frame_count(request.user_id)
    ready = _auth.has_profile(request.user_id)
    msg = (
        f"Frame enrolled ({frames} total). Profile ready for verification."
        if ready
        else f"Frame enrolled ({frames} total). Need at least 3 frames to activate."
    )
    return FaceRegisterResponse(
        user_id=request.user_id,
        success=True,
        frames_enrolled=frames,
        message=msg,
    )


@router.post("/{user_id}/verify", response_model=FaceVerifyResponse)
async def verify_face(
    user_id: str,
    request: FaceVerifyRequest,
    _: None = Depends(require_internal_api_key),
) -> FaceVerifyResponse:
    """Verify a face image against stored embeddings for login authentication.

    Returns verified=True only when:
    - The user has a registered face profile (≥3 frames)
    - Exactly one face is detected in the image
    - Cosine similarity against stored embeddings >= 0.85
    """
    image = _decode_image(request.image_base64)
    verified, confidence, message = _auth.verify_face_for_login(user_id, image)
    return FaceVerifyResponse(verified=verified, confidence=confidence, message=message)


@router.post("/{user_id}/verify-live", response_model=FaceLiveVerifyResponse)
async def verify_face_live(
    user_id: str,
    request: FaceLiveVerifyRequest,
    _: None = Depends(require_internal_api_key),
) -> FaceLiveVerifyResponse:
    """Aktif challenge ile yüz girişi: kimlik + canlılık tek istekte doğrulanır.

    - **Kimlik:** dizideki örnek kareler saklı embedding'lerle karşılaştırılır.
    - **Canlılık:** istenen eylem (BLINK / TURN_HEAD) kare dizisi boyunca EAR/yaw
      zaman serisinden doğrulanır. Durağan bir fotoğraf bunu geçemez.
    """
    frames_b64 = request.frames[:_MAX_LIVE_FRAMES]
    if not frames_b64:
        raise HTTPException(status_code=400, detail="no frames provided")

    images = [_decode_image(f) for f in frames_b64]

    with _live_lock:
        # Kimlik: maliyeti sınırlamak için en çok 3 örnek kareyi dene, en iyisini al.
        sample_idx = sorted({0, len(images) // 2, len(images) - 1})
        best_conf = 0.0
        identity_ok = False
        for idx in sample_idx:
            verified, confidence, _msg = _auth.verify_face_for_login(user_id, images[idx])
            best_conf = max(best_conf, float(confidence))
            if verified:
                identity_ok = True
                break

        liveness = verify_liveness(_mesh, images, request.action)

    if not identity_ok:
        message = "Yüz eşleşmedi"
    elif not liveness.passed:
        message = liveness.detail
    else:
        message = "Yüz ve canlılık doğrulandı"

    return FaceLiveVerifyResponse(
        verified=identity_ok,
        liveness_passed=liveness.passed,
        action_detected=liveness.action_detected,
        confidence=round(best_conf, 4),
        message=message,
    )


@router.delete("/{user_id}", response_model=FaceDeleteResponse)
async def delete_face_profile(
    user_id: str,
    _: None = Depends(require_internal_api_key),
) -> FaceDeleteResponse:
    """Delete all stored face embeddings for a user."""
    deleted = _auth.delete_profile(user_id)
    return FaceDeleteResponse(user_id=user_id, deleted=deleted)


@router.get("/{user_id}/status", response_model=FaceRegisterResponse)
async def face_status(
    user_id: str,
    _: None = Depends(require_internal_api_key),
) -> FaceRegisterResponse:
    """Return enrolment status for a user (no image required)."""
    frames = _auth.frame_count(user_id)
    ready = _auth.has_profile(user_id)
    return FaceRegisterResponse(
        user_id=user_id,
        success=ready,
        frames_enrolled=frames,
        message="Profile active" if ready else f"{frames} frames enrolled (need 3+)",
    )
