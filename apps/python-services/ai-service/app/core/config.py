import os


class Settings:
    app_name: str = "ai-service"
    app_version: str = "1.1.0"
    model_name: str = os.getenv("AI_MODEL_NAME", "heuristic-behavior-classifier")
    model_version: str = os.getenv("AI_MODEL_VERSION", "phase-2.1")
    internal_api_key: str = os.getenv("INTERNAL_API_KEY", "change-me-in-real-environments")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")


settings = Settings()
