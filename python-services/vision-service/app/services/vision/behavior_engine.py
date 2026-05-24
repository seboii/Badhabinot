"""Module F — Behavioral Event System.

Aggregates outputs from all vision modules into discrete behavioral events.
Maintains per-session temporal state (face_absent_since, drowsy_since, etc.)
to enforce duration-based thresholds.

Events emitted:
    FACE_TOUCH       — hand near face landmark
    SMOKING          — elongated object near mouth + hand raised
    EATING           — hand near mouth + food-like object detected
    DRINKING         — bottle/cup near mouth
    LEFT_SCREEN      — no registered face detected > 5 s
    SLOUCHING        — spine angle > 20° sustained > 10 s
    DROWSY           — EAR < 0.25 for > 2 s
    YAWNING          — MAR > 0.60 (immediate)
    DISTRACTED       — gaze off-screen > 8 s
    UNKNOWN_PERSON   — face detected but not authenticated
    FOREIGN_OBJECT   — unexpected YOLO object in frame
"""

from __future__ import annotations

import logging
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Deque

logger = logging.getLogger(__name__)

# ── Duration thresholds ───────────────────────────────────────────────────────
_LEFT_SCREEN_SECS = 5
_DROWSY_SECS = 2
_SLOUCH_SECS = 10
_DISTRACTED_SECS = 8
_GAZE_AWAY_SECS = 3    # iris-based gaze off-screen
_OWNER_ABSENT_SECS = 5  # owner face not identified

# ── Severity mapping ──────────────────────────────────────────────────────────
_EVENT_SEVERITY: dict[str, str] = {
    "FACE_TOUCH":      "low",
    "SMOKING":         "high",
    "EATING":          "medium",
    "DRINKING":        "medium",
    "LEFT_SCREEN":     "high",
    "SLOUCHING":       "medium",
    "DROWSY":          "high",
    "YAWNING":         "low",
    "DISTRACTED":      "medium",
    "UNKNOWN_PERSON":  "high",
    "FOREIGN_OBJECT":  "low",
    # Owner-tracking events
    "GAZE_AWAY":       "medium",
    "OWNER_ABSENT":    "high",
    "STRANGER_DETECTED": "high",
}


@dataclass
class BehaviorEvent:
    event_type: str
    severity: str
    confidence: float          # 0.0 – 1.0
    detail: str = ""           # human-readable detail


@dataclass
class _SessionBehaviorState:
    """Mutable per-session state tracked between frames."""

    face_absent_since: datetime | None = None
    drowsy_since: datetime | None = None
    slouching_since: datetime | None = None
    distracted_since: datetime | None = None
    gaze_away_since: datetime | None = None    # iris-based gaze tracking
    owner_absent_since: datetime | None = None  # owner not identified
    last_seen: datetime = field(default_factory=lambda: datetime.now(tz=timezone.utc))


@dataclass
class BehaviorFrameInput:
    """All per-frame signals fed into the behavior engine."""

    captured_at: datetime
    session_id: str
    user_id: str

    # Face presence & auth
    face_detected: bool = False
    face_authenticated: bool = False   # True = registered user confirmed
    auth_confidence: float = 0.0

    # Face mesh signals
    ear: float = 0.3                   # Eye Aspect Ratio
    mar: float = 0.2                   # Mouth Aspect Ratio
    is_drowsy: bool = False
    is_yawning: bool = False
    gaze_off_screen: bool = False

    # Hand tracking
    face_touch_detected: bool = False
    mouth_touch_detected: bool = False

    # Pose
    is_slouching: bool = False
    posture_score: int = 100

    # YOLO objects
    bottle_near_mouth: bool = False
    cup_near_mouth: bool = False
    phone_detected: bool = False

    # Legacy elongated object score (from feature_extraction.py)
    elongated_object_score: float = 0.0

    # Hand face proximity score (legacy)
    hand_face_proximity_score: float = 0.0

    # ── Owner tracking signals (new) ──────────────────────────────────────
    owner_tracked: bool = True               # True = owner face identified this frame
    strangers_in_frame: int = 0              # count of non-owner faces in frame
    owner_gaze_looking_at_screen: bool = True  # from iris-based gaze tracking
    owner_absence_streak: int = 0            # consecutive frames without owner match


