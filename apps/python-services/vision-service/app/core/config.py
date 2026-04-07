import os


class Settings:
    app_name: str = "vision-service"
    app_version: str = "2.0.0"
    internal_api_key: str = os.getenv("INTERNAL_API_KEY", "change-me-in-real-environments")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")


settings = Settings()
