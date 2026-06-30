"""DTOs Pydantic del módulo de créditos."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class CheckoutBody(BaseModel):
    """Solicitud de compra: cantidad de créditos del paquete elegido."""

    cantidad_creditos: int = Field(gt=0)


class PaqueteDTO(BaseModel):
    """Un paquete de créditos comprable."""

    cantidad: int
    precio_unitario_mxn: int
    precio_total_mxn: int


class BalanceDTO(BaseModel):
    saldo_creditos: int
    saldo_pendiente_retiro: int


class CheckoutURLDTO(BaseModel):
    checkout_url: str


class TransaccionDTO(BaseModel):
    id: str
    tipo: str
    monto: int
    descripcion: str | None = None
    referencia_stripe: str | None = None
    created_at: datetime


class PaginatedTransaccionesDTO(BaseModel):
    items: list[TransaccionDTO]
    total: int
    page: int
    page_size: int
