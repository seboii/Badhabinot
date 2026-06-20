package com.badhabinot.backend.dto.monitoring;

import java.util.List;

public record VisionAnalysisResponse(
        String requestId,
        boolean subjectPresent,
        String postureState,
        double postureConfidence,
        List<Detection> detections,
        Processing processing,
        // Phase 8 — new optional fields (null when not requested or deps unavailable)
        String annotatedFrameBase64,
        List<VisionBehaviorEvent> behaviorEvents,
        // Module A — face authentication result (null when no profile registered)
        AuthStatus auth,
        // Module C — face mesh data (null when MediaPipe unavailable)
        FaceMeshData faceMesh,
        // Module D — hand tracking data (null when MediaPipe unavailable)
        HandTrackingData hands,
        // Module E — pose estimation data (null when YOLO unavailable)
        PoseData pose,
        // YOLO object detections (null when YOLO unavailable)
        YoloData objects,
        // Module G — owner tracking and iris gaze (null when face auth disabled)
        OwnerTracking ownerTracking
) {
    public record Detection(
            String eventType,
            double confidence,
            String severity,
            String recommendationHint,
            Evidence evidence
    ) {
    }

    public record Evidence(
            boolean faceDetected,
            boolean upperBodyDetected,
            int handCount,
            Double postureAlignmentScore,
            Double handFaceProximityScore,
            Double handMotionScore,
            Double repetitiveMotionScore,
            Double repeatedHandToFaceScore,
            Double elongatedObjectScore
    ) {
    }

    public record Processing(
            int frameWidth,
            int frameHeight,
            long visionLatencyMs
    ) {
    }

    /** Mirrors the Python BehaviorEventData schema. */
    public record VisionBehaviorEvent(
            String eventType,
            String severity,
            double confidence,
            String detail
    ) {
    }

    /** Mirrors the Python FaceAuthStatus schema (Module A). */
    public record AuthStatus(
            boolean enabled,
            boolean authenticated,
            double confidence,
            int framesEnrolled,
            String error
    ) {
    }

    /** Mirrors the Python FaceMeshData schema (Module C). */
    public record FaceMeshData(
            List<List<Double>> landmarks,
            double ear,
            double mar,
            boolean isDrowsy,
            boolean isYawning,
            double yaw,
            double pitch,
            double roll,
            boolean gazeOffScreen
    ) {
    }

    /** Single hand tracking result. Mirrors Python HandData. */
    public record HandItem(
            List<List<Double>> landmarks,
            String handedness,
            double centerX,
            double centerY,
            boolean nearFace,
            boolean nearMouth
    ) {
    }

    /** Mirrors the Python HandTrackingData schema (Module D). */
    public record HandTrackingData(
            List<HandItem> hands,
            boolean faceTouchDetected,
            boolean mouthTouchDetected
    ) {
    }

    /** Single pose keypoint (x, y, confidence). */
    public record PoseKeypoint(
            double x,
            double y,
            double confidence
    ) {
    }

    /** Mirrors the Python PoseData schema (Module E). */
    public record PoseData(
            List<PoseKeypoint> keypoints,
            double spineTiltAngle,
            double shoulderTiltAngle,
            int postureScore,
            boolean isSlouching,
            List<Double> personBbox,
            // Çok-sinyalli postür alanları (yeni; null güvenli, eski yanıtlarda yok)
            String postureCategory,
            String postureReason,
            Double forwardHeadRatio,
            Double lateralOffset,
            Double headRoll,
            Double headDownRatio,
            Double proximityRatio
    ) {
    }

    /** Single YOLO object detection. */
    public record ObjectDetection(
            int classId,
            String className,
            double confidence,
            List<Double> bboxNorm
    ) {
    }

    /** Mirrors the Python YoloDetectionData schema. */
    public record YoloData(
            List<ObjectDetection> detections,
            boolean bottleNearMouth,
            boolean cupNearMouth,
            boolean phoneDetected
    ) {
    }

    /** Iris-based gaze direction. Mirrors Python GazeData (Module G). */
    public record GazeData(
            List<Double> gazeVector,
            boolean lookingAtScreen,
            String gazeZone,
            double confidence
    ) {
    }

    /** Aggregated owner identification and gaze result. Mirrors Python OwnerTrackingData. */
    public record OwnerTracking(
            boolean ownerTracked,
            GazeData ownerGaze,
            int strangersInFrame
    ) {
    }
}
