from fastapi import APIRouter, Depends

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
