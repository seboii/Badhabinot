from __future__ import annotations

from math import hypot

import cv2
import numpy as np

from app.services.vision.models import FrameFeatures, Region


class VisionFeatureExtractor:
    def __init__(self) -> None:
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
        self.upper_body_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_upperbody.xml"
        )

    def extract(self, image: np.ndarray) -> tuple[FrameFeatures, np.ndarray, np.ndarray]:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        gray = cv2.equalizeHist(gray)
        edges = cv2.Canny(gray, 60, 150)
        focus_score = float(cv2.Laplacian(gray, cv2.CV_64F).var())

        height, width = gray.shape
        brightness_mean = float(gray.mean())
        edge_density = float(edges.mean() / 255.0)

        center_crop = edges[height // 4 : (3 * height) // 4, width // 4 : (3 * width) // 4]
        center_edge_density = float(center_crop.mean() / 255.0) if center_crop.size else 0.0

        face_region = self._detect_largest(
            self.face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(max(width // 10, 48), max(height // 10, 48)),
            )
        )
        upper_body_region = self._detect_largest(
            self.upper_body_cascade.detectMultiScale(
                gray,
                scaleFactor=1.05,
                minNeighbors=3,
                minSize=(max(width // 4, 96), max(height // 4, 96)),
            )
        )

        hand_regions = self._detect_hand_regions(image, face_region)
        dominant_hand_region = self._select_dominant_hand(hand_regions, face_region)

        face_size_ratio = (
            0.0 if face_region is None else face_region.area / max(float(width * height), 1.0)
        )
        posture_alignment_score = self._posture_alignment_score(
            face_region,
            upper_body_region,
            width,
            height,
            gray,
        )
        hand_face_proximity_score = self._hand_face_proximity_score(face_region, dominant_hand_region, width, height)
        elongated_object_score = self._elongated_object_score(edges, dominant_hand_region)

        subject_present = (
            (face_region is not None)
            or (upper_body_region is not None)
            or (width >= 64 and height >= 64 and brightness_mean > 12.0)
        )

        return (
            FrameFeatures(
                frame_width=width,
                frame_height=height,
                brightness_mean=round(brightness_mean, 4),
                edge_density=round(edge_density, 4),
                center_edge_density=round(center_edge_density, 4),
                focus_score=round(focus_score, 4),
                subject_present=subject_present,
                face_region=face_region,
                upper_body_region=upper_body_region,
                hand_regions=hand_regions,
                dominant_hand_region=dominant_hand_region,
                face_size_ratio=round(face_size_ratio, 4),
                posture_alignment_score=round(posture_alignment_score, 4),
                hand_face_proximity_score=round(hand_face_proximity_score, 4),
                elongated_object_score=round(elongated_object_score, 4),
            ),
            gray,
            edges,
        )

    def _detect_largest(self, regions: np.ndarray) -> Region | None:
        if regions is None or len(regions) == 0:
            return None
        x, y, width, height = max(regions, key=lambda candidate: int(candidate[2] * candidate[3]))
        return Region(int(x), int(y), int(width), int(height))

    def _detect_hand_regions(self, image: np.ndarray, face_region: Region | None) -> list[Region]:
        ycrcb = cv2.cvtColor(image, cv2.COLOR_BGR2YCrCb)
        lower = np.array([0, 133, 77], dtype=np.uint8)
        upper = np.array([255, 173, 127], dtype=np.uint8)
        mask = cv2.inRange(ycrcb, lower, upper)

        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        regions: list[Region] = []
        frame_area = image.shape[0] * image.shape[1]
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < max(frame_area * 0.002, 240):
                continue
            x, y, width, height = cv2.boundingRect(contour)
            region = Region(int(x), int(y), int(width), int(height))
            if face_region is not None and self._intersection_ratio(region, face_region) > 0.35:
                continue
            if region.width < 14 or region.height < 14:
                continue
            regions.append(region)

        return sorted(regions, key=lambda region: region.area, reverse=True)[:4]

    def _select_dominant_hand(
        self,
        hand_regions: list[Region],
        face_region: Region | None,
    ) -> Region | None:
        if not hand_regions:
            return None
        if face_region is None:
            return hand_regions[0]
        return min(
            hand_regions,
            key=lambda region: hypot(region.center_x - face_region.center_x, region.center_y - face_region.center_y),
        )

    def _posture_alignment_score(
        self,
        face_region: Region | None,
        upper_body_region: Region | None,
        width: int,
        height: int,
        gray: np.ndarray,
    ) -> float:
        if face_region is not None and upper_body_region is not None:
            horizontal_offset = abs(face_region.center_x - upper_body_region.center_x) / max(upper_body_region.width / 2.0, 1.0)
            expected_face_position = upper_body_region.y + (upper_body_region.height * 0.28)
            vertical_offset = abs(face_region.center_y - expected_face_position) / max(upper_body_region.height, 1.0)
            face_scale = max(0.0, (face_region.area / max(float(upper_body_region.area), 1.0)) - 0.22) * 1.8
            return self._clamp((horizontal_offset * 0.4) + (vertical_offset * 0.4) + (face_scale * 0.2))

        if face_region is not None:
            horizontal_offset = abs(face_region.center_x - (width / 2.0)) / max(width / 2.0, 1.0)
            vertical_offset = max(0.0, (face_region.center_y / max(height, 1.0)) - 0.30)
            face_scale = max(0.0, ((face_region.area / max(float(width * height), 1.0)) - 0.08) * 3.2)
            return self._clamp((horizontal_offset * 0.35) + (vertical_offset * 0.35) + (face_scale * 0.30))

        upper = gray[: height // 2, :]
        lower = gray[height // 2 :, :]
        upper_std = float(upper.std()) if upper.size else 0.0
        lower_std = float(lower.std()) if lower.size else 0.0
        return self._clamp(abs(upper_std - lower_std) / 128.0)

    def _hand_face_proximity_score(
        self,
        face_region: Region | None,
        dominant_hand_region: Region | None,
        width: int,
        height: int,
    ) -> float:
        if face_region is None or dominant_hand_region is None:
            return 0.0
        distance = hypot(
            face_region.center_x - dominant_hand_region.center_x,
            face_region.center_y - dominant_hand_region.center_y,
        )
        normalization = max(face_region.diagonal * 3.2, hypot(width, height) * 0.25, 1.0)
        return self._clamp(1.0 - (distance / normalization))

    def _elongated_object_score(self, edges: np.ndarray, dominant_hand_region: Region | None) -> float:
        if dominant_hand_region is None:
            return 0.0

        pad = 10
        y_start = max(dominant_hand_region.y - pad, 0)
        y_end = min(dominant_hand_region.y + dominant_hand_region.height + pad, edges.shape[0])
        x_start = max(dominant_hand_region.x - pad, 0)
        x_end = min(dominant_hand_region.x + dominant_hand_region.width + pad, edges.shape[1])
        roi = edges[y_start:y_end, x_start:x_end]
        if roi.size == 0:
            return 0.0

        contours, _ = cv2.findContours(roi, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        best_score = 0.0
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < 28:
                continue
            _, _, width, height = cv2.boundingRect(contour)
            major = max(width, height)
            minor = max(min(width, height), 1)
            aspect_ratio = major / minor
            contour_score = self._clamp((aspect_ratio - 1.8) / 4.5)
            if contour_score > best_score:
                best_score = contour_score
        return best_score

    def _intersection_ratio(self, left: Region, right: Region) -> float:
        x_start = max(left.x, right.x)
        y_start = max(left.y, right.y)
        x_end = min(left.x + left.width, right.x + right.width)
        y_end = min(left.y + left.height, right.y + right.height)
        if x_end <= x_start or y_end <= y_start:
            return 0.0
        intersection = (x_end - x_start) * (y_end - y_start)
        return intersection / max(float(left.area), 1.0)

    def _clamp(self, value: float) -> float:
        return max(0.0, min(1.0, value))
