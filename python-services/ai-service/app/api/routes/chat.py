import json

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.core.security import require_internal_api_key
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import get_chat_service

router = APIRouter(prefix="/v1/chat", tags=["chat"])


@router.post("/respond", response_model=ChatResponse)
async def respond(
    request: ChatRequest,
    _: None = Depends(require_internal_api_key),
) -> ChatResponse:
    return await get_chat_service().respond(request)


@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    _: None = Depends(require_internal_api_key),
) -> StreamingResponse:
    service = get_chat_service()

    async def generate():
        try:
            async for event_json in service.stream(request):
                yield f"data: {event_json}\n\n"
        except Exception as exc:
            yield f"data: {json.dumps({'error': str(exc)})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
