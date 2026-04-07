import os


class Settings:
    app_name: str = "ai-service"
    app_version: str = "2.0.0"
    ai_provider: str = os.getenv("AI_PROVIDER", "openai-compatible").strip().lower()
    ai_api_base_url: str = os.getenv("AI_API_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    ai_api_key: str = os.getenv("AI_API_KEY", "").strip()
    model_name: str = os.getenv("AI_MODEL_NAME", "gpt-4.1-mini").strip()
    internal_api_key: str = os.getenv("INTERNAL_API_KEY", "change-me-in-real-environments")
    ai_timeout_seconds: float = float(os.getenv("AI_TIMEOUT_SECONDS", "30"))
    ai_readiness_timeout_seconds: float = float(os.getenv("AI_READINESS_TIMEOUT_SECONDS", "10"))
    ai_max_retries: int = int(os.getenv("AI_MAX_RETRIES", "2"))
    ai_temperature: float = float(os.getenv("AI_TEMPERATURE", "0.1"))
    log_level: str = os.getenv("LOG_LEVEL", "INFO")


settings = Settings()
