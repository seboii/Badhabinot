from __future__ import annotations

from dataclasses import dataclass, field
from math import hypot
from typing import Any


@dataclass(frozen=True)
class Region:
    x: int
    y: int
    width: int
    height: int

    @property
    def center_x(self) -> float:
        return self.x + (self.width / 2.0)

    @property
    def center_y(self) -> float:
        return self.y + (self.height / 2.0)

    @property
    def area(self) -> int:
        return self.width * self.height

    @property
    def diagonal(self) -> float:
        return hypot(self.width, self.height)

    def to_dict(self) -> dict[str, int]:
        return {
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
        }


@dataclass(frozen=True)
class FrameFeatures:
    frame_width: int
    frame_height: int
    brightness_mean: float
    edge_density: float
    center_edge_density: float
    focus_score: float
    subject_present: bool
    face_region: Region | None
    upper_body_region: Region | None
    hand_regions: list[Region]
    dominant_hand_region: Region | None
    face_size_ratio: float
    posture_alignment_score: float
    hand_face_proximity_score: float
    elongated_object_score: float


@dataclass(frozen=True)
class TemporalFeatures:
    hand_motion_score: float
    repetitive_motion_score: float
    repeated_hand_to_face_score: float


@dataclass(frozen=True)
class DetectionResult:
    event_type: str
    confidence: float
    severity: str
    recommendation_hint: str
    evidence: dict[str, Any] = field(default_factory=dict)
