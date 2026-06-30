"""Tests del wallet_service (Fase 06). Usan la BD real vía SessionLocal."""

from __future__ import annotations

import uuid

import pytest

from src.infra.db import SessionLocal
from src.services import wallet_service
from src.services.exceptions import InsufficientCreditsError

API = "/api"


@pytest.fixture
async def usuario_id(client, register_and_confirm) -> uuid.UUID:
    await register_and_confirm(client, "artista")
    me = (await client.get(f"{API}/users/me")).json()
    return uuid.UUID(me["id"])


async def test_balance_sin_wallet_es_cero(usuario_id):
    async with SessionLocal() as s:
        wallet = await wallet_service.get_balance(s, usuario_id)
    assert wallet.saldo_creditos == 0
    assert wallet.saldo_pendiente_retiro == 0


async def test_add_credits_idempotente(usuario_id):
    # La idempotencia es global por referencia (payment_intent único en Stripe);
    # el DB de dev persiste entre corridas, así que la referencia debe ser única.
    ref = f"ref-{uuid.uuid4()}"
    async with SessionLocal() as s:
        await wallet_service.add_credits(s, usuario_id, 5, descripcion="compra", referencia=ref)
    async with SessionLocal() as s:
        await wallet_service.add_credits(s, usuario_id, 5, descripcion="dup", referencia=ref)
    async with SessionLocal() as s:
        assert (await wallet_service.get_balance(s, usuario_id)).saldo_creditos == 5


async def test_deduct_y_saldo_insuficiente(usuario_id):
    async with SessionLocal() as s:
        await wallet_service.add_credits(s, usuario_id, 10, descripcion="compra")
    async with SessionLocal() as s:
        await wallet_service.deduct_credits(s, usuario_id, 3, descripcion="gasto")
    async with SessionLocal() as s:
        assert (await wallet_service.get_balance(s, usuario_id)).saldo_creditos == 7
    async with SessionLocal() as s:
        with pytest.raises(InsufficientCreditsError):
            await wallet_service.deduct_credits(s, usuario_id, 999, descripcion="overdraft")
    # El intento fallido no alteró el saldo.
    async with SessionLocal() as s:
        assert (await wallet_service.get_balance(s, usuario_id)).saldo_creditos == 7


async def test_monto_no_positivo_rechazado(usuario_id):
    from src.services.exceptions import ValidationError

    async with SessionLocal() as s:
        with pytest.raises(ValidationError):
            await wallet_service.add_credits(s, usuario_id, 0, descripcion="cero")


async def test_paquetes():
    async with SessionLocal() as s:
        paquetes = await wallet_service.list_paquetes(s)
    assert [p.cantidad for p in paquetes] == [5, 10, 20, 50]
    assert all(
        p.precio_total_mxn == p.cantidad * p.precio_unitario_mxn for p in paquetes
    )
