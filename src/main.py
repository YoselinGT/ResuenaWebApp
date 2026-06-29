"""Entry point de la API FastAPI de Resuena.

Configura logging estructurado, el router raíz y el endpoint de salud.
La lógica de negocio vive en src/services; este módulo solo cablea la app.
"""

import structlog
from fastapi import FastAPI

from src.api import api_router
from src.api.errors import register_exception_handlers
from src.config.settings import get_settings
from src.middleware.auth import AuthMiddleware

# ── Logging estructurado (JSON) ──────────────────────────────────
structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
)
logger = structlog.get_logger()

settings = get_settings()

app = FastAPI(
    title="Resuena API",
    description="Plataforma de gestión de campañas musicales.",
    version="0.1.0",
)

app.add_middleware(AuthMiddleware)
register_exception_handlers(app)

app.include_router(api_router)


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    """Healthcheck usado por Docker y balanceadores."""
    return {"status": "ok", "service": "api"}


@app.on_event("startup")
async def on_startup() -> None:
    logger.info("api.startup", environment=settings.environment)
