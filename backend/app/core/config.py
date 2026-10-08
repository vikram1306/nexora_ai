import os
from typing import List, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Nexora AI"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # Security
    SECRET_KEY: str = "NEXORA_ENTERPRISE_SECRET_KEY_SUPER_SECURE_32BYTES_LONG"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # Database - default to SQLite for instant local dev & fallback if Postgres is not running, or use Postgres URI
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "sqlite:///./nexora.db"
    )

    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # ChromaDB Vector Store
    CHROMA_PERSIST_DIR: str = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")

    # Open-Source Embedding Model
    EMBEDDING_MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"

    # Ollama Local LLM Daemon
    OLLAMA_URL: str = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")

    # Rate Limiting Policy
    RATE_LIMIT_AUTH: str = os.getenv("RATE_LIMIT_AUTH", "5/minute")
    RATE_LIMIT_QUERY: str = os.getenv("RATE_LIMIT_QUERY", "20/minute")
    RATE_LIMIT_INGEST: str = os.getenv("RATE_LIMIT_INGEST", "10/minute")

    # Environment & Observability
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    SENTRY_DSN: Optional[str] = os.getenv("SENTRY_DSN", None)
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_STRUCTURED: bool = os.getenv("LOG_STRUCTURED", "true").lower() in ["1", "true", "yes"]

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000", "*"]

    model_config = SettingsConfigDict(case_sensitive=True)



settings = Settings()
