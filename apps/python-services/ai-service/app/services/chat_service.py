from functools import lru_cache

from app.schemas.chat import ChatRequest, ChatResponse
from app.services.providers import (
    ChatProviderResult,
    MockProvider,
    OpenAiCompatibleProvider,
    ProviderConfig,
)
from app.core.config import settings


class ChatService:
    def __init__(self, provider: MockProvider | OpenAiCompatibleProvider | None = None) -> None:
        self.provider = provider or _build_provider()

    async def respond(self, request: ChatRequest) -> ChatResponse:
        result: ChatProviderResult = await self.provider.respond_chat(request)
        return ChatResponse(
            conversation_id=request.conversation_id,
            answer=result.answer,
            grounded_facts=result.grounded_facts,
            follow_up_suggestions=result.follow_up_suggestions,
            model={
                "provider": result.provider,
                "name": result.model_name,
                "mode": result.model_mode,
            },
        )


def _build_provider() -> MockProvider | OpenAiCompatibleProvider:
    config = ProviderConfig(
        provider_name=settings.ai_provider,
        api_base_url=settings.ai_api_base_url,
        api_key=settings.ai_api_key,
        model_name=settings.model_name,
        timeout_seconds=settings.ai_timeout_seconds,
        readiness_timeout_seconds=settings.ai_readiness_timeout_seconds,
        max_retries=settings.ai_max_retries,
        temperature=settings.ai_temperature,
    )
    if settings.ai_provider == "mock":
        return MockProvider(config)
    return OpenAiCompatibleProvider(config)


@lru_cache(maxsize=1)
def get_chat_service() -> ChatService:
    return ChatService()
