"""Tests for Module H: SessionLogger — JSONL write, JSON/CSV export, sanitisation."""

from __future__ import annotations

import csv
import io
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

import app.services.vision.session_logger as sl


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _ts() -> datetime:
    return datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)


def _event(event_type: str = "FACE_TOUCH", severity: str = "low", confidence: float = 0.8) -> dict:
    return {"event_type": event_type, "severity": severity, "confidence": confidence, "detail": "test"}


# ─────────────────────────────────────────────────────────────────────────────
# 1. log_frame_events — basic write
# ─────────────────────────────────────────────────────────────────────────────

def test_log_frame_events_creates_jsonl(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sl, "_LOG_ROOT", tmp_path)

    sl.log_frame_events("sess1", "user1", "frame1", _ts(), [_event()])

    log_file = tmp_path / "sess1.jsonl"
    assert log_file.exists()

    with log_file.open() as f:
        record = json.loads(f.readline())

    assert record["session_id"] == "sess1"
    assert record["user_id"] == "user1"
    assert record["frame_id"] == "frame1"
    assert len(record["events"]) == 1
    assert record["events"][0]["event_type"] == "FACE_TOUCH"


def test_log_frame_events_appends_multiple_frames(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sl, "_LOG_ROOT", tmp_path)

    sl.log_frame_events("sess2", "u", "f1", _ts(), [_event("YAWNING")])
    sl.log_frame_events("sess2", "u", "f2", _ts(), [_event("DROWSY")])

    log_file = tmp_path / "sess2.jsonl"
    lines = [l for l in log_file.read_text().splitlines() if l.strip()]
    assert len(lines) == 2
    assert json.loads(lines[0])["frame_id"] == "f1"
    assert json.loads(lines[1])["frame_id"] == "f2"


def test_log_frame_events_noop_when_empty(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sl, "_LOG_ROOT", tmp_path)

    sl.log_frame_events("sess3", "u", "f1", _ts(), [])

    # No file should be created when there are no events
    assert not (tmp_path / "sess3.jsonl").exists()


def test_log_frame_events_stores_iso_timestamp(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sl, "_LOG_ROOT", tmp_path)

    ts = datetime(2026, 6, 15, 9, 30, 45, tzinfo=timezone.utc)
    sl.log_frame_events("sess4", "u", "f1", ts, [_event()])

    record = json.loads((tmp_path / "sess4.jsonl").read_text().strip())
    assert "2026-06-15" in record["ts"]


# ─────────────────────────────────────────────────────────────────────────────
# 2. log_frame_events — error handling
# ─────────────────────────────────────────────────────────────────────────────

def test_log_frame_events_survives_oserror(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """OSError on write must be swallowed — not propagate."""
    monkeypatch.setattr(sl, "_LOG_ROOT", tmp_path)

    def _bad_open(*args, **kwargs):  # noqa: ANN001
        raise OSError("disk full")

    # Monkeypatch Path.open to raise on write
    monkeypatch.setattr(Path, "open", _bad_open)

    # Should not raise
    sl.log_frame_events("sess5", "u", "f1", _ts(), [_event()])


# ─────────────────────────────────────────────────────────────────────────────
# 3. export_session_json
# ─────────────────────────────────────────────────────────────────────────────

def test_export_session_json_returns_none_when_no_log(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sl, "_LOG_ROOT", tmp_path)
    assert sl.export_session_json("nonexistent") is None


def test_export_session_json_correct_structure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sl, "_LOG_ROOT", tmp_path)

    sl.log_frame_events("sjson1", "u1", "f1", _ts(), [_event("SMOKING", "high", 0.9)])
    sl.log_frame_events("sjson1", "u1", "f2", _ts(), [_event("DROWSY", "high", 0.7)])

    result = sl.export_session_json("sjson1")
    assert result is not None

    data = json.loads(result)
    assert data["session_id"] == "sjson1"
    assert len(data["frames"]) == 2
    assert data["frames"][0]["frame_id"] == "f1"
    assert data["frames"][1]["frame_id"] == "f2"
    assert data["frames"][0]["events"][0]["event_type"] == "SMOKING"


