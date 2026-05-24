"""Tests for the face verification endpoint (POST /v1/vision/face/{user_id}/verify).

These tests mock both _decode_image and VisionFaceAuth to avoid requiring
a real camera frame, a decodable JPEG, or a DeepFace installation.
"""
from __future__ import annotations

from unittest.mock import patch

import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import settings

API_KEY = settings.internal_api_key
AUTH_HEADERS = {"X-Internal-Api-Key": API_KEY}

# Placeholder base64 — _decode_image is mocked so the content doesn't matter
_TINY_JPEG_B64 = "dGVzdA=="

# Dummy numpy frame returned by the mocked _decode_image
_DUMMY_FRAME = np.zeros((100, 100, 3), dtype=np.uint8)

# Context manager that patches _decode_image for all verify-endpoint tests
def _mock_decode():
    return patch(
        "app.api.routes.face_registration._decode_image",
        return_value=_DUMMY_FRAME,
    )


@pytest.fixture()
def client():
    return TestClient(app)


# ──────────────────────────────────────────────────────────────────────────────
# /verify endpoint tests
# ──────────────────────────────────────────────────────────────────────────────

class TestFaceVerifyEndpoint:

    def test_requires_api_key(self, client: TestClient):
        response = client.post(
            "/v1/vision/face/user-123/verify",
            json={"image_base64": _TINY_JPEG_B64, "image_content_type": "image/jpeg"},
        )
        assert response.status_code == 401

    def test_verify_matching_face_returns_verified_true(self, client: TestClient):
        with _mock_decode(), patch(
            "app.api.routes.face_registration._auth.verify_face_for_login",
            return_value=(True, 0.92, "Yüz doğrulandı"),
        ):
            response = client.post(
                "/v1/vision/face/user-123/verify",
                json={"image_base64": _TINY_JPEG_B64, "image_content_type": "image/jpeg"},
                headers=AUTH_HEADERS,
            )
        assert response.status_code == 200
        data = response.json()
        assert data["verified"] is True
        assert data["confidence"] >= 0.85
        assert "doğrulandı" in data["message"]

    def test_verify_non_matching_face_returns_verified_false(self, client: TestClient):
        with _mock_decode(), patch(
            "app.api.routes.face_registration._auth.verify_face_for_login",
            return_value=(False, 0.42, "Yüz eşleşmedi"),
        ):
            response = client.post(
                "/v1/vision/face/user-123/verify",
                json={"image_base64": _TINY_JPEG_B64, "image_content_type": "image/jpeg"},
                headers=AUTH_HEADERS,
            )
        assert response.status_code == 200
        data = response.json()
        assert data["verified"] is False
        assert data["confidence"] < 0.85

    def test_verify_no_face_in_image(self, client: TestClient):
        with _mock_decode(), patch(
            "app.api.routes.face_registration._auth.verify_face_for_login",
            return_value=(False, 0.0, "No face detected in image"),
        ):
            response = client.post(
                "/v1/vision/face/user-123/verify",
                json={"image_base64": _TINY_JPEG_B64, "image_content_type": "image/jpeg"},
                headers=AUTH_HEADERS,
            )
        assert response.status_code == 200
        data = response.json()
        assert data["verified"] is False
        assert "face" in data["message"].lower()

    def test_verify_multiple_faces_returns_false(self, client: TestClient):
        with _mock_decode(), patch(
            "app.api.routes.face_registration._auth.verify_face_for_login",
            return_value=(False, 0.0, "Multiple faces detected"),
        ):
            response = client.post(
                "/v1/vision/face/user-123/verify",
                json={"image_base64": _TINY_JPEG_B64, "image_content_type": "image/jpeg"},
                headers=AUTH_HEADERS,
            )
        assert response.status_code == 200
        data = response.json()
        assert data["verified"] is False

    def test_verify_no_stored_embeddings(self, client: TestClient):
        with _mock_decode(), patch(
            "app.api.routes.face_registration._auth.verify_face_for_login",
            return_value=(False, 0.0, "No face profile registered for this user"),
        ):
            response = client.post(
                "/v1/vision/face/user-no-profile/verify",
                json={"image_base64": _TINY_JPEG_B64, "image_content_type": "image/jpeg"},
                headers=AUTH_HEADERS,
            )
        assert response.status_code == 200
        data = response.json()
        assert data["verified"] is False
        assert "profile" in data["message"].lower()

    def test_verify_invalid_base64_returns_400(self, client: TestClient):
        response = client.post(
            "/v1/vision/face/user-123/verify",
            json={"image_base64": "!!!not-valid-base64!!!", "image_content_type": "image/jpeg"},
            headers=AUTH_HEADERS,
        )
        assert response.status_code == 400


# ──────────────────────────────────────────────────────────────────────────────
# Unit tests for verify_face_for_login logic
# ──────────────────────────────────────────────────────────────────────────────

class TestVerifyFaceForLoginUnit:

    def test_returns_false_when_deepface_unavailable(self, tmp_path, monkeypatch):
        from app.services.vision import vision_face_auth
        monkeypatch.setattr(vision_face_auth, "_DEEPFACE_AVAILABLE", False)

        auth = vision_face_auth.VisionFaceAuth()
        dummy_image = np.zeros((100, 100, 3), dtype=np.uint8)
        verified, confidence, message = auth.verify_face_for_login("user-1", dummy_image)

        assert verified is False
        assert confidence == 0.0

    def test_returns_false_when_no_profile(self, tmp_path, monkeypatch):
        from app.services.vision import vision_face_auth
        monkeypatch.setattr(vision_face_auth, "_DATA_ROOT", tmp_path)
        monkeypatch.setattr(vision_face_auth, "_DEEPFACE_AVAILABLE", True)

        auth = vision_face_auth.VisionFaceAuth()
        dummy_image = np.zeros((100, 100, 3), dtype=np.uint8)
        verified, confidence, message = auth.verify_face_for_login("no-such-user", dummy_image)

        assert verified is False
        assert "No face profile" in message
