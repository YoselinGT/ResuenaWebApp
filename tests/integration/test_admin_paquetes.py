"""Tests de integración — Admin paquetes de créditos (Fase 06b)."""

from __future__ import annotations

import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from src.main import app
from src.models.paquetes_creditos import PaqueteCredito
from src.models.parametros_config import ParametroConfig
from src.infra.db import SessionLocal

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


# ── POST /admin/paquetes ──────────────────────────────────────────


async def test_admin_paquetes_post_como_artista_403(make_client, register_and_confirm):
    c = await make_client()
    await register_and_confirm(c, "artista")
    r = await c.post(
        f"{API}/admin/paquetes",
        json={
            "nombre": "Test",
            "cantidad_creditos": 10,
            "precio_total_usd": 18.00,
        },
    )
    assert r.status_code == 403


async def test_admin_paquetes_post_crea_paquete(make_client, register_and_confirm):
    c = await make_client()
    await register_and_confirm(c, "admin")
    r = await c.post(
        f"{API}/admin/paquetes",
        json={
            "nombre": "Pro",
            "cantidad_creditos": 10,
            "precio_total_usd": 18.00,
            "descripcion": "Ideal para campañas medianas.",
            "activo": True,
            "visible": True,
            "destacado": False,
        },
    )
    assert r.status_code == 201
    data = r.json()
    assert data["nombre"] == "Pro"
    assert data["cantidad_creditos"] == 10
    assert float(data["precio_total_usd"]) == 18.00
    # Campos calculados
    assert float(data["calculado"]["precio_por_credito_usd"]) == 1.80
    assert float(data["calculado"]["curador_recibe_por_credito_usd"]) == 0.90


# ── GET /admin/paquetes ───────────────────────────────────────────


async def test_admin_paquetes_get_campos_calculados(
    make_client, register_and_confirm
):
    c = await make_client()
    await register_and_confirm(c, "admin")
    # Crear paquete
    await c.post(
        f"{API}/admin/paquetes",
        json={
            "nombre": "Basic",
            "cantidad_creditos": 5,
            "precio_total_usd": 9.00,
        },
    )
    r = await c.get(f"{API}/admin/paquetes")
    assert r.status_code == 200
    paquetes = r.json()
    assert len(paquetes) >= 1
    p = paquetes[0]
    assert "calculado" in p
    assert "transacciones_count" in p
    assert float(p["calculado"]["precio_por_credito_usd"]) == 1.80


# ── PATCH /admin/paquetes/:id ─────────────────────────────────────


async def test_admin_paquetes_patch_visible_desaparece_del_catalogo(
    make_client, register_and_confirm
):
    c = await make_client()
    await register_and_confirm(c, "admin")
    # Crear paquete visible
    r = await c.post(
        f"{API}/admin/paquetes",
        json={
            "nombre": "Visible",
            "cantidad_creditos": 5,
            "precio_total_usd": 9.00,
            "visible": True,
        },
    )
    pid = r.json()["id"]

    # Hacer invisible
    r2 = await c.patch(f"{API}/admin/paquetes/{pid}", json={"visible": False})
    assert r2.status_code == 200
    assert r2.json()["visible"] is False

    # Login como artista y verificar que no aparece
    c2 = await make_client()
    await register_and_confirm(c2, "artista")
    r3 = await c2.get(f"{API}/creditos/paquetes")
    assert r3.status_code == 200
    ids = [p["id"] for p in r3.json()]
    assert pid not in ids


# ── GET /admin/config/creditos ────────────────────────────────────


async def test_admin_config_creditos_get(make_client, register_and_confirm):
    c = await make_client()
    await register_and_confirm(c, "admin")
    r = await c.get(f"{API}/admin/config/creditos")
    assert r.status_code == 200
    data = r.json()
    assert "precio_credito_individual_usd" in data
    assert "comision_resuena_pct" in data
    assert "stripe_pct_nacional" in data
    assert "stripe_escenario_default" in data


# ── PATCH /admin/config/creditos ──────────────────────────────────


async def test_admin_config_creditos_patch_actualiza(
    make_client, register_and_confirm
):
    c = await make_client()
    await register_and_confirm(c, "admin")
    r = await c.patch(
        f"{API}/admin/config/creditos",
        json={"stripe_pct_internacional": 0.01},
    )
    assert r.status_code == 200
    assert float(r.json()["stripe_pct_internacional"]) == 0.01

    # Verificar en BD
    async with SessionLocal() as s:
        val = await s.scalar(
            select(ParametroConfig.valor_cifrado).where(
                ParametroConfig.clave == "stripe_pct_internacional"
            )
        )
        assert val == "0.01"