def test_export_session_json_multiple_events_per_frame(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sl, "_LOG_ROOT", tmp_path)

    sl.log_frame_events("sjson2", "u", "f1", _ts(), [_event("FACE_TOUCH"), _event("YAWNING")])

    data = json.loads(sl.export_session_json("sjson2"))
    assert len(data["frames"][0]["events"]) == 2


# ─────────────────────────────────────────────────────────────────────────────
# 4. export_session_csv
# ─────────────────────────────────────────────────────────────────────────────

def test_export_session_csv_returns_none_when_no_log(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sl, "_LOG_ROOT", tmp_path)
    assert sl.export_session_csv("nonexistent") is None


def test_export_session_csv_has_correct_columns(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sl, "_LOG_ROOT", tmp_path)

    sl.log_frame_events("scsv1", "u1", "f1", _ts(), [_event("LEFT_SCREEN", "high", 0.95)])

    result = sl.export_session_csv("scsv1")
    assert result is not None

    reader = csv.DictReader(io.StringIO(result))
    expected_columns = {"timestamp", "session_id", "user_id", "frame_id",
                        "event_type", "severity", "confidence", "detail"}
    assert set(reader.fieldnames or []) == expected_columns


def test_export_session_csv_one_row_per_event(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sl, "_LOG_ROOT", tmp_path)

    sl.log_frame_events("scsv2", "u", "f1", _ts(), [_event("DROWSY"), _event("SLOUCHING")])
    sl.log_frame_events("scsv2", "u", "f2", _ts(), [_event("SMOKING")])

    result = sl.export_session_csv("scsv2")
    rows = list(csv.DictReader(io.StringIO(result)))
    assert len(rows) == 3  # 2 from frame1 + 1 from frame2


def test_export_session_csv_correct_values(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sl, "_LOG_ROOT", tmp_path)

    sl.log_frame_events("scsv3", "user99", "frame42", _ts(), [_event("UNKNOWN_PERSON", "high", 0.88)])

    rows = list(csv.DictReader(io.StringIO(sl.export_session_csv("scsv3"))))
    assert rows[0]["session_id"] == "scsv3"
    assert rows[0]["user_id"] == "user99"
    assert rows[0]["frame_id"] == "frame42"
    assert rows[0]["event_type"] == "UNKNOWN_PERSON"
    assert rows[0]["severity"] == "high"
    assert float(rows[0]["confidence"]) == pytest.approx(0.88)


# ─────────────────────────────────────────────────────────────────────────────
# 5. _safe — filename sanitisation
# ─────────────────────────────────────────────────────────────────────────────

def test_safe_allows_alphanumeric_and_dash_underscore() -> None:
    assert sl._safe("abc-123_XYZ") == "abc-123_XYZ"


def test_safe_strips_path_traversal() -> None:
    result = sl._safe("../../../etc/passwd")
    assert "/" not in result
    assert "." not in result


def test_safe_strips_spaces_and_special_chars() -> None:
    result = sl._safe("session id!@#$")
    assert result == "sessionid"


def test_safe_empty_string() -> None:
    assert sl._safe("") == ""


# ─────────────────────────────────────────────────────────────────────────────
# 6. Directory creation
# ─────────────────────────────────────────────────────────────────────────────

def test_log_creates_missing_log_directory(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    nested = tmp_path / "deep" / "nested" / "logs"
    monkeypatch.setattr(sl, "_LOG_ROOT", nested)

    # Directory does not exist yet
    assert not nested.exists()

    sl.log_frame_events("sess6", "u", "f1", _ts(), [_event()])

    assert nested.exists()
    assert (nested / "sess6.jsonl").exists()
