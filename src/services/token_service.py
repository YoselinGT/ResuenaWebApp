"""Servicio de tokens de un solo uso (confirmación, reset, registro).

Reglas no negociables (CLAUDE.md):
- Tokens de un solo uso: verificar con `SELECT FOR UPDATE` antes de consumir.
- Nunca loguear el valor del token.

El token es una cadena opaca generada con `secrets.token_urlsafe` (≈256 bits de
entropía), más fuerte que un UUID y apta para incrustar en URLs de email.
"""

from __future__ import annotations

import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.enums import TipoToken
from src.models.tokens import Token
from src.services.exceptions import (
    TokenConsumidoError,
    TokenExpiradoError,
    TokenInvalidoError,
)

_TOKEN_BYTES = 32


async def create(
    session: AsyncSession,
    tipo: TipoToken,
    usuario_id,
    ttl_minutes: int,
) -> str:
    """Crea y persiste un token; devuelve su valor en claro (para el email)."""
    valor = secrets.token_urlsafe(_TOKEN_BYTES)
    token = Token(
        token=valor,
        tipo=tipo,
        usuario_id=usuario_id,
        expires_at=datetime.now(UTC) + timedelta(minutes=ttl_minutes),
    )
    session.add(token)
    await session.flush()
    return valor


async def consume(
    session: AsyncSession,
    valor: str,
    tipo: TipoToken | None = None,
) -> Token:
    """Consume un token de un solo uso de forma atómica.

    Bloquea la fila con SELECT FOR UPDATE, valida vigencia y unicidad de uso,
    y marca `consumed_at`. Lanza excepción tipada si es inválido/expirado/usado.
    """
    stmt = select(Token).where(Token.token == valor).with_for_update()
    if tipo is not None:
        stmt = stmt.where(Token.tipo == tipo)

    token = (await session.execute(stmt)).scalar_one_or_none()
    if token is None:
        raise TokenInvalidoError("Token inexistente o de tipo incorrecto")
    if token.consumed_at is not None:
        raise TokenConsumidoError("El token ya fue utilizado")
    if token.expires_at <= datetime.now(UTC):
        raise TokenExpiradoError("El token ha expirado")

    token.consumed_at = datetime.now(UTC)
    await session.flush()
    return token
