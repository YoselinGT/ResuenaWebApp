"""Tests de integración del módulo de sellos discográficos (Fase 04b)."""

from __future__ import annotations

import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from src.infra.db import SessionLocal
from src.main import app
from src.models.enums import EstadoInvitacionSello, RolSelloArtista
from src.models.invitaciones_sello import InvitacionSello
from src.models.sellos import SelloArtista

API = "/api"


@pytest.fixture
async def make_client():
    """Crea clientes ASGI independientes (cookie jar por usuario)."""
    abiertos: list[AsyncClient] = []

    async def _make() -> AsyncClient:
        c = AsyncClient(transport=ASGITransport(app=app), base_url="http://test")
        abiertos.append(c)
        return c

    yield _make
    for c in abiertos:
        await c.aclose()


async def _crear_artista(make_client, register_and_confirm) -> tuple[AsyncClient, str]:
    c = await make_client()
    correo = await register_and_confirm(c, "artista")
    return c, correo


async def _user_id(client: AsyncClient) -> str:
    return (await client.get(f"{API}/users/me")).json()["id"]


async def _token_invitacion(correo: str) -> str | None:
    async with SessionLocal() as s:
        return await s.scalar(
            select(InvitacionSello.token)
            .where(
                InvitacionSello.correo == correo,
                InvitacionSello.estado == EstadoInvitacionSello.pendiente,
            )
            .order_by(InvitacionSello.created_at.desc())
        )


async def _crear_sello(client: AsyncClient, nombre: str | None = None):
    nombre = nombre or f"Sello {uuid.uuid4().hex[:8]}"
    return await client.post(f"{API}/sellos", data={"nombre": nombre})


# ── Tests ────────────────────────────────────────────────────────
async def test_crear_sello_owner(make_client, register_and_confirm):
    c, _ = await _crear_artista(make_client, register_and_confirm)
    r = await _crear_sello(c)
    assert r.status_code == 201
    body = r.json()
    assert body["rol"] == "owner"

    async with SessionLocal() as s:
        fila = await s.scalar(
            select(SelloArtista).where(SelloArtista.sello_id == uuid.UUID(body["id"]))
        )
    assert fila is not None
    assert fila.rol == RolSelloArtista.owner
    assert fila.activo is True


async def test_no_dos_sellos(make_client, register_and_confirm):
    c, _ = await _crear_artista(make_client, register_and_confirm)
    assert (await _crear_sello(c)).status_code == 201
    r2 = await _crear_sello(c)
    assert r2.status_code == 409


async def test_get_mio_sin_sello_null(make_client, register_and_confirm):
    c, _ = await _crear_artista(make_client, register_and_confirm)
    r = await c.get(f"{API}/sellos/mio")
    assert r.status_code == 200
    assert r.json() is None


async def test_invitar_artista_en_otro_sello_409(make_client, register_and_confirm):
    a, _ = await _crear_artista(make_client, register_and_confirm)
    b, correo_b = await _crear_artista(make_client, register_and_confirm)
    sello_a = (await _crear_sello(a)).json()
    await _crear_sello(b)  # B ya es owner de su propio sello

    r = await a.post(
        f"{API}/sellos/{sello_a['id']}/invitar",
        json={"correo": correo_b, "rol": "artista"},
    )
    assert r.status_code == 409


async def test_aceptar_invitacion_crea_membresia(make_client, register_and_confirm):
    a, _ = await _crear_artista(make_client, register_and_confirm)
    c, correo_c = await _crear_artista(make_client, register_and_confirm)
    sello = (await _crear_sello(a)).json()

    inv = await a.post(
        f"{API}/sellos/{sello['id']}/invitar",
        json={"correo": correo_c, "rol": "manager"},
    )
    assert inv.status_code == 201

    token = await _token_invitacion(correo_c)
    assert token is not None

    r = await c.post(f"{API}/sellos/aceptar-invitacion/{token}")
    assert r.status_code == 200
    assert r.json()["rol"] == "manager"

    cid = await _user_id(c)
    async with SessionLocal() as s:
        fila = await s.scalar(
            select(SelloArtista).where(
                SelloArtista.sello_id == uuid.UUID(sello["id"]),
                SelloArtista.artista_id == uuid.UUID(cid),
                SelloArtista.activo.is_(True),
            )
        )
    assert fila is not None
    assert fila.rol == RolSelloArtista.manager


async def test_owner_no_puede_auto_eliminarse(make_client, register_and_confirm):
    a, _ = await _crear_artista(make_client, register_and_confirm)
    sello = (await _crear_sello(a)).json()
    aid = await _user_id(a)
    r = await a.delete(f"{API}/sellos/{sello['id']}/miembros/{aid}")
    assert r.status_code == 409


async def test_curador_no_tiene_sello(make_client, register_and_confirm):
    c = await make_client()
    await register_and_confirm(c, "profesional")
    # /sellos/mio exige rol artista → 403 para curador.
    assert (await c.get(f"{API}/sellos/mio")).status_code == 403
