"""Application configuration using Pydantic settings."""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings."""

    # Database
    database_url: str = "sqlite:///./supervisor.db"

    # Security
    secret_key: str = "dev-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24  # 24 hours

    # Federated index
    federated_index_url: str = "http://localhost:8001"
    federated_index_timeout: int = 5

    # CORS
    cors_origins: list[str] = ["http://localhost:5173"]

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
