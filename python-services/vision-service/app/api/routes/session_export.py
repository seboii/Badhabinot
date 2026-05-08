"""Module H — Session log export endpoints.

Endpoints:
    GET /v1/vision/sessions/{session_id}/export.json
    GET /v1/vision/sessions/{session_id}/export.csv
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse

from app.core.security import require_internal_api_key
from app.services.vision.session_logger import export_session_csv, export_session_json

router = APIRouter(prefix="/v1/vision/sessions", tags=["session-export"])


@router.get("/{session_id}/export.json", response_class=PlainTextResponse)
async def export_json(
    session_id: str,
    _: None = Depends(require_internal_api_key),
) -> PlainTextResponse:
    data = export_session_json(session_id)
    if data is None:
        raise HTTPException(status_code=404, detail=f"No log found for session {session_id!r}")
    return PlainTextResponse(content=data, media_type="application/json")


@router.get("/{session_id}/export.csv", response_class=PlainTextResponse)
async def export_csv(
    session_id: str,
    _: None = Depends(require_internal_api_key),
) -> PlainTextResponse:
    data = export_session_csv(session_id)
    if data is None:
        raise HTTPException(status_code=404, detail=f"No log found for session {session_id!r}")
    return PlainTextResponse(content=data, media_type="text/csv")
