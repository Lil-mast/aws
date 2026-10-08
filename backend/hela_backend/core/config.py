"""
core/config.py
──────────────
Central application settings loaded from environment variables / .env file.
All other modules import from here — never read os.environ directly.
"""

from functools import lru_cache
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── App ──────────────────────────────────────────────────────────────────
    app_env: str = "development"
    debug: bool = True

    # ── Security ─────────────────────────────────────────────────────────────
    secret_key: str = "change-me-to-a-random-64-char-secret"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # ── Database ─────────────────────────────────────────────────────────────
    # Empty → fall back to SQLite for local development.
    database_url: str = ""

    @property
    def effective_database_url(self) -> str:
        """Return the resolved database URL (SQLite fallback for dev)."""
        if self.database_url:
            return self.database_url
        return "sqlite+aiosqlite:///./hela_dev.db"

    # ── CORS ─────────────────────────────────────────────────────────────────
    allowed_origins: str = "http://localhost:5173,http://localhost:3000"

    @property
    def cors_origins(self) -> List[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]

    # ── Google OAuth ─────────────────────────────────────────────────────────
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/api/v1/auth/google/callback"

    # ── AWS Bedrock ───────────────────────────────────────────────────────────
    ai_provider: str = "local"
    bedrock_region: str = "us-east-1"
    bedrock_nova_lite_model_id: str = (
        "arn:aws:bedrock:us-east-1::foundation-model/amazon.nova-lite-v1:0"
    )
    bedrock_nova_micro_model_id: str = (
        "arn:aws:bedrock:us-east-1::foundation-model/amazon.nova-micro-v1:0"
    )
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""

    # ── Hela Score ────────────────────────────────────────────────────────────
    score_engine_version: int = 1
    score_min_data_days: int = 30


@lru_cache
def get_settings() -> Settings:
    """Return a cached singleton Settings instance."""
    return Settings()
