"""Servicio de bitácora — registro de acciones críticas (auditoría).

Toda acción crítica (login, registro, reset, aprobación, etc.) se persiste en
`bitacora_eventos`. Nunca se registran passwords, tokens ni datos bancarios.
"""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.models.bitacora_eventos import BitacoraEvento


async def registrar(
    session: AsyncSession,
    *,
    accion: str,
    entidad: str,
    entidad_id: str | None = None,
    autor_id: uuid.UUID | None = None,
    detalle: dict | None = None,
    correlation_id: str | None = None,
) -> None:
    """Inserta un evento en la bitácora (no hace commit; lo hace el caller)."""
    session.add(
        BitacoraEvento(
            accion=accion,
            entidad=entidad,
            entidad_id=str(entidad_id) if entidad_id is not None else None,
            autor_id=autor_id,
            detalle=detalle,
            correlation_id=correlation_id,
        )
    )
    await session.flush()
