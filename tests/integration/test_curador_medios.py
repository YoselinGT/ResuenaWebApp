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
from src.models.enums import EstadoCampanaMedio
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


async def _user_id(client: AsyncClient) -> str:
    return (await client.get(f"{API}/users/me")).json()["id"]


async def _primer_genero() -> int:
    async with SessionLocal() as s:
        return await s.scalar(select(GeneroMusical.id).order_by(GeneroMusical.id))


async def _aprobar_curador(correo: str) -> None:
    """Aprueba el primer medio del curador (ya no se basa en solicitudes_curador)."""
    async with SessionLocal() as s:
        uid = await s.scalar(select(Usuario.id).where(Usuario.correo == correo))
        medio = await s.scalar(
            select(CuradorMedio).where(CuradorMedio.curador_id == uid)
        )
        if medio:
            medio.estado_revision = "aprobado"
            await s.commit()


async def _curador_aprobado(make_client, register_and_confirm) -> tuple[AsyncClient, str]:
    c = await make_client()
    correo = await register_and_confirm(c, "profesional")
    gen = await _primer_genero()
    # Crear un canal → crea solicitud automáticamente (fase-06e)
    await c.post(
        f"{API}/onboarding/medios",
        json={
            "nombre": "Canal Inicial",
            "tipo": "tiktok",
            "genero_ids": [gen],
            "redes": [{"tipo": "tiktok", "url": "https://tiktok.com/@test", "es_principal": True}],
        },
    )
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


async def test_curador_sin_aprobacion_puede_crear_medio(make_client, register_and_confirm):
    """POST /curador/medios ya no requiere aprobación — cualquier curador activo puede crear."""
    c = await make_client()
    await register_and_confirm(c, "profesional")
    gen = await _primer_genero()
    r = await c.post(
        f"{API}/curador/medios",
        json={
            "nombre": "Canal Nuevo",
            "tipo": "blog",
            "generos_especializados": [gen],
        },
    )
    assert r.status_code == 201
    data = r.json()
    assert data["estado_revision"] == "pendiente"


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


# ── Tests require_curador_aprobado (Fase 06g) ───────────────────


async def test_curador_aprobado_retorna_estado_revision(make_client, register_and_confirm):
    """GET /curador/medios incluye estado_revision en cada medio."""
    c, _ = await _curador_aprobado(make_client, register_and_confirm)
    gen = await _primer_genero()
    await _crear_medio(c, gen)
    r = await c.get(f"{API}/curador/medios")
    assert r.status_code == 200
    medios = r.json()
    assert len(medios) > 0
    for m in medios:
        assert "estado_revision" in m
        assert m["estado_revision"] in ("pendiente", "aprobado", "rechazado")


async def test_crear_medio_precio_en_response(make_client, register_and_confirm):
    """POST /curador/medios retorna precio_creditos y descripcion_precio."""
    c, _ = await _curador_aprobado(make_client, register_and_confirm)
    gen = await _primer_genero()
    r = await c.post(
        f"{API}/curador/medios",
        json={
            "nombre": "Canal Precio",
            "tipo": "tiktok",
            "generos_especializados": [gen],
            "precio_creditos": 4,
            "descripcion_precio": "Reel 30 seg",
        },
    )
    assert r.status_code == 201
    data = r.json()
    assert data["precio_creditos"] == 4
    assert data["descripcion_precio"] == "Reel 30 seg"
