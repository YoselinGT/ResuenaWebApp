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
