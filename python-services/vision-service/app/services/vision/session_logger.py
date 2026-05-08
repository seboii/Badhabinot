"""Module H — Session Logging.

Appends behavioral events to a per-session JSONL log file.
Each line is a JSON object representing one frame's events.

Storage:
    logs/sessions/{session_id}.jsonl

The JSON-Lines format is append-only and easy to stream / export.
The companion export_session() function converts a session log to JSON or CSV.
"""

from __future__ import annotations

import csv
import io
import json
import logging
import os
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

_LOG_ROOT = Path(os.getenv("SESSION_LOG_DIR", "logs/sessions"))


def log_frame_events(
    session_id: str,
    user_id: str,
    frame_id: str,
    captured_at: datetime,
    behavior_events: list[dict],  # list of BehaviorEventData-like dicts
) -> None:
    """Append one frame's behavioral events to the session log file.

    No-ops if *behavior_events* is empty (keeps logs lean).
    """
    if not behavior_events:
        return

    _LOG_ROOT.mkdir(parents=True, exist_ok=True)
    log_path = _LOG_ROOT / f"{_safe(session_id)}.jsonl"

    record = {
        "ts": captured_at.isoformat(),
        "session_id": session_id,
        "user_id": user_id,
        "frame_id": frame_id,
        "events": behavior_events,
    }

    try:
        with log_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    except OSError:
        logger.warning("Could not write session log for session=%s", session_id, exc_info=True)


def export_session_json(session_id: str) -> str | None:
    """Return the full session log as a JSON string, or None if no log exists."""
    log_path = _LOG_ROOT / f"{_safe(session_id)}.jsonl"
    if not log_path.exists():
        return None

    records = []
    with log_path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return json.dumps({"session_id": session_id, "frames": records}, ensure_ascii=False, indent=2)


def export_session_csv(session_id: str) -> str | None:
    """Return the session event log as a CSV string, or None if no log exists."""
    log_path = _LOG_ROOT / f"{_safe(session_id)}.jsonl"
    if not log_path.exists():
        return None

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["timestamp", "session_id", "user_id", "frame_id",
                     "event_type", "severity", "confidence", "detail"])

    with log_path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            for event in record.get("events", []):
                writer.writerow([
                    record.get("ts", ""),
                    record.get("session_id", ""),
                    record.get("user_id", ""),
                    record.get("frame_id", ""),
                    event.get("event_type", ""),
                    event.get("severity", ""),
                    event.get("confidence", ""),
                    event.get("detail", ""),
                ])

    return output.getvalue()


def _safe(value: str) -> str:
    """Sanitise a string for use as a filename."""
    return "".join(c for c in value if c.isalnum() or c in "-_")
