from __future__ import annotations

import asyncio
import base64
import time
from math import hypot

import cv2
import numpy as np
from fastapi import HTTPException

from app.schemas.vision import (
    BehaviorEventData,
    DetectionEvidence,
    FaceAuthStatus,
    FaceMeshData,
    GazeData,
    HandData,
    HandTrackingData,
    ObjectDetectionData,
    OwnerTrackingData,
    PoseData,
    PoseKeypointData,
    ProcessingDetails,
    VisionAnalysisRequest,
    VisionAnalysisResponse,
    VisionDetection,
    VisionSignals,
    YoloDetectionData,
)
from app.services.vision import SessionStateStore, VisionDetectors, VisionFeatureExtractor
from app.services.vision.session_state import (
    OwnerTrackingObservation,
    OwnerTrackingStateStore,
    SessionObservation,
)

# New modules (each degrades gracefully if its dependencies are missing)
from app.services.vision.behavior_engine import BehaviorFrameInput, BehaviorStateStore
from app.services.vision.session_logger import log_frame_events
from app.services.vision.vision_face_auth import OwnerFaceResult, VisionFaceAuth
from app.services.vision.vision_face_mesh import GazeResult, VisionFaceMesh
from app.services.vision.vision_hand_tracker import VisionHandTracker
from app.services.vision.vision_overlay import OverlayData, frame_to_base64, render_annotated_frame
from app.services.vision.vision_pose_estimator import VisionPoseEstimator
from app.services.vision.vision_yolo_detector import VisionYoloDetector


