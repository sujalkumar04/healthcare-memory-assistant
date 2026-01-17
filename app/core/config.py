"""Core configuration and settings."""

from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    # Application
    APP_ENV: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # Qdrant - supports both local (host+port) and cloud (url)
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_URL: str | None = None  # For Qdrant Cloud: https://xxx.qdrant.io
    QDRANT_API_KEY: str | None = None
    QDRANT_COLLECTION_NAME: str = "patient_memories"

    # Embeddings (sentence-transformers)
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION: int = 384

    # LLM (OpenAI)
    OPENAI_API_KEY: str = ""
    OPENAI_LLM_MODEL: str = "gpt-4"


    # Security
    API_KEY_SECRET: str = "change-me-in-production"
    JWT_SECRET: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRY_HOURS: int = 24

    # CORS
    CORS_ORIGINS: List[str] = Field(default=["*"])

    # Redis (optional)
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379


settings = Settings()
