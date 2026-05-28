from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any


# ══════════════════════════════════════════════════════════════════════════════
# Owner tracking state — tracks per-session owner face & gaze across frames
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class OwnerTrackingObservation:
    """Per-frame owner tracking data fed into :class:`OwnerTrackingStateStore`."""

    captured_at: datetime
    owner_found: bool
    owner_bbox: tuple[int, int, int, int] | None   # (x, y, w, h) pixel coords
    owner_gaze: Any | None                          # GazeResult from vision_face_mesh
    strangers_in_frame: int                         # non-owner faces detected


@dataclass
class _OwnerSessionState:
    """Mutable per-session state maintained by :class:`OwnerTrackingStateStore`."""

    owner_face_bbox: tuple[int, int, int, int] | None = None
    owner_gaze: Any | None = None
    strangers_in_frame: int = 0
    owner_absence_streak: int = 0   # consecutive frames where owner was not found
    last_seen: datetime = field(
        default_factory=lambda: datetime.now(tz=timezone.utc)
    )


class OwnerTrackingStateStore:
    """Per-session store for owner face and gaze tracking state.

    Maintains a lightweight mutable state dict keyed by session_id.
    Sessions expire after ``expiry_minutes`` of inactivity.
    """

    def __init__(self, expiry_minutes: int = 30) -> None:
        self._expiry = timedelta(minutes=expiry_minutes)
        self._states: dict[str, _OwnerSessionState] = {}

    def update(
        self,
        session_id: str,
        observation: OwnerTrackingObservation,
    ) -> _OwnerSessionState:
        """Record *observation* and return the updated session state."""
        self._cleanup(observation.captured_at)
        state = self._states.setdefault(session_id, _OwnerSessionState())
        state.last_seen = observation.captured_at
        state.owner_face_bbox = observation.owner_bbox
        state.owner_gaze = observation.owner_gaze
        state.strangers_in_frame = observation.strangers_in_frame

        if observation.owner_found:
            state.owner_absence_streak = 0
        else:
            state.owner_absence_streak += 1

        return state

    def _cleanup(self, now: datetime) -> None:
        expired = [
            sid for sid, state in self._states.items()
            if (now - state.last_seen) > self._expiry
        ]
        for sid in expired:
            self._states.pop(sid, None)
