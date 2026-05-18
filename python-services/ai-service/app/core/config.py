import logging
import os
from pathlib import Path

from dotenv import load_dotenv


def _load_root_dotenv() -> None:
    for parent in Path(__file__).resolve().parents:
        candidate = parent / ".env"
        if candidate.exists():
            load_dotenv(candidate, override=False)
            break


_load_root_dotenv()

logger = logging.getLogger(__name__)


class Settings:
    app_name: str = "ai-service"
    app_version: str = "2.0.0"

    # Primary AI provider: "openai-compatible" | "ollama" | "mock"
    ai_provider: str = os.getenv("AI_PROVIDER", "openai-compatible").strip().lower()

    # OpenAI-compatible settings
    ai_api_base_url: str = os.getenv("AI_API_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    ai_api_key: str = os.getenv("AI_API_KEY", "").strip()
    model_name: str = os.getenv("AI_MODEL_NAME", "gpt-4.1-mini").strip()

    # Ollama settings (server-level default; per-request values override these)
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
    ollama_model_name: str = os.getenv("OLLAMA_MODEL_NAME", "llama3.2:3b").strip()

    internal_api_key: str = os.getenv("INTERNAL_API_KEY", "change-me-in-real-environments")
    ai_timeout_seconds: float = float(os.getenv("AI_TIMEOUT_SECONDS", "30"))
    ai_readiness_timeout_seconds: float = float(os.getenv("AI_READINESS_TIMEOUT_SECONDS", "10"))
    ai_max_retries: int = int(os.getenv("AI_MAX_RETRIES", "2"))
    ai_temperature: float = float(os.getenv("AI_TEMPERATURE", "0.1"))
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    @property
    def effective_provider(self) -> str:
        """
        Returns the provider that will actually be used at runtime.
        Falls back to 'mock' when openai-compatible is selected but no API key is set,
        so the service stays functional instead of returning 503 on every request.
        """
        if self.ai_provider == "openai-compatible" and not self.ai_api_key:
            return "mock"
        return self.ai_provider

    def log_startup(self) -> None:
        effective = self.effective_provider
        if effective != self.ai_provider:
            logger.warning(
                "AI_PROVIDER is '%s' but AI_API_KEY is not set — "
                "falling back to 'mock' provider. "
                "Set AI_API_KEY in your .env to enable real AI analysis.",
                self.ai_provider,
            )
        else:
            logger.info(
                "AI provider: %s | model: %s | base_url: %s",
                effective,
                self.model_name if effective != "ollama" else self.ollama_model_name,
                self.ai_api_base_url if effective == "openai-compatible" else self.ollama_base_url,
            )


settings = Settings()
