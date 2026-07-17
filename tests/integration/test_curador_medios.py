"""Tests de integración de la gestión de medios del curador (Fase 04b)."""

from __future__ import annotations

import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from src.infra.db import SessionLocal
from src.main import app
from src.models.campana_medios import CampanaMedio
from src.models.campanas import Campana
from src.models.curador_medios import CuradorMedio
from src.models.enums import EstadoCampanaMedio, EstadoSolicitudCurador
from src.models.generos import GeneroMusical
from src.models.solicitudes_curador import SolicitudCurador
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


async def _user_id(client: AsyncClient) -> str:
    return (await client.get(f"{API}/users/me")).json()["id"]


async def _primer_genero() -> int:
    async with SessionLocal() as s:
        return await s.scalar(select(GeneroMusical.id).order_by(GeneroMusical.id))


async def _aprobar_curador(correo: str) -> None:
    async with SessionLocal() as s:
        uid = await s.scalar(select(Usuario.id).where(Usuario.correo == correo))
        sol = await s.scalar(
            select(SolicitudCurador).where(SolicitudCurador.usuario_id == uid)
        )
        sol.estado = EstadoSolicitudCurador.aprobada
        await s.commit()


async def _curador_aprobado(make_client, register_and_confirm) -> tuple[AsyncClient, str]:
    c = await make_client()
    correo = await register_and_confirm(c, "profesional")
    await c.post(f"{API}/auth/aplicar", json={"tipo_profesional": "playlister"})
    await _aprobar_curador(correo)
    return c, correo


async def _crear_medio(client: AsyncClient, gen: int) -> dict:
    r = await client.post(
        f"{API}/curador/medios",
        json={
            "nombre": f"Canal {uuid.uuid4().hex[:6]}",
            "tipo": "playlist",
            "generos_especializados": [gen],
        },
    )
    assert r.status_code == 201, r.text
    return r.json()


# ── Tests ────────────────────────────────────────────────────────
async def test_artista_no_puede_crear_medio(make_client, register_and_confirm):
    c = await make_client()
    await register_and_confirm(c, "artista")
    r = await c.post(
        f"{API}/curador/medios", json={"nombre": "X", "tipo": "playlist"}
    )
    assert r.status_code == 403


async def test_curador_no_aprobado_403(make_client, register_and_confirm):
    c = await make_client()
    await register_and_confirm(c, "profesional")
    await c.post(f"{API}/auth/aplicar", json={"tipo_profesional": "blogger"})
    r = await c.post(
        f"{API}/curador/medios", json={"nombre": "X", "tipo": "blog"}
    )
    assert r.status_code == 403


async def test_curador_aprobado_crea_medio_stats_cero(
    make_client, register_and_confirm
):
    c, _ = await _curador_aprobado(make_client, register_and_confirm)
    gen = await _primer_genero()
    medio = await _crear_medio(c, gen)

    assert medio["activo"] is True
    assert medio["genero_ids"] == [gen]
    assert medio["stats"] == {
        "recibidas": 0,
        "aceptadas": 0,
        "entregadas": 0,
        "tasa_aceptacion": 0.0,
    }

    async with SessionLocal() as s:
        fila = await s.scalar(
            select(CuradorMedio).where(CuradorMedio.id == uuid.UUID(medio["id"]))
        )
    assert fila is not None


async def test_stats_detalladas_recien_creado_cero(
    make_client, register_and_confirm
):
    c, _ = await _curador_aprobado(make_client, register_and_confirm)
    gen = await _primer_genero()
    medio = await _crear_medio(c, gen)
    r = await c.get(f"{API}/curador/medios/{medio['id']}/stats")
    assert r.status_code == 200
    d = r.json()
    assert d["recibidas"] == 0 and d["aceptadas"] == 0 and d["entregadas"] == 0
    assert d["por_mes"] == []


async def test_toggle_con_campana_activa_409(make_client, register_and_confirm):
    c, _ = await _curador_aprobado(make_client, register_and_confirm)
    gen = await _primer_genero()
    medio = await _crear_medio(c, gen)
    cid = await _user_id(c)

    # Inserta una campaña + vínculo pendiente al medio (campañas reales: Fase 08).
    async with SessionLocal() as s:
        campana = Campana(
            artista_id=uuid.UUID(cid),
            titulo="Camp Test",
            url_audio="s3://x",
            genero_id=gen,
        )
        s.add(campana)
        await s.flush()
        s.add(
            CampanaMedio(
                campana_id=campana.id,
                medio_id=uuid.UUID(medio["id"]),
                curador_id=uuid.UUID(cid),
                estado=EstadoCampanaMedio.pendiente,
            )
        )
        await s.commit()

    r = await c.post(f"{API}/curador/medios/{medio['id']}/toggle-activo")
    assert r.status_code == 409