class BehaviorStateStore:
    """In-memory per-session state store for behavior engine.

    Parallel to SessionStateStore — manages duration-based event thresholds.
    Sessions expire after 30 minutes of inactivity.
    """

    def __init__(self, expiry_minutes: int = 30) -> None:
        self._expiry = timedelta(minutes=expiry_minutes)
        self._states: dict[str, _SessionBehaviorState] = {}

    def evaluate(self, inputs: BehaviorFrameInput) -> list[BehaviorEvent]:
        """Update session state from *inputs* and return active behavior events."""
        now = inputs.captured_at
        self._cleanup(now)
        state = self._states.setdefault(inputs.session_id, _SessionBehaviorState())
        state.last_seen = now

        events: list[BehaviorEvent] = []

        # ── Face presence / auth tracking ─────────────────────────────────
        if inputs.face_detected:
            state.face_absent_since = None
        else:
            if state.face_absent_since is None:
                state.face_absent_since = now

        # LEFT_SCREEN
        if state.face_absent_since is not None:
            absent_secs = (now - state.face_absent_since).total_seconds()
            if absent_secs >= _LEFT_SCREEN_SECS:
                events.append(BehaviorEvent(
                    event_type="LEFT_SCREEN",
                    severity=_EVENT_SEVERITY["LEFT_SCREEN"],
                    confidence=min(1.0, absent_secs / (_LEFT_SCREEN_SECS * 3)),
                    detail=f"Face absent for {absent_secs:.0f}s",
                ))

        # UNKNOWN_PERSON — face detected but NOT the registered user
        if inputs.face_detected and not inputs.face_authenticated:
            events.append(BehaviorEvent(
                event_type="UNKNOWN_PERSON",
                severity=_EVENT_SEVERITY["UNKNOWN_PERSON"],
                confidence=round(1.0 - inputs.auth_confidence, 4),
                detail="Unregistered face in frame",
            ))

        # ── Drowsiness tracking ───────────────────────────────────────────
        if inputs.is_drowsy:
            if state.drowsy_since is None:
                state.drowsy_since = now
        else:
            state.drowsy_since = None

        if state.drowsy_since is not None:
            drowsy_secs = (now - state.drowsy_since).total_seconds()
            if drowsy_secs >= _DROWSY_SECS:
                ear_conf = max(0.0, min(1.0, (0.25 - inputs.ear) / 0.25))
                events.append(BehaviorEvent(
                    event_type="DROWSY",
                    severity=_EVENT_SEVERITY["DROWSY"],
                    confidence=round(ear_conf, 4),
                    detail=f"EAR={inputs.ear:.3f} for {drowsy_secs:.1f}s",
                ))

        # ── Yawning (immediate, no duration needed) ───────────────────────
        if inputs.is_yawning:
            mar_conf = min(1.0, (inputs.mar - 0.60) / 0.40)
            events.append(BehaviorEvent(
                event_type="YAWNING",
                severity=_EVENT_SEVERITY["YAWNING"],
                confidence=round(max(0.0, mar_conf), 4),
                detail=f"MAR={inputs.mar:.3f}",
            ))

        # ── Gaze / distraction tracking ───────────────────────────────────
        if inputs.gaze_off_screen:
            if state.distracted_since is None:
                state.distracted_since = now
        else:
            state.distracted_since = None

        if state.distracted_since is not None:
            dist_secs = (now - state.distracted_since).total_seconds()
            if dist_secs >= _DISTRACTED_SECS:
                events.append(BehaviorEvent(
                    event_type="DISTRACTED",
                    severity=_EVENT_SEVERITY["DISTRACTED"],
                    confidence=min(1.0, dist_secs / (_DISTRACTED_SECS * 2)),
                    detail=f"Gaze off-screen for {dist_secs:.0f}s",
                ))

        # ── Slouching tracking ────────────────────────────────────────────
        if inputs.is_slouching:
            if state.slouching_since is None:
                state.slouching_since = now
        else:
            state.slouching_since = None

        if state.slouching_since is not None:
            slouch_secs = (now - state.slouching_since).total_seconds()
            if slouch_secs >= _SLOUCH_SECS:
                posture_conf = max(0.0, (100 - inputs.posture_score) / 100.0)
                events.append(BehaviorEvent(
                    event_type="SLOUCHING",
                    severity=_EVENT_SEVERITY["SLOUCHING"],
                    confidence=round(posture_conf, 4),
                    detail=f"Posture score {inputs.posture_score} for {slouch_secs:.0f}s",
                ))

        # ── Hand / object events (immediate) ──────────────────────────────
        if inputs.face_touch_detected:
            conf = min(1.0, inputs.hand_face_proximity_score + 0.2)
            events.append(BehaviorEvent(
                event_type="FACE_TOUCH",
                severity=_EVENT_SEVERITY["FACE_TOUCH"],
                confidence=round(conf, 4),
                detail="Hand near face detected",
            ))

        if inputs.bottle_near_mouth:
            events.append(BehaviorEvent(
                event_type="DRINKING",
                severity=_EVENT_SEVERITY["DRINKING"],
                confidence=0.75,
                detail="Bottle near mouth",
            ))

        if inputs.cup_near_mouth:
            events.append(BehaviorEvent(
                event_type="EATING",
                severity=_EVENT_SEVERITY["EATING"],
                confidence=0.70,
                detail="Cup near mouth",
            ))

        # SMOKING: elongated object + hand near face + mouth touch
        if (
            inputs.elongated_object_score > 0.45
            and inputs.hand_face_proximity_score > 0.45
            and inputs.mouth_touch_detected
        ):
            smoke_conf = min(1.0,
                inputs.elongated_object_score * 0.4
                + inputs.hand_face_proximity_score * 0.4
                + 0.2
            )
            events.append(BehaviorEvent(
                event_type="SMOKING",
                severity=_EVENT_SEVERITY["SMOKING"],
                confidence=round(smoke_conf, 4),
                detail="Elongated object near mouth with hand-face contact",
            ))

        # FOREIGN_OBJECT: phone detected during session
        if inputs.phone_detected:
            events.append(BehaviorEvent(
                event_type="FOREIGN_OBJECT",
                severity=_EVENT_SEVERITY["FOREIGN_OBJECT"],
                confidence=0.80,
                detail="Mobile phone detected in frame",
            ))

        # ── STRANGER_DETECTED: non-owner face(s) in frame (immediate) ────────
        if inputs.strangers_in_frame > 0:
            stranger_conf = min(1.0, 0.60 + inputs.strangers_in_frame * 0.20)
            events.append(BehaviorEvent(
                event_type="STRANGER_DETECTED",
                severity=_EVENT_SEVERITY["STRANGER_DETECTED"],
                confidence=round(stranger_conf, 4),
                detail=f"{inputs.strangers_in_frame} unidentified face(s) detected in frame",
            ))

        # ── GAZE_AWAY: iris-based tracking shows owner not looking at screen ─
        if inputs.owner_tracked and not inputs.owner_gaze_looking_at_screen:
            if state.gaze_away_since is None:
                state.gaze_away_since = now
        else:
            state.gaze_away_since = None

        if state.gaze_away_since is not None:
            gaze_away_secs = (now - state.gaze_away_since).total_seconds()
            if gaze_away_secs >= _GAZE_AWAY_SECS:
                events.append(BehaviorEvent(
                    event_type="GAZE_AWAY",
                    severity=_EVENT_SEVERITY["GAZE_AWAY"],
                    confidence=min(1.0, gaze_away_secs / (_GAZE_AWAY_SECS * 2)),
                    detail=f"Owner gaze off-screen for {gaze_away_secs:.0f}s",
                ))

        # ── OWNER_ABSENT: owner face not identified for sustained period ──────
        if not inputs.owner_tracked:
            if state.owner_absent_since is None:
                state.owner_absent_since = now
        else:
            state.owner_absent_since = None

        if state.owner_absent_since is not None:
            owner_absent_secs = (now - state.owner_absent_since).total_seconds()
            if owner_absent_secs >= _OWNER_ABSENT_SECS:
                events.append(BehaviorEvent(
                    event_type="OWNER_ABSENT",
                    severity=_EVENT_SEVERITY["OWNER_ABSENT"],
                    confidence=min(1.0, owner_absent_secs / (_OWNER_ABSENT_SECS * 3)),
                    detail=f"Owner not identified for {owner_absent_secs:.0f}s",
                ))

        return events

    # ------------------------------------------------------------------ #
    # Private helpers                                                      #
    # ------------------------------------------------------------------ #

    def _cleanup(self, now: datetime) -> None:
        expired = [
            sid for sid, state in self._states.items()
            if (now - state.last_seen) > self._expiry
        ]
        for sid in expired:
            self._states.pop(sid, None)


