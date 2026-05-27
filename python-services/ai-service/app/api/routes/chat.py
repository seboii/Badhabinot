import asyncio
import contextlib
import json

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.core.security import require_internal_api_key
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import get_chat_service

router = APIRouter(prefix="/v1/chat", tags=["chat"])

# Send an SSE comment every N seconds while waiting for the first token.
# SSE comments (": ...\n\n") are ignored by clients but reset proxy read-timeouts
# and the backend WebClient's ReadTimeoutHandler, preventing premature disconnects
# on slow local models with long TTFT (time-to-first-token).
_KEEPALIVE_INTERVAL_SECONDS = 15.0


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
        queue: asyncio.Queue[str | None] = asyncio.Queue()

        async def fill_queue() -> None:
            try:
                async for event_json in service.stream(request):
                    await queue.put(event_json)
            except Exception as exc:
                await queue.put(json.dumps({"error": str(exc)}))
            finally:
                await queue.put(None)  # sentinel — signals end of stream

        task = asyncio.create_task(fill_queue())
        try:
            while True:
                try:
                    item = await asyncio.wait_for(
                        queue.get(), timeout=_KEEPALIVE_INTERVAL_SECONDS
                    )
                    if item is None:
                        break
                    yield f"data: {item}\n\n"
                except asyncio.TimeoutError:
                    # No token yet — send SSE comment to keep the connection alive
                    yield ": keepalive\n\n"
        finally:
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
