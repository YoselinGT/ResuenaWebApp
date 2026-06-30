"""Tests de integración del módulo de créditos (Fase 06)."""

from __future__ import annotations

import hashlib
import hmac
import json
import time
import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from src.config.settings import get_settings
from src.main import app

API = "/api"


@pytest.fixture
async def make_client():
    abiertos: list[AsyncClient] = []

    async def _make() -> AsyncClient:
        c = AsyncClient(transport=ASGITransport(app=app), base_url="http://test")
        abiertos.append(c)
        return c

    yield _make
    for c in abiertos:
        await c.aclose()


def _firmar(payload: bytes) -> str:
    secret = get_settings().stripe_webhook_secret
    ts = int(time.time())
    firmado = f"{ts}.".encode() + payload
    sig = hmac.new(secret.encode(), firmado, hashlib.sha256).hexdigest()
    return f"t={ts},v1={sig}"


# ── Paquetes / balance ───────────────────────────────────────────
async def test_paquetes_requiere_sesion(make_client):
    c = await make_client()
    assert (await c.get(f"{API}/creditos/paquetes")).status_code == 401


async def test_paquetes_lista(make_client, register_and_confirm):
    c = await make_client()
    await register_and_confirm(c, "artista")
    r = await c.get(f"{API}/creditos/paquetes")
    assert r.status_code == 200
    assert len(r.json()) == 4


async def test_balance_sin_wallet_cero(make_client, register_and_confirm):
    c = await make_client()
    await register_and_confirm(c, "artista")
    r = await c.get(f"{API}/creditos/balance")
    assert r.status_code == 200
    assert r.json()["saldo_creditos"] == 0


# ── Checkout ─────────────────────────────────────────────────────
async def test_curador_checkout_403(make_client, register_and_confirm):
    c = await make_client()
    await register_and_confirm(c, "profesional")
    r = await c.post(f"{API}/creditos/checkout", json={"cantidad_creditos": 5})
    assert r.status_code == 403


async def test_checkout_cantidad_invalida_422(make_client, register_and_confirm):
    c = await make_client()
    await register_and_confirm(c, "artista")
    r = await c.post(f"{API}/creditos/checkout", json={"cantidad_creditos": 7})
    assert r.status_code == 422


async def test_checkout_artista_ok(make_client, register_and_confirm, monkeypatch):
    async def fake_session(usuario_id, cantidad, precio):
        return "https://checkout.stripe.test/cs_fake"

    monkeypatch.setattr(
        "src.services.stripe_service.create_checkout_session", fake_session
    )
    c = await make_client()
    await register_and_confirm(c, "artista")
    r = await c.post(f"{API}/creditos/checkout", json={"cantidad_creditos": 10})
    assert r.status_code == 200
    assert r.json()["checkout_url"].startswith("https://")


# ── Webhook ──────────────────────────────────────────────────────
async def test_webhook_firma_invalida_400(make_client):
    c = await make_client()
    r = await c.post(
        f"{API}/creditos/webhook",
        content=b'{"x":1}',
        headers={"stripe-signature": "t=1,v1=bad"},
    )
    assert r.status_code == 400


async def test_webhook_acredita_idempotente(make_client, register_and_confirm):
    c = await make_client()
    await register_and_confirm(c, "artista")
    me = (await c.get(f"{API}/users/me")).json()

    pi = f"pi_test_{uuid.uuid4().hex[:10]}"
    event = {
        "id": "evt_test",
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "id": "cs_test",
                "payment_intent": pi,
                "client_reference_id": me["id"],
                "metadata": {"usuario_id": me["id"], "cantidad_creditos": "5"},
            }
        },
    }
    payload = json.dumps(event).encode()

    r1 = await c.post(
        f"{API}/creditos/webhook",
        content=payload,
        headers={"stripe-signature": _firmar(payload)},
    )
    assert r1.status_code == 200
    saldo1 = (await c.get(f"{API}/creditos/balance")).json()["saldo_creditos"]
    assert saldo1 == 5

    # Reenvío del mismo evento (mismo payment_intent) → no re-acredita.
    r2 = await c.post(
        f"{API}/creditos/webhook",
        content=payload,
        headers={"stripe-signature": _firmar(payload)},
    )
    assert r2.status_code == 200
    saldo2 = (await c.get(f"{API}/creditos/balance")).json()["saldo_creditos"]
    assert saldo2 == 5
