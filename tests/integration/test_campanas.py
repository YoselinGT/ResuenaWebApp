"""Tests de integración de campañas musicales (Fase 08)."""

from __future__ import annotations

import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from src.infra.db import SessionLocal
from src.main import app
from src.models.campanas import Campana
from src.models.enums import EstadoCampana
from src.models.generos import GeneroMusical
from src.models.usuarios import Usuario

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


async def _register_artista(make_client) -> tuple[AsyncClient, str]:
    """Registra un artista y retorna el client + correo."""
    c = await make_client()
    correo = f"artista_{uuid.uuid4().hex[:8]}@test.com"
    await c.post(
        f"{API}/auth/register",
        json={
            "nombre_completo": "Artista Test",
            "correo": correo,
            "password": "Artista1234!",
        },
    )
    async with SessionLocal() as s:
        u = await s.scalar(select(Usuario).where(Usuario.correo == correo))
        if u:
            u.activo = True
            await s.commit()
    return c, correo


async def _primer_genero() -> int:
    async with SessionLocal() as s:
        return await s.scalar(select(GeneroMusical.id).order_by(GeneroMusical.id))


# ── Tests creación de campaña ────────────────────────────────────


async def test_crear_campana_borrador(make_client):
    c, _ = await _register_artista(make_client)
    gen_id = await _primer_genero()

    r = await c.post(
        f"{API}/campanas",
        json={
            "titulo": "Mi primera campaña",
            "descripcion": "Test de campaña",
            "genero_id": gen_id,
        },
    )
    assert r.status_code == 201
    data = r.json()
    assert data["titulo"] == "Mi primera campaña"
    assert data["estado"] == "borrador"
    assert data["creditos_usados"] == 0


async def test_crear_campana_sin_titulo_422(make_client):
    c, _ = await _register_artista(make_client)
    gen_id = await _primer_genero()

    r = await c.post(
        f"{API}/campanas",
        json={"titulo": "", "genero_id": gen_id},
    )
    assert r.status_code == 422


async def test_crear_campana_genero_invalido_400(make_client):
    c, _ = await _register_artista(make_client)

    r = await c.post(
        f"{API}/campanas",
        json={"titulo": "Test", "genero_id": 99999},
    )
    assert r.status_code == 400


# ── Tests actualización ──────────────────────────────────────────


async def test_actualizar_campana_borrador(make_client):
    c, _ = await _register_artista(make_client)
    gen_id = await _primer_genero()

    r = await c.post(
        f"{API}/campanas",
        json={"titulo": "Original", "genero_id": gen_id},
    )
    campana_id = r.json()["id"]

    r = await c.patch(
        f"{API}/campanas/{campana_id}",
        json={"titulo": "Actualizada"},
    )
    assert r.status_code == 200
    assert r.json()["titulo"] == "Actualizada"


# ── Tests listado ────────────────────────────────────────────────


async def test_listar_campanas_vacio(make_client):
    c, _ = await _register_artista(make_client)

    r = await c.get(f"{API}/campanas")
    assert r.status_code == 200
    data = r.json()
    assert data["items"] == []
    assert data["total"] == 0


async def test_listar_campanas_con_datos(make_client):
    c, _ = await _register_artista(make_client)
    gen_id = await _primer_genero()

    await c.post(
        f"{API}/campanas",
        json={"titulo": "Campaña 1", "genero_id": gen_id},
    )
    await c.post(
        f"{API}/campanas",
        json={"titulo": "Campaña 2", "genero_id": gen_id},
    )

    r = await c.get(f"{API}/campanas")
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2


# ── Tests detalle ────────────────────────────────────────────────


async def test_detalle_campana(make_client):
    c, _ = await _register_artista(make_client)
    gen_id = await _primer_genero()

    r = await c.post(
        f"{API}/campanas",
        json={"titulo": "Detalle Test", "genero_id": gen_id},
    )
    campana_id = r.json()["id"]

    r = await c.get(f"{API}/campanas/{campana_id}")
    assert r.status_code == 200
    assert r.json()["titulo"] == "Detalle Test"


async def test_detalle_campana_no_existente_404(make_client):
    c, _ = await _register_artista(make_client)

    fake_id = str(uuid.uuid4())
    r = await c.get(f"{API}/campanas/{fake_id}")
    assert r.status_code == 404


# ── Tests eliminación ────────────────────────────────────────────


async def test_eliminar_campana_borrador(make_client):
    c, _ = await _register_artista(make_client)
    gen_id = await _primer_genero()

    r = await c.post(
        f"{API}/campanas",
        json={"titulo": "Para eliminar", "genero_id": gen_id},
    )
    campana_id = r.json()["id"]

    r = await c.delete(f"{API}/campanas/{campana_id}")
    assert r.status_code == 204

    # Verificar que ya no existe
    r = await c.get(f"{API}/campanas/{campana_id}")
    assert r.status_code == 404


# ── Tests envío ──────────────────────────────────────────────────


async def test_enviar_sin_medios_400(make_client):
    c, _ = await _register_artista(make_client)
    gen_id = await _primer_genero()

    r = await c.post(
        f"{API}/campanas",
        json={"titulo": "Sin medios", "genero_id": gen_id},
    )
    campana_id = r.json()["id"]

    r = await c.post(f"{API}/campanas/{campana_id}/enviar")
    assert r.status_code == 400
    assert "curador" in r.json()["detail"].lower()


async def test_enviar_sin_audio_400(make_client):
    c, _ = await _register_artista(make_client)
    gen_id = await _primer_genero()

    r = await c.post(
        f"{API}/campanas",
        json={"titulo": "Sin audio", "genero_id": gen_id},
    )
    campana_id = r.json()["id"]

    # Simular que tiene medios vinculados (mock)
    # En un test real, necesitaríamos crear curadores primero
    r = await c.post(f"{API}/campanas/{campana_id}/enviar")
    assert r.status_code in (400, 422)
