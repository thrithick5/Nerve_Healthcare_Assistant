from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    APP_NAME: str = "Nerve"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False

    SECRET_KEY: str = "healthcare-assistant-secret-key-change-in-production-2024"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    MISTRAL_API_KEY: Optional[str] = None
    MISTRAL_MODEL: str = "mistral-large-latest"
    MISTRAL_EMBEDDING_MODEL: str = "mistral-embed"

    DATABASE_URL: str = "sqlite:///./data/healthcare.db"
    CHROMA_PERSIST_DIR: str = "data/chroma_db"
    COLLECTION_NAME: str = "medical_knowledge"

    CHUNK_SIZE: int = 1024
    CHUNK_OVERLAP: int = 128
    TOP_K_RETRIEVAL: int = 8

    MAX_HISTORY_LENGTH: int = 30
    MAX_TOKENS: int = 16000
    TEMPERATURE: float = 0.3

    GOOGLE_CLIENT_ID: str = ""

    ENABLE_WEB_SEARCH: bool = False
    ENABLE_SCRAPER: bool = True

    HEALTH_DISCLAIMER: str = (
        "I am an AI assistant for informational support only. "
        "Not a substitute for professional medical advice. "
        "Always consult a healthcare professional."
    )

    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    ]

    CORS_ORIGINS_EXTRA: str = ""
    CORS_ORIGIN_REGEX: str = r"https://.*\.vercel\.app"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @property
    def effective_cors_origins(self) -> list[str]:
        origins = list(self.CORS_ORIGINS)
        if self.CORS_ORIGINS_EXTRA:
            extras = [o.strip().rstrip("/") for o in self.CORS_ORIGINS_EXTRA.split(",") if o.strip()]
            origins.extend(extras)
        return origins
