from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from datetime import datetime, timedelta
from math import hypot
from typing import Deque

from app.services.vision.models import TemporalFeatures


@dataclass(frozen=True)
class SessionObservation:
    captured_at: datetime
    hand_centroid_x: float | None
    hand_centroid_y: float | None
    hand_face_proximity_score: float
    elongated_object_score: float
    frame_diagonal: float


class SessionStateStore:
    def __init__(self, *, max_observations: int = 8, expiry_minutes: int = 30) -> None:
        self.max_observations = max_observations
        self.expiry = timedelta(minutes=expiry_minutes)
        self._observations: dict[str, Deque[SessionObservation]] = {}

    def update(
        self,
        session_id: str,
        observation: SessionObservation,
    ) -> TemporalFeatures:
        self._cleanup(observation.captured_at)
        history = self._observations.setdefault(session_id, deque(maxlen=self.max_observations))
        previous = list(history)
        history.append(observation)

        if not previous:
            return TemporalFeatures(
                hand_motion_score=0.0,
                repetitive_motion_score=0.0,
                repeated_hand_to_face_score=observation.hand_face_proximity_score * 0.4,
            )

        last = previous[-1]
        hand_motion_score = 0.0
        if (
            observation.hand_centroid_x is not None
            and observation.hand_centroid_y is not None
            and last.hand_centroid_x is not None
            and last.hand_centroid_y is not None
            and observation.frame_diagonal > 0
        ):
            hand_motion_score = min(
                1.0,
                hypot(
                    observation.hand_centroid_x - last.hand_centroid_x,
                    observation.hand_centroid_y - last.hand_centroid_y,
                )
                / max(observation.frame_diagonal * 0.28, 1.0),
            )

        proximity_values = [item.hand_face_proximity_score for item in (*previous, observation)]
        crossings = 0
        near_face_frames = 0
        for index, value in enumerate(proximity_values):
            if value >= 0.55:
                near_face_frames += 1
            if index == 0:
                continue
            if abs(value - proximity_values[index - 1]) >= 0.18:
                crossings += 1

        repetitive_motion_score = min(
            1.0,
            (crossings / max(len(proximity_values) - 1, 1)) * 0.65
            + (near_face_frames / len(proximity_values)) * 0.35,
        )

        repeated_hand_to_face_score = min(
            1.0,
            observation.hand_face_proximity_score * 0.45
            + repetitive_motion_score * 0.35
            + observation.elongated_object_score * 0.20,
        )

        return TemporalFeatures(
            hand_motion_score=round(hand_motion_score, 4),
            repetitive_motion_score=round(repetitive_motion_score, 4),
            repeated_hand_to_face_score=round(repeated_hand_to_face_score, 4),
        )

    def _cleanup(self, now: datetime) -> None:
        expired_sessions = []
        for session_id, history in self._observations.items():
            if not history:
                expired_sessions.append(session_id)
                continue
            if now - history[-1].captured_at > self.expiry:
                expired_sessions.append(session_id)
        for session_id in expired_sessions:
            self._observations.pop(session_id, None)
