import os


class Settings:
    app_name: str = "vision-service"
    app_version: str = "1.1.0"
    ai_service_url: str = os.getenv("AI_SERVICE_URL", "http://localhost:8092")
    ai_service_timeout_seconds: float = float(os.getenv("AI_SERVICE_TIMEOUT_SECONDS", "5"))
    internal_api_key: str = os.getenv("INTERNAL_API_KEY", "change-me-in-real-environments")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")


settings = Settings()
