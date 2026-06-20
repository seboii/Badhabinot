from functools import lru_cache

from fastapi import HTTPException

from app.core.config import settings
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.providers import (
    ChatProviderResult,
    MockProvider,
    OllamaProvider,
    OpenAiCompatibleProvider,
    ProviderConfig,
    ProviderConfigurationError,
    ProviderInvocationError,
)


class ChatService:
    def __init__(self, provider: MockProvider | OpenAiCompatibleProvider | OllamaProvider | None = None) -> None:
        self.provider = provider

    async def respond(self, request: ChatRequest) -> ChatResponse:
        try:
            provider = self._resolve_provider(request)
        except ProviderConfigurationError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        try:
            result: ChatProviderResult = await provider.respond_chat(request)
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

    async def stream(self, request: ChatRequest):
        """Async generator yielding JSON event strings for SSE streaming."""
        import json as _json

        try:
            provider = self._resolve_provider(request)
        except ProviderConfigurationError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc

        # Real token streaming providers (Ollama + OpenAI-compatible)
        if isinstance(provider, OllamaProvider):
            async for event_json in provider.stream_chat(request):
                yield event_json
            return
        if isinstance(provider, OpenAiCompatibleProvider):
            async for event_json in provider.stream_chat(request):
                yield event_json
            return

        # Fallback for MockProvider: get full response, simulate char-by-char
        try:
            result: ChatProviderResult = await provider.respond_chat(request)
        except ProviderConfigurationError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except ProviderInvocationError as exc:
            raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
        for char in result.answer:
            yield _json.dumps({"token": char})
        yield _json.dumps({
            "done": True,
            "grounded_facts": result.grounded_facts,
            "follow_up_suggestions": result.follow_up_suggestions,
        })

    def _resolve_provider(
        self, request: ChatRequest
    ) -> MockProvider | OpenAiCompatibleProvider | OllamaProvider:
        """LOCAL → kullanıcının Ollama'sı; API → bulut OpenAI-compatible.

        - LOCAL her zaman önceliklidir (kullanıcının kendi makinesindeki model).
        - Constructor'da provider injection varsa (test/single-tenant)
          ai_mode == "LOCAL" dışındaki her durumda onu kullan.
        - Production'da injection yok → ai_mode'a göre OpenAI veya env default.
        Eksik konfigürasyonda ProviderConfigurationError → 503.
        """
        # 1. LOCAL: kullanıcının kendi Ollama instance'ı (her durumda öncelik)
        if request.ai_mode == "LOCAL":
            if not (request.ollama_base_url and request.local_model_name):
                raise ProviderConfigurationError(
                    "LOCAL mode için ollama_base_url ve local_model_name gerekli."
                )
            return OllamaProvider(
                base_url=request.ollama_base_url,
                model_name=request.local_model_name,
                timeout_seconds=settings.ai_timeout_seconds,
            )
        # 2. Test/explicit injection
        if self.provider is not None:
            return self.provider
        # 3. API: bulut OpenAI-compatible (anahtar varsa)
        if request.ai_mode == "API":
            if settings.ai_api_key:
                return OpenAiCompatibleProvider(_make_openai_config())
            # AI_API_KEY yoksa cloud yerine sunucunun varsayilan saglayicisina dus.
            # AI_PROVIDER=ollama → fine-tune edilmis coach modeli. Boylece kullanici
            # API modunda kalsa bile sohbet, sunucudaki yerel modelle kutu disi calisir.
            return _build_provider()
        # 4. Belirsiz: env varsayılanına düş
        return _build_provider()


def _build_provider() -> MockProvider | OpenAiCompatibleProvider | OllamaProvider:
    effective = settings.effective_provider

    if effective == "mock":
        config = _make_config()
        return MockProvider(config)

    if effective == "ollama":
        return OllamaProvider(
            base_url=settings.ollama_base_url,
            model_name=settings.ollama_model_name,
            timeout_seconds=settings.ai_timeout_seconds,
        )

    if effective == "openai-compatible":
        config = _make_config()
        return OpenAiCompatibleProvider(config)

    raise ProviderConfigurationError(f"Unsupported AI_PROVIDER value: {settings.ai_provider}")


def _make_config() -> ProviderConfig:
    return ProviderConfig(
        provider_name=settings.ai_provider,
        api_base_url=settings.ai_api_base_url,
        api_key=settings.ai_api_key,
        model_name=settings.model_name,
        timeout_seconds=settings.ai_timeout_seconds,
        readiness_timeout_seconds=settings.ai_readiness_timeout_seconds,
        max_retries=settings.ai_max_retries,
        temperature=settings.ai_temperature,
    )


def _make_openai_config() -> ProviderConfig:
    """Per-request API mode için OpenAI-compatible config. provider_name'i
    her zaman 'openai-compatible' olarak ayarlar — env'deki AI_PROVIDER
    'ollama' olsa bile kullanıcı API modunu seçince OpenAI'ye yönlenmesi için.
    """
    return ProviderConfig(
        provider_name="openai-compatible",
        api_base_url=settings.ai_api_base_url,
        api_key=settings.ai_api_key,
        model_name=settings.model_name,
        timeout_seconds=settings.ai_timeout_seconds,
        readiness_timeout_seconds=settings.ai_readiness_timeout_seconds,
        max_retries=settings.ai_max_retries,
        temperature=settings.ai_temperature,
    )


@lru_cache(maxsize=1)
def get_chat_service() -> ChatService:
    return ChatService()
