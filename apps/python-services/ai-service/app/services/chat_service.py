from functools import lru_cache

from fastapi import HTTPException

from app.core.config import settings
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.providers import (
    ChatProviderResult,
    MockProvider,
    OpenAiCompatibleProvider,
    ProviderConfig,
    ProviderConfigurationError,
    ProviderInvocationError,
)


class ChatService:
    def __init__(self, provider: MockProvider | OpenAiCompatibleProvider | None = None) -> None:
        self.provider = provider

    async def respond(self, request: ChatRequest) -> ChatResponse:
        try:
            result: ChatProviderResult = await self._provider().respond_chat(request)
        except ProviderConfigurationError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except ProviderInvocationError as exc:
            raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc

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

    def _provider(self) -> MockProvider | OpenAiCompatibleProvider:
        if self.provider is None:
            self.provider = _build_provider()
        return self.provider


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
    if settings.ai_provider == "openai-compatible":
        return OpenAiCompatibleProvider(config)
    raise ProviderConfigurationError(f"Unsupported AI_PROVIDER value: {settings.ai_provider}")


@lru_cache(maxsize=1)
def get_chat_service() -> ChatService:
    return ChatService()
