"""Servicio de paquetes de créditos.

Reemplaza la lógica hardcodeada de la fase 06. Los paquetes viven en
`paquetes_creditos` y los parámetros de config (comisión, fees Stripe)
en `parametros_config`. Todos los campos derivados se calculan aquí
y **nunca** se almacenan en BD.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.paquetes_creditos import PaqueteCredito
from src.models.parametros_config import ParametroConfig
from src.services.exceptions import ConflictError, NotFoundError, ValidationError


# ── Configuración leída de BD ─────────────────────────────────────


@dataclass(frozen=True)
class StripeConfig:
    pct_nacional: Decimal
    fixed_usd: Decimal
    pct_internacional: Decimal
    pct_conversion_moneda: Decimal
    pct_oxxo: Decimal
    escenario_default: str


@dataclass(frozen=True)
class CreditosConfig:
    precio_individual_usd: Decimal
    comision_resuena_pct: int
    stripe: StripeConfig


async def _get_param(session: AsyncSession, clave: str, default: str) -> str:
    valor = await session.scalar(
        select(ParametroConfig.valor_cifrado).where(
            ParametroConfig.clave == clave
        )
    )
    return valor if valor is not None else default


async def get_creditos_config(session: AsyncSession) -> CreditosConfig:
    """Lee los 9 parámetros de créditos/Stripe de `parametros_config`."""
    return CreditosConfig(
        precio_individual_usd=Decimal(
            await _get_param(session, "precio_credito_individual_usd", "2.00")
        ),
        comision_resuena_pct=int(
            await _get_param(session, "comision_resuena_pct", "50")
        ),
        stripe=StripeConfig(
            pct_nacional=Decimal(
                await _get_param(session, "stripe_pct_nacional", "0.036")
            ),
            fixed_usd=Decimal(
                await _get_param(session, "stripe_fixed_usd", "0.17")
            ),
            pct_internacional=Decimal(
                await _get_param(session, "stripe_pct_internacional", "0.005")
            ),
            pct_conversion_moneda=Decimal(
                await _get_param(session, "stripe_pct_conversion_moneda", "0.02")
            ),
            pct_oxxo=Decimal(
                await _get_param(session, "stripe_pct_oxxo", "0.04")
            ),
            escenario_default=await _get_param(
                session, "stripe_escenario_default", "nacional"
            ),
        ),
    )


# ── Cálculos de precios ───────────────────────────────────────────


def calcular_precio_artista(
    precio_neto_usd: Decimal,
    escenario: str = "nacional",
    con_conversion: bool = False,
    *,
    stripe: StripeConfig,
) -> Decimal:
    """Calcula cuánto debe pagar el artista para que Resuena reciba `precio_neto`.

    Fórmula: precio_artista = (precio_neto + fixed) / (1 - pct_total)
    """
    pct = stripe.pct_nacional  # base siempre

    if escenario == "internacional":
        pct += stripe.pct_internacional
    elif escenario == "oxxo":
        pct = stripe.pct_oxxo  # reemplaza base

    if con_conversion:
        pct += stripe.pct_conversion_moneda

    fixed = stripe.fixed_usd
    precio_artista = (precio_neto_usd + fixed) / (1 - pct)
    return precio_artista.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calcular_campos(
    paquete: PaqueteCredito,
    comision_global: int,
    stripe: StripeConfig,
) -> dict:
    """Calcula todos los campos derivados de un paquete.

    Ningún valor se almacena en BD.
    """
    comision = paquete.comision_pct if paquete.comision_pct is not None else comision_global
    ppc = paquete.precio_total_usd / paquete.cantidad_creditos  # precio por crédito
    stripe_fee = paquete.precio_total_usd * stripe.pct_nacional + stripe.fixed_usd
    artista_paga = paquete.precio_total_usd + stripe_fee
    curador_ppc = ppc * (100 - comision) / 100
    resuena_ppc = ppc * comision / 100

    return {
        "precio_por_credito_usd": ppc.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
        "stripe_fee_estimado_usd": stripe_fee.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
        "artista_paga_estimado_usd": artista_paga.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
        "curador_recibe_por_credito_usd": curador_ppc.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
        "resuena_por_credito_usd": resuena_ppc.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
    }


def get_comision_efectiva(paquete: PaqueteCredito, comision_global: int) -> int:
    """Devuelve la comisión aplicable: la del paquete o la global."""
    return paquete.comision_pct if paquete.comision_pct is not None else comision_global


# ── CRUD ──────────────────────────────────────────────────────────


async def list_all(session: AsyncSession) -> list[dict]:
    """Todos los paquetes (admin) + campos calculados + transacciones_count."""
    config = await get_creditos_config(session)
    rows = (
        await session.execute(
            select(PaqueteCredito).order_by(PaqueteCredito.created_at.desc())
        )
    ).scalars().all()

    result = []
    for p in rows:
        # Contar transacciones que referencian este paquete (via metadata o FK futura).
        # Por ahora, 0 — se conectará cuando el checkout use paquete_id.
        tx_count = 0
        campos = calcular_campos(p, config.comision_resuena_pct, config.stripe)
        result.append(
            {
                "id": str(p.id),
                "nombre": p.nombre,
                "cantidad_creditos": p.cantidad_creditos,
                "precio_total_usd": p.precio_total_usd,
                "comision_pct": p.comision_pct,
                "descripcion": p.descripcion,
                "activo": p.activo,
                "visible": p.visible,
                "destacado": p.destacado,
                "transacciones_count": tx_count,
                "calculado": campos,
                "created_at": p.created_at,
                "updated_at": p.updated_at,
            }
        )
    return result


async def list_activos(session: AsyncSession) -> list[dict]:
    """Solo paquetes activos y visibles (catálogo del artista)."""
    config = await get_creditos_config(session)
    rows = (
        await session.execute(
            select(PaqueteCredito)
            .where(PaqueteCredito.activo.is_(True), PaqueteCredito.visible.is_(True))
            .order_by(PaqueteCredito.created_at.desc())
        )
    ).scalars().all()

    return [
        {
            "id": str(p.id),
            "nombre": p.nombre,
            "cantidad_creditos": p.cantidad_creditos,
            "precio_total_usd": p.precio_total_usd,
            "descripcion": p.descripcion,
            "destacado": p.destacado,
            "calculado": calcular_campos(p, config.comision_resuena_pct, config.stripe),
        }
        for p in rows
    ]


async def get_by_id(session: AsyncSession, paquete_id: uuid.UUID) -> PaqueteCredito:
    paquete = await session.get(PaqueteCredito, paquete_id)
    if paquete is None:
        raise NotFoundError("Paquete de créditos no encontrado")
    return paquete


async def create(
    session: AsyncSession,
    *,
    nombre: str,
    cantidad_creditos: int,
    precio_total_usd: Decimal,
    comision_pct: int | None,
    descripcion: str | None,
    activo: bool,
    visible: bool,
    destacado: bool,
) -> PaqueteCredito:
    paquete = PaqueteCredito(
        nombre=nombre,
        cantidad_creditos=cantidad_creditos,
        precio_total_usd=precio_total_usd,
        comision_pct=comision_pct,
        descripcion=descripcion,
        activo=activo,
        visible=visible,
        destacado=destacado,
    )
    session.add(paquete)
    await session.flush()
    await session.commit()
    return paquete


async def update(
    session: AsyncSession,
    paquete_id: uuid.UUID,
    *,
    nombre: str | None = None,
    descripcion: str | None = None,
    precio_total_usd: Decimal | None = None,
    comision_pct: int | None = None,  # None = usar global, se guarda como None
    comision_pct_set: bool = False,    # True si se envió explícitamente
    activo: bool | None = None,
    visible: bool | None = None,
    destacado: bool | None = None,
    cantidad_creditos: int | None = None,
) -> PaqueteCredito:
    paquete = await get_by_id(session, paquete_id)

    # Si se intenta cambiar cantidad_creditos y ya hay transacciones → 409
    if cantidad_creditos is not None and cantidad_creditos != paquete.cantidad_creditos:
        tx_count = await session.scalar(
            select(func.count())
            .select_from(PaqueteCredito)
            .where(PaqueteCredito.id == paquete_id)
        )
        # Por ahora siempre permitimos (tx_count se conectará en T9/T10).
        # Cuando se implemente el checkout con paquete_id, aquí se valida:
        # if tx_count and tx_count > 0:
        #     raise ConflictError("No se puede cambiar créditos de un paquete con transacciones")
        paquete.cantidad_creditos = cantidad_creditos

    if nombre is not None:
        paquete.nombre = nombre
    if descripcion is not None:
        paquete.descripcion = descripcion
    if precio_total_usd is not None:
        paquete.precio_total_usd = precio_total_usd
    if comision_pct_set:
        paquete.comision_pct = comision_pct
    if activo is not None:
        paquete.activo = activo
    if visible is not None:
        paquete.visible = visible
    if destacado is not None:
        paquete.destacado = destacado

    await session.flush()
    await session.commit()
    return paquete