class VisionAnalysisService:
    def __init__(self) -> None:
        # Legacy pipeline (always active)
        self.feature_extractor = VisionFeatureExtractor()
        self.detectors = VisionDetectors()
        self.session_state = SessionStateStore()

        # New modules (gracefully degrade if deps missing)
        self.face_auth = VisionFaceAuth()
        self.face_mesh = VisionFaceMesh()
        self.hand_tracker = VisionHandTracker()
        self.pose_estimator = VisionPoseEstimator()
        self.yolo_detector = VisionYoloDetector()
        self.behavior_store = BehaviorStateStore()
        self.owner_tracking_store = OwnerTrackingStateStore()

    async def analyze(self, request: VisionAnalysisRequest, *, render_overlay: bool = False) -> VisionAnalysisResponse:
        started = time.perf_counter()
        image = self._decode_image(request.image_base64)

        # ── Phase 1: Parallel — independent modules ───────────────────────
        # feature_extractor, identify_owner (replaces face_auth), face_mesh, and
        # pose_estimator have no mutual dependencies and run simultaneously.
        features_raw, owner_quad, mesh_result, pose_result = await asyncio.gather(
            asyncio.to_thread(self.feature_extractor.extract, image),
            asyncio.to_thread(self._run_identify_owner, request.user_id, image),
            asyncio.to_thread(self.face_mesh.analyze, image),
            asyncio.to_thread(self.pose_estimator.analyze, image),
        )
        features, _, _ = features_raw
        face_authenticated, auth_confidence, auth_status, owner_result = owner_quad

        # ── Phase 2: Session state + detectors (need features) ────────────
        frame_diagonal = hypot(features.frame_width, features.frame_height)
        dominant_hand = features.dominant_hand_region
        temporal = self.session_state.update(
            request.session_id,
            SessionObservation(
                captured_at=request.captured_at,
                hand_centroid_x=None if dominant_hand is None else dominant_hand.center_x,
                hand_centroid_y=None if dominant_hand is None else dominant_hand.center_y,
                hand_face_proximity_score=features.hand_face_proximity_score,
                elongated_object_score=features.elongated_object_score,
                frame_diagonal=frame_diagonal,
            ),
        )
        posture_state, posture_confidence, detections, signals = self.detectors.detect(
            features, temporal
        )

        # ── Phase 3: Build face mesh data + mouth region ──────────────────
        face_mesh_data: FaceMeshData | None = None
        face_landmarks_list = None
        if mesh_result is not None:
            face_landmarks_list = mesh_result.landmarks
            face_mesh_data = FaceMeshData(
                landmarks=[[lm[0], lm[1], lm[2]] for lm in mesh_result.landmarks],
                ear=mesh_result.ear,
                mar=mesh_result.mar,
                is_drowsy=mesh_result.is_drowsy,
                is_yawning=mesh_result.is_yawning,
                yaw=mesh_result.yaw,
                pitch=mesh_result.pitch,
                roll=mesh_result.roll,
                gaze_off_screen=mesh_result.gaze_off_screen,
            )
        mouth_region = self._compute_mouth_region(face_landmarks_list)

        # ── Phase 4: Parallel — hand tracker + YOLO + gaze ───────────────
        # All three depend only on results from Phase 1/3; they run simultaneously.
        hand_result, yolo_result, gaze_result = await asyncio.gather(
            asyncio.to_thread(self.hand_tracker.analyze, image, face_landmarks_list),
            asyncio.to_thread(self.yolo_detector.detect, image, mouth_region),
            asyncio.to_thread(self._run_gaze, image, owner_result.owner_bbox),
        )

        # ── Phase 4.5: Owner tracking state update ────────────────────────
        owner_state = self.owner_tracking_store.update(
            request.session_id,
            OwnerTrackingObservation(
                captured_at=request.captured_at,
                owner_found=owner_result.owner_found,
                owner_bbox=owner_result.owner_bbox,
                owner_gaze=gaze_result,
                strangers_in_frame=owner_result.strangers_count,
            ),
        )

        # ── Unpack hand result ────────────────────────────────────────────
        hand_data: HandTrackingData | None = None
        face_touch = False
        mouth_touch = False
        if hand_result is not None:
            face_touch = hand_result.face_touch_detected
            mouth_touch = hand_result.mouth_touch_detected
            hand_data = HandTrackingData(
                hands=[
                    HandData(
                        landmarks=[[lm[0], lm[1], lm[2]] for lm in h.landmarks],
                        handedness=h.handedness,
                        center_x=h.center_x,
                        center_y=h.center_y,
                        near_face=h.near_face,
                        near_mouth=h.near_mouth,
                    )
                    for h in hand_result.hands
                ],
                face_touch_detected=hand_result.face_touch_detected,
                mouth_touch_detected=hand_result.mouth_touch_detected,
            )

        # ── Unpack pose result ────────────────────────────────────────────
        pose_data: PoseData | None = None
        is_slouching = False
        posture_score_int = 100
        if pose_result is not None:
            is_slouching = pose_result.is_slouching
            posture_score_int = pose_result.posture_score
            pose_data = PoseData(
                keypoints=[
                    PoseKeypointData(x=kp.x, y=kp.y, confidence=kp.confidence)
                    if kp is not None else None
                    for kp in pose_result.keypoints
                ],
                spine_tilt_angle=pose_result.spine_tilt_angle,
                shoulder_tilt_angle=pose_result.shoulder_tilt_angle,
                posture_score=pose_result.posture_score,
                is_slouching=pose_result.is_slouching,
                person_bbox=list(pose_result.person_bbox) if pose_result.person_bbox else None,
            )

        # ── Unpack YOLO result ────────────────────────────────────────────
        yolo_data: YoloDetectionData | None = None
        bottle_near_mouth = False
        cup_near_mouth = False
        phone_detected = False

        if yolo_result is not None:
            bottle_near_mouth = yolo_result.bottle_near_mouth
            cup_near_mouth = yolo_result.cup_near_mouth
            phone_detected = yolo_result.phone_detected
            yolo_data = YoloDetectionData(
                detections=[
                    ObjectDetectionData(
                        class_id=d.class_id,
                        class_name=d.class_name,
                        confidence=d.confidence,
                        bbox_norm=list(d.bbox_norm),
                    )
                    for d in yolo_result.detections
                ],
                bottle_near_mouth=yolo_result.bottle_near_mouth,
                cup_near_mouth=yolo_result.cup_near_mouth,
                phone_detected=yolo_result.phone_detected,
            )

        # ── Module F: Behavioral Event System ────────────────────────────
        behavior_inputs = BehaviorFrameInput(
            captured_at=request.captured_at,
            session_id=request.session_id,
            user_id=request.user_id,
            face_detected=features.face_region is not None or (mesh_result is not None),
            face_authenticated=face_authenticated,
            auth_confidence=auth_confidence,
            ear=mesh_result.ear if mesh_result else 0.3,
            mar=mesh_result.mar if mesh_result else 0.2,
            is_drowsy=mesh_result.is_drowsy if mesh_result else False,
            is_yawning=mesh_result.is_yawning if mesh_result else False,
            gaze_off_screen=mesh_result.gaze_off_screen if mesh_result else False,
            face_touch_detected=face_touch,
            mouth_touch_detected=mouth_touch,
            is_slouching=is_slouching,
            posture_score=posture_score_int,
            bottle_near_mouth=bottle_near_mouth,
            cup_near_mouth=cup_near_mouth,
            phone_detected=phone_detected,
            elongated_object_score=features.elongated_object_score,
            hand_face_proximity_score=features.hand_face_proximity_score,
            # Owner tracking signals
            owner_tracked=owner_result.owner_found,
            strangers_in_frame=owner_result.strangers_count,
            owner_gaze_looking_at_screen=(
                gaze_result.looking_at_screen if gaze_result is not None else True
            ),
            owner_absence_streak=owner_state.owner_absence_streak,
        )
        behavior_events_raw = self.behavior_store.evaluate(behavior_inputs)
        behavior_events = [
            BehaviorEventData(
                event_type=ev.event_type,
                severity=ev.severity,  # type: ignore[arg-type]
                confidence=ev.confidence,
                detail=ev.detail,
            )
            for ev in behavior_events_raw
        ]

        # ── Build response ────────────────────────────────────────────────
        vision_latency_ms = int((time.perf_counter() - started) * 1000)

        response_detections = [
            VisionDetection(
                event_type=detection.event_type,
                confidence=detection.confidence,
                severity=detection.severity,
                recommendation_hint=detection.recommendation_hint,
                evidence=DetectionEvidence(
                    face_detected=bool(detection.evidence.get("face_detected", False)),
                    upper_body_detected=bool(detection.evidence.get("upper_body_detected", False)),
                    hand_count=int(detection.evidence.get("hand_count", 0)),
                    posture_alignment_score=self._optional_float(
                        detection.evidence.get("posture_alignment_score")
                    ),
                    hand_face_proximity_score=self._optional_float(
                        detection.evidence.get("hand_face_proximity_score")
                    ),
                    hand_motion_score=self._optional_float(
                        detection.evidence.get("hand_motion_score")
                    ),
                    repetitive_motion_score=self._optional_float(
                        detection.evidence.get("repetitive_motion_score")
                    ),
                    repeated_hand_to_face_score=self._optional_float(
                        detection.evidence.get("repeated_hand_to_face_score")
                    ),
                    elongated_object_score=self._optional_float(
                        detection.evidence.get("elongated_object_score")
                    ),
                ),
            )
            for detection in detections
        ]

        # ── Phase 8: Annotated frame (optional) ──────────────────────────
        annotated_b64: str | None = None
        if render_overlay:
            try:
                overlay_data = OverlayData(
                    mesh_result=mesh_result,
                    hand_result=hand_result,
                    pose_result=pose_result,
                    yolo_result=yolo_result,
                    behavior_events=behavior_events_raw,
                    username=request.user_id if face_authenticated else None,
                    authenticated=face_authenticated,
                    posture_score=posture_score_int,
                    fps=0.0,  # fps not tracked server-side
                )
                annotated = render_annotated_frame(image, overlay_data)
                annotated_b64 = frame_to_base64(annotated)
            except Exception:
                pass  # overlay rendering is non-critical; never block the response

        # ── Module H: Session logging ─────────────────────────────────────
        log_frame_events(
            session_id=request.session_id,
            user_id=request.user_id,
            frame_id=request.frame_id,
            captured_at=request.captured_at,
            behavior_events=[ev.model_dump() for ev in behavior_events],
        )

        # ── Module G: Build owner tracking response ───────────────────────
        gaze_data: GazeData | None = None
        if gaze_result is not None:
            gaze_data = GazeData(
                gaze_vector=list(gaze_result.gaze_vector),
                looking_at_screen=gaze_result.looking_at_screen,
                gaze_zone=gaze_result.gaze_zone,
                confidence=gaze_result.confidence,
            )
        owner_tracking_data = OwnerTrackingData(
            owner_tracked=owner_result.owner_found,
            owner_gaze=gaze_data,
            strangers_in_frame=owner_result.strangers_count,
        )

        return VisionAnalysisResponse(
            request_id=request.request_id,
            subject_present=features.subject_present,
            posture_state=posture_state,
            posture_confidence=posture_confidence,
            detections=response_detections,
            signals=VisionSignals(
                brightness_mean=signals["brightness_mean"],
                edge_density=signals["edge_density"],
                center_edge_density=signals["center_edge_density"],
                posture_risk_score=signals["posture_risk_score"],
                hand_face_proximity_score=signals["hand_face_proximity_score"],
                elongated_object_score=signals["elongated_object_score"],
                focus_score=signals["focus_score"],
                posture_confidence=signals["posture_confidence"],
                posture_alignment_score=signals["posture_alignment_score"],
                hand_motion_score=signals["hand_motion_score"],
                repetitive_motion_score=signals["repetitive_motion_score"],
                smoking_gesture_score=signals["smoking_gesture_score"],
                face_size_ratio=signals["face_size_ratio"],
            ),
            processing=ProcessingDetails(
                frame_width=features.frame_width,
                frame_height=features.frame_height,
                brightness_mean=features.brightness_mean,
                edge_density=features.edge_density,
                focus_score=features.focus_score,
                vision_latency_ms=vision_latency_ms,
            ),
            # New fields
            auth=auth_status,
            face_mesh=face_mesh_data,
            hands=hand_data,
            pose=pose_data,
            objects=yolo_data,
            behavior_events=behavior_events,
            owner_tracking=owner_tracking_data,
            annotated_frame_base64=annotated_b64,
        )

    def _decode_image(self, image_base64: str) -> np.ndarray:
        try:
            normalized = image_base64.split(",", maxsplit=1)[-1]
            raw = base64.b64decode(normalized)
            array = np.frombuffer(raw, dtype=np.uint8)
            image = cv2.imdecode(array, cv2.IMREAD_COLOR)
        except Exception as exc:
            raise HTTPException(status_code=400, detail="invalid base64 image payload") from exc

        if image is None:
            raise HTTPException(status_code=400, detail="image payload could not be decoded")
        return image

    def _run_identify_owner(
        self,
        user_id: str,
        image: np.ndarray,
    ) -> tuple[bool, float, FaceAuthStatus, OwnerFaceResult]:
        """Identify the owner face across all detected faces in *image*.

        Replaces ``_run_face_auth``: one DeepFace.represent() call now provides
        both authentication status and multi-face owner localisation.

        Returns (face_authenticated, auth_confidence, FaceAuthStatus, OwnerFaceResult).
        When no face profile exists, authentication is not enforced (owner assumed
        present with confidence 1.0) and owner_bbox is None.
        """
        has_profile = self.face_auth.has_profile(user_id)
        frames_enrolled = self.face_auth.frame_count(user_id)

        if has_profile:
            owner_result = self.face_auth.identify_owner(user_id, image)
            auth_status = FaceAuthStatus(
                enabled=True,
                authenticated=owner_result.owner_found,
                confidence=owner_result.owner_confidence,
                frames_enrolled=frames_enrolled,
            )
            return owner_result.owner_found, owner_result.owner_confidence, auth_status, owner_result

        # No profile registered — authentication not enforced
        no_profile_result = OwnerFaceResult(
            owner_found=True,
            owner_bbox=None,
            owner_confidence=1.0,
            total_faces=0,
            strangers_count=0,
        )
        auth_status = FaceAuthStatus(
            enabled=False,
            authenticated=True,
            confidence=1.0,
            frames_enrolled=0,
        )
        return True, 1.0, auth_status, no_profile_result

    def _run_gaze(
        self,
        image: np.ndarray,
        owner_bbox: tuple[int, int, int, int] | None,
    ) -> GazeResult | None:
        """Extract iris gaze for the owner face; returns None when bbox is absent."""
        if owner_bbox is None:
            return None
        return self.face_mesh.extract_owner_gaze(image, owner_bbox)

    @staticmethod
    def _compute_mouth_region(
        face_landmarks_list: list | None,
    ) -> tuple[float, float, float, float] | None:
        """Return normalized mouth bounding box from face mesh landmarks, or None."""
        if not face_landmarks_list or len(face_landmarks_list) <= 308:
            return None
        ml = face_landmarks_list
        return (
            min(ml[78][0], ml[308][0]),
            min(ml[13][1], ml[14][1]),
            max(ml[78][0], ml[308][0]),
            max(ml[13][1], ml[14][1]),
        )

    def _optional_float(self, value: object) -> float | None:
        if value is None:
            return None
        try:
            return round(float(value), 4)
        except (TypeError, ValueError):
            return None
