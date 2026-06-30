"""Servicio de wallet de créditos.

El saldo vive en `wallets` (una fila por usuario, CHECK >= 0) y es la fuente de
verdad; `creditos_transacciones` es el libro mayor append-only. Toda mutación de
saldo bloquea la fila con `SELECT FOR UPDATE` (regla no negociable) para evitar
condiciones de carrera. Las acreditaciones son idempotentes por `referencia`
(p. ej. el `payment_intent`/`session.id` de Stripe).
"""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.creditos import CreditoTransaccion, Wallet
from src.models.dto.creditos import (
    PaginatedTransaccionesDTO,
    PaqueteDTO,
    TransaccionDTO,
)
from src.models.enums import TipoTransaccionCredito
from src.models.parametros_config import ParametroConfig
from src.services.exceptions import InsufficientCreditsError, ValidationError

# Paquetes de créditos ofrecidos (cantidades).
PAQUETES_CREDITOS = [5, 10, 20, 50]
PRECIO_CREDITO_DEFAULT = 50


async def _lock_wallet(session: AsyncSession, usuario_id: uuid.UUID) -> Wallet:
    """Garantiza la existencia del wallet (on-demand) y lo bloquea para update."""
    await session.execute(
        pg_insert(Wallet)
        .values(usuario_id=usuario_id)
        .on_conflict_do_nothing(index_elements=["usuario_id"])
    )
    return (
        await session.execute(
            select(Wallet).where(Wallet.usuario_id == usuario_id).with_for_update()
        )
    ).scalar_one()


async def _ya_procesada(session: AsyncSession, referencia: str) -> bool:
    existe = await session.scalar(
        select(CreditoTransaccion.id).where(
            CreditoTransaccion.referencia_stripe == referencia
        )
    )
    return existe is not None


async def get_precio_credito(session: AsyncSession) -> int:
    """Precio en MXN de un crédito (de `parametros_config`, default 50)."""
    valor = await session.scalar(
        select(ParametroConfig.valor_cifrado).where(
            ParametroConfig.clave == "precio_credito_mxn"
        )
    )
    try:
        return int(valor)
    except (TypeError, ValueError):
        return PRECIO_CREDITO_DEFAULT


async def list_paquetes(session: AsyncSession) -> list[PaqueteDTO]:
    """Paquetes disponibles con su precio total derivado del precio por crédito."""
    precio = await get_precio_credito(session)
    return [
        PaqueteDTO(
            cantidad=c,
            precio_unitario_mxn=precio,
            precio_total_mxn=c * precio,
        )
        for c in PAQUETES_CREDITOS
    ]


async def get_balance(session: AsyncSession, usuario_id: uuid.UUID) -> Wallet:
    """Devuelve el wallet del usuario (transitorio con saldo 0 si aún no existe)."""
    wallet = await session.scalar(
        select(Wallet).where(Wallet.usuario_id == usuario_id)
    )
    return wallet or Wallet(
        usuario_id=usuario_id, saldo_creditos=0, saldo_pendiente_retiro=0
    )


async def list_historial(
    session: AsyncSession,
    usuario_id: uuid.UUID,
    page: int = 1,
    page_size: int = 20,
) -> PaginatedTransaccionesDTO:
    """Historial paginado de transacciones del usuario (más recientes primero)."""
    total = await session.scalar(
        select(func.count())
        .select_from(CreditoTransaccion)
        .where(CreditoTransaccion.usuario_id == usuario_id)
    )
    rows = (
        await session.scalars(
            select(CreditoTransaccion)
            .where(CreditoTransaccion.usuario_id == usuario_id)
            .order_by(CreditoTransaccion.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).all()
    return PaginatedTransaccionesDTO(
        items=[
            TransaccionDTO(
                id=str(t.id),
                tipo=t.tipo.value,
                monto=t.monto,
                descripcion=t.descripcion,
                referencia_stripe=t.referencia_stripe,
                created_at=t.created_at,
            )
            for t in rows
        ],
        total=total or 0,
        page=page,
        page_size=page_size,
    )


async def add_credits(
    session: AsyncSession,
    usuario_id: uuid.UUID,
    monto: int,
    *,
    descripcion: str,
    tipo: TipoTransaccionCredito = TipoTransaccionCredito.compra,
    referencia: str | None = None,
    campana_id: uuid.UUID | None = None,
) -> Wallet:
    """Acredita `monto` créditos. Idempotente si se pasa `referencia` ya usada."""
    if monto <= 0:
        raise ValidationError("El monto debe ser positivo")

    if referencia is not None and await _ya_procesada(session, referencia):
        # Webhook/operación duplicada: no se vuelve a acreditar.
        return await get_balance(session, usuario_id)

    wallet = await _lock_wallet(session, usuario_id)
    wallet.saldo_creditos += monto
    session.add(
        CreditoTransaccion(
            usuario_id=usuario_id,
            tipo=tipo,
            monto=monto,
            referencia_stripe=referencia,
            campana_id=campana_id,
            descripcion=descripcion,
        )
    )
    await session.commit()
    return wallet


async def deduct_credits(
    session: AsyncSession,
    usuario_id: uuid.UUID,
    monto: int,
    *,
    descripcion: str,
    tipo: TipoTransaccionCredito = TipoTransaccionCredito.gasto,
    referencia: str | None = None,
    campana_id: uuid.UUID | None = None,
) -> Wallet:
    """Descuenta `monto` créditos. → 409 si el saldo es insuficiente."""
    if monto <= 0:
        raise ValidationError("El monto debe ser positivo")

    wallet = await _lock_wallet(session, usuario_id)
    if wallet.saldo_creditos < monto:
        raise InsufficientCreditsError("Saldo de créditos insuficiente")

    wallet.saldo_creditos -= monto
    session.add(
        CreditoTransaccion(
            usuario_id=usuario_id,
            tipo=tipo,
            monto=monto,
            referencia_stripe=referencia,
            campana_id=campana_id,
            descripcion=descripcion,
        )
    )
    await session.commit()
    return wallet
