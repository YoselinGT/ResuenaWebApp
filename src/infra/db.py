"""Engine async y fábrica de sesiones de SQLAlchemy.

Punto único de acceso a la BD para la capa de repositorios. La URL viene de
settings (asyncpg). Dependencia FastAPI `get_session` para inyectar sesiones.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.config.settings import get_settings

settings = get_settings()

# pool_pre_ping evita errores por conexiones muertas; el tuning fino del pool
# se ajusta en fases de performance.
engine = create_async_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)

SessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    autoflush=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependencia FastAPI: cede una sesión y la cierra al terminar."""
    async with SessionLocal() as session:
        yield session