async def test_editar_medio(make_client, register_and_confirm):
    c, _ = await _curador_aprobado(make_client, register_and_confirm)
    gen = await _primer_genero()
    medio = await _crear_medio(c, gen)
    r = await c.patch(
        f"{API}/curador/medios/{medio['id']}",
        json={"nombre": "Canal Renombrado", "generos_especializados": []},
    )
    assert r.status_code == 200
    assert r.json()["nombre"] == "Canal Renombrado"
    assert r.json()["genero_ids"] == []


# ── Tests precio_creditos (Fase 06c) ────────────────────────────


async def test_crear_medio_sin_precio_usa_default_1(make_client, register_and_confirm):
    c, _ = await _curador_aprobado(make_client, register_and_confirm)
    gen = await _primer_genero()
    medio = await _crear_medio(c, gen)

    assert medio["precio_creditos"] == 1
    assert medio["descripcion_precio"] is None


async def test_crear_medio_con_precio_personalizado(make_client, register_and_confirm):
    c, _ = await _curador_aprobado(make_client, register_and_confirm)
    gen = await _primer_genero()
    r = await c.post(
        f"{API}/curador/medios",
        json={
            "nombre": f"Canal {uuid.uuid4().hex[:6]}",
            "tipo": "playlist",
            "generos_especializados": [gen],
            "precio_creditos": 3,
            "descripcion_precio": "Reel de 15-60 segundos",
        },
    )
    assert r.status_code == 201
    data = r.json()
    assert data["precio_creditos"] == 3
    assert data["descripcion_precio"] == "Reel de 15-60 segundos"


async def test_crear_medio_precio_cero_422(make_client, register_and_confirm):
    c, _ = await _curador_aprobado(make_client, register_and_confirm)
    gen = await _primer_genero()
    r = await c.post(
        f"{API}/curador/medios",
        json={
            "nombre": f"Canal {uuid.uuid4().hex[:6]}",
            "tipo": "playlist",
            "generos_especializados": [gen],
            "precio_creditos": 0,
        },
    )
    assert r.status_code == 422


async def test_editar_precio_medio(make_client, register_and_confirm):
    c, _ = await _curador_aprobado(make_client, register_and_confirm)
    gen = await _primer_genero()
    medio = await _crear_medio(c, gen)

    assert medio["precio_creditos"] == 1

    r = await c.patch(
        f"{API}/curador/medios/{medio['id']}",
        json={"precio_creditos": 5, "descripcion_precio": "Post en blog"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["precio_creditos"] == 5
    assert data["descripcion_precio"] == "Post en blog"


async def test_editar_precio_no_afecta_campanas_existentes(
    make_client, register_and_confirm
):
    c, _ = await _curador_aprobado(make_client, register_and_confirm)
    gen = await _primer_genero()
    medio = await _crear_medio(c, gen)
    cid = await _user_id(c)

    # Crear campaña vinculada al medio con precio_snapshot=1 (default).
    async with SessionLocal() as s:
        campana = Campana(
            artista_id=uuid.UUID(cid),
            titulo="Camp Precio",
            url_audio="s3://x",
            genero_id=gen,
        )
        s.add(campana)
        await s.flush()
        s.add(
            CampanaMedio(
                campana_id=campana.id,
                medio_id=uuid.UUID(medio["id"]),
                curador_id=uuid.UUID(cid),
                estado=EstadoCampanaMedio.pendiente,
                precio_snapshot=1,
            )
        )
        await s.commit()

    # Cambiar precio del medio a 5.
    r = await c.patch(
        f"{API}/curador/medios/{medio['id']}",
        json={"precio_creditos": 5},
    )
    assert r.status_code == 200
    assert r.json()["precio_creditos"] == 5

    # Verificar que precio_snapshot de la campaña existente sigue en 1.
    async with SessionLocal() as s:
        snap = await s.scalar(
            select(CampanaMedio.precio_snapshot).where(
                CampanaMedio.medio_id == uuid.UUID(medio["id"])
            )
        )
    assert snap == 1
