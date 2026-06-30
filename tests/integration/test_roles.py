"""Tests de los guards de rol (RBAC, Fase 05)."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from src.infra.db import SessionLocal
from src.main import app
from src.models.usuarios import Usuario

API = "/api"
STRONG_PW = "Str0ng!Pass"


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


async def make_admin(client, register_and_confirm, otp_for) -> str:
    """Crea un admin: registra artista, promueve perfil_id=1 y re-loguea (JWT fresco)."""
    correo = await register_and_confirm(client, "artista")
    async with SessionLocal() as s:
        usuario = await s.scalar(select(Usuario).where(Usuario.correo == correo))
        usuario.perfil_id = 1
        await s.commit()
    r = await client.post(
        f"{API}/auth/login", json={"correo": correo, "password": STRONG_PW}
    )
    sid = r.json()["pre_auth_session_id"]
    code = await otp_for(sid)
    await client.post(
        f"{API}/auth/otp/verify",
        json={"pre_auth_session_id": sid, "code": code},
    )
    return correo


async def test_admin_accede(make_client, register_and_confirm, otp_for):
    c = await make_client()
    await make_admin(c, register_and_confirm, otp_for)
    r = await c.get(f"{API}/admin/solicitudes")
    assert r.status_code == 200


async def test_artista_no_accede_admin(make_client, register_and_confirm):
    c = await make_client()
    await register_and_confirm(c, "artista")
    assert (await c.get(f"{API}/admin/solicitudes")).status_code == 403
    assert (await c.get(f"{API}/admin/usuarios")).status_code == 403


async def test_admin_requiere_sesion(make_client):
    c = await make_client()
    assert (await c.get(f"{API}/admin/solicitudes")).status_code == 401


async def test_es_admin_en_me(make_client, register_and_confirm, otp_for):
    c = await make_client()
    await make_admin(c, register_and_confirm, otp_for)
    assert (await c.get(f"{API}/auth/me")).json()["es_admin"] is True
