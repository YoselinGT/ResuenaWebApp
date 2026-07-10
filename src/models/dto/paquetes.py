"""DTOs Pydantic del módulo de paquetes de créditos."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


# ── Request DTOs ──────────────────────────────────────────────────


class PaqueteCreateBody(BaseModel):
    """Body para POST /admin/paquetes."""

    nombre: str = Field(min_length=1, max_length=255)
    cantidad_creditos: int = Field(gt=0)
    precio_total_usd: Decimal = Field(gt=0, decimal_places=2)
    comision_pct: int | None = Field(None, ge=1, le=99)
    descripcion: str | None = None
    activo: bool = True
    visible: bool = True
    destacado: bool = False


class PaqueteUpdateBody(BaseModel):
    """Body para PATCH /admin/paquetes/:id — todos los campos opcionales."""

    nombre: str | None = Field(None, min_length=1, max_length=255)
    descripcion: str | None = None
    precio_total_usd: Decimal | None = Field(None, gt=0, decimal_places=2)
    comision_pct: int | None = Field(None, ge=1, le=99)
    activo: bool | None = None
    visible: bool | None = None
    destacado: bool | None = None


class ConfigCreditosUpdateBody(BaseModel):
    """Body para PATCH /admin/config/creditos — todos los campos opcionales."""

    precio_credito_individual_usd: Decimal | None = Field(None, gt=0, decimal_places=2)
    comision_resuena_pct: int | None = Field(None, ge=1, le=99)
    stripe_pct_nacional: Decimal | None = Field(None, ge=0, le=1)
    stripe_fixed_usd: Decimal | None = Field(None, ge=0, decimal_places=2)
    stripe_pct_internacional: Decimal | None = Field(None, ge=0, le=1)
    stripe_pct_conversion_moneda: Decimal | None = Field(None, ge=0, le=1)
    stripe_pct_oxxo: Decimal | None = Field(None, ge=0, le=1)
    stripe_fixed_disputa_usd: Decimal | None = Field(None, ge=0, decimal_places=2)
    stripe_escenario_default: str | None = Field(
        None, pattern=r"^(nacional|internacional|oxxo)$"
    )


# ── Response DTOs ─────────────────────────────────────────────────


class PaqueteCamposCalculados(BaseModel):
    """Campos derivados calculados en tiempo real — nunca se almacenan."""

    precio_por_credito_usd: Decimal
    stripe_fee_estimado_usd: Decimal
    artista_paga_estimado_usd: Decimal
    curador_recibe_por_credito_usd: Decimal
    resuena_por_credito_usd: Decimal


class PaqueteAdminResponse(BaseModel):
    """Response de GET /admin/paquetes — incluye campos calculados + transacciones_count."""

    id: str
    nombre: str
    cantidad_creditos: int
    precio_total_usd: Decimal
    comision_pct: int | None
    descripcion: str | None
    activo: bool
    visible: bool
    destacado: bool
    transacciones_count: int
    calculado: PaqueteCamposCalculados
    created_at: datetime
    updated_at: datetime


class PaquetePublicoResponse(BaseModel):
    """Response de GET /creditos/paquetes — lo que ve el artista."""

    id: str
    nombre: str
    cantidad_creditos: int
    precio_total_usd: Decimal
    descripcion: str | None
    destacado: bool
    calculado: PaqueteCamposCalculados


class ConfigCreditosResponse(BaseModel):
    """Response de GET /admin/config/creditos."""

    precio_credito_individual_usd: Decimal
    comision_resuena_pct: int
    stripe_pct_nacional: Decimal
    stripe_fixed_usd: Decimal
    stripe_pct_internacional: Decimal
    stripe_pct_conversion_moneda: Decimal
    stripe_pct_oxxo: Decimal
    stripe_fixed_disputa_usd: Decimal
    stripe_escenario_default: str


class CheckoutBodyUSD(BaseModel):
    """Body para POST /creditos/checkout — compra de paquete o individual."""

    paquete_id: str | None = None
    cantidad_creditos: int | None = Field(None, gt=0)