# ══════════════════════════════════════════════════════════════════════════════
# Phase 7 — BehaviorEngine (explicit dt-based API for testing and tooling)
#
# This class uses a signals dict with an explicit time-delta (`dt`) instead of
# wall-clock timestamps.  It is suited for desktop / embedded use cases where
# the caller directly controls the frame loop.  In the web-service context the
# BehaviorStateStore (above) is used instead.
# ══════════════════════════════════════════════════════════════════════════════

from collections import defaultdict  # noqa: E402 (keep at module level but placed here for clarity)


class BehaviorEngine:
    """Event engine that accepts explicit dt and a signals dictionary.

    Usage::

        engine = BehaviorEngine()
        engine.register_callback("DROWSY", lambda ev: print(ev))

        # Per-frame:
        signals = {
            "ear": 0.21,
            "mar": 0.30,
            "spine_angle": 15.0,
            "hand_near_face": False,
            "hand_near_mouth": False,
            "object_near_mouth": None,
            "registered_face_visible": True,
            "unknown_face_visible": False,
            "gaze_on_screen": True,
        }
        engine.update(dt=1/30, signals=signals)
        active = engine.active          # dict[str, bool]
        history = engine.history        # list[BehaviorEvent]
    """

    def __init__(self) -> None:
        self.timers: dict[str, float] = defaultdict(float)
        self.active: dict[str, bool] = {}
        self.history: list[BehaviorEvent] = []
        self.callbacks: dict[str, object] = {}

    def update(self, dt: float, signals: dict) -> None:
        """Process one frame's signals and update all event timers.

        ``signals`` keys:
            ear                      — Eye Aspect Ratio (float)
            mar                      — Mouth Aspect Ratio (float)
            spine_angle              — degrees from vertical (float)
            hand_near_face           — bool
            hand_near_mouth          — bool
            object_near_mouth        — "cup" | "bottle" | "cigarette" | "food" | None
            registered_face_visible  — bool
            unknown_face_visible     — bool
            gaze_on_screen           — bool
        """
        s = signals
        obj = s.get("object_near_mouth")

        self._check("DROWSY",         (s.get("ear", 1.0) or 1.0) < 0.25,          dt, 2.0,  "critical")
        self._check("YAWNING",        (s.get("mar", 0.0) or 0.0) > 0.60,          dt, 1.0,  "info")
        self._check("FACE_TOUCH",     bool(s.get("hand_near_face")),               dt, 0.5,  "warning")
        self._check("SMOKING",        obj == "cigarette",                           dt, 1.0,  "critical")
        self._check("EATING",         obj == "food",                               dt, 2.0,  "warning")
        self._check("DRINKING",       obj in ("cup", "bottle"),                    dt, 2.0,  "warning")
        self._check("LEFT_SCREEN",    not bool(s.get("registered_face_visible")),   dt, 5.0,  "critical")
        self._check("SLOUCHING",      (s.get("spine_angle", 0.0) or 0.0) > 20.0,  dt, 10.0, "warning")
        self._check("DISTRACTED",     not bool(s.get("gaze_on_screen", True)),     dt, 8.0,  "warning")
        self._check("UNKNOWN_PERSON", bool(s.get("unknown_face_visible")),         dt, 0.1,  "critical")

    def register_callback(self, event_type: str, fn: object) -> None:
        """Register a callable that fires when *event_type* becomes active."""
        self.callbacks[event_type] = fn

    def export_session(self, path: str) -> None:
        """Dump the event history to a JSON file."""
        import json
        with open(path, "w", encoding="utf-8") as fh:
            json.dump([vars(e) for e in self.history], fh, indent=2, ensure_ascii=False)

    def reset(self) -> None:
        """Clear all timers, active states, and history."""
        self.timers.clear()
        self.active.clear()
        self.history.clear()

    # ------------------------------------------------------------------ #
    # Private helpers                                                      #
    # ------------------------------------------------------------------ #

    def _check(
        self,
        event_type: str,
        condition: bool,
        dt: float,
        threshold_s: float,
        severity: str,
    ) -> None:
        if condition:
            self.timers[event_type] += dt
            if self.timers[event_type] >= threshold_s and not self.active.get(event_type):
                self.active[event_type] = True
                event = BehaviorEvent(
                    event_type=event_type,
                    severity=_EVENT_SEVERITY.get(event_type, "warning"),
                    confidence=min(1.0, self.timers[event_type] / threshold_s),
                    detail=f"Active for {self.timers[event_type]:.1f}s",
                )
                self.history.append(event)
                cb = self.callbacks.get(event_type)
                if cb is not None:
                    try:
                        cb(event)  # type: ignore[operator]
                    except Exception:
                        logger.debug("Behavior callback for %s raised", event_type, exc_info=True)
        else:
            self.timers[event_type] = 0.0
            self.active[event_type] = False
