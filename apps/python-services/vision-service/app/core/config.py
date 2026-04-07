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


class Settings:
    app_name: str = "vision-service"
    app_version: str = "2.0.0"
    internal_api_key: str = os.getenv("INTERNAL_API_KEY", "change-me-in-real-environments")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")


settings = Settings()
