"""Configuración central de la aplicación basada en variables de entorno.

Usa pydantic-settings: las variables se leen del entorno (o del .env en dev)
y se validan al arrancar. Nunca hay secretos hardcodeados.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Settings de la aplicación. Una instancia cacheada por proceso."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ── Entorno ──────────────────────────────────────────────
    environment: Literal["development", "staging", "production"] = "development"
    app_secret_key: str = Field(min_length=32)

    # ── Base de datos ────────────────────────────────────────
    database_url: str = "postgresql+asyncpg://portal:portal@postgres:5432/resuena"

    # ── Redis ────────────────────────────────────────────────
    redis_url: str = "redis://redis:6379/0"

    # ── RabbitMQ ─────────────────────────────────────────────
    rabbitmq_url: str = "amqp://guest:guest@rabbitmq:5672/"

    # ── Almacenamiento (StorageProvider) ─────────────────────
    storage_provider: Literal["s3", "gcs", "azure"] = "s3"
    aws_access_key_id: str = "test"
    aws_secret_access_key: str = "test"
    aws_region: str = "us-east-1"
    aws_s3_bucket: str = "resuena-dev"
    aws_endpoint_url: str | None = None  # vacío en prod, LocalStack en dev

    # ── Email ────────────────────────────────────────────────
    smtp_host: str = "mailhog"
    smtp_port: int = 1025
    smtp_from: str = "no-reply@resuena.local"

    # ── Stripe ───────────────────────────────────────────────
    stripe_secret_key: str = ""
    stripe_publishable_key: str = ""
    stripe_webhook_secret: str = ""

    # ── Observabilidad ───────────────────────────────────────
    sentry_dsn: str = ""

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    """Devuelve la instancia única de Settings (cacheada)."""
    return Settings()  # type: ignore[call-arg]
