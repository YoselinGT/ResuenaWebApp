"""Tests de integración de géneros musicales y categorías por canal."""

from __future__ import annotations

import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from src.infra.db import SessionLocal
from src.infra.redis_client import get_redis
from src.main import app
from src.models.generos import CategoriaProfesional, GeneroMusical
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


def _uid() -> str:
    return uuid.uuid4().hex[:6]


async def _make_admin(client: AsyncClient, register_and_confirm, otp_for) -> str:
    """Registra un artista, lo hace admin, y obtiene nuevo token."""
    correo = await register_and_confirm(client, "artista")
    async with SessionLocal() as s:
        u = await s.scalar(select(Usuario).where(Usuario.correo == correo))
        if u:
            u.perfil_id = 1
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


async def _crear_genero_con_categorias(admin: AsyncClient):
    """Helper: crea un género con 2 categorías."""
    r = await admin.post(f"{API}/admin/generos", json={"nombre": f"Gen_{_uid()}"})
    assert r.status_code == 201, f"Failed to create genero: {r.text}"
    gen_id = r.json()["id"]
    r = await admin.post(f"{API}/admin/generos/{gen_id}/categorias", json={"nombre": f"Cat_A_{_uid()}"})
    assert r.status_code == 201
    cat1_id = r.json()["id"]
    r = await admin.post(f"{API}/admin/generos/{gen_id}/categorias", json={"nombre": f"Cat_B_{_uid()}"})
    assert r.status_code == 201
    cat2_id = r.json()["id"]
    return gen_id, cat1_id, cat2_id


# ── Tests admin géneros ──────────────────────────────────────────


async def test_admin_crear_genero(client, register_and_confirm, otp_for):
    await _make_admin(client, register_and_confirm, otp_for)
    nombre = f"Urbano_{_uid()}"
    r = await client.post(f"{API}/admin/generos", json={"nombre": nombre})
    assert r.status_code == 201
    data = r.json()
    assert data["nombre"] == nombre
    assert data["activo"] is True
    assert data["categorias"] == []


async def test_admin_list_generos(client, register_and_confirm, otp_for):
    await _make_admin(client, register_and_confirm, otp_for)
    n1 = f"Rock_{_uid()}"
    n2 = f"Pop_{_uid()}"
    await client.post(f"{API}/admin/generos", json={"nombre": n1})
    await client.post(f"{API}/admin/generos", json={"nombre": n2})
    r = await client.get(f"{API}/admin/generos")
    assert r.status_code == 200
    nombres = [g["nombre"] for g in r.json()]
    assert n1 in nombres
    assert n2 in nombres


async def test_admin_crear_genero_duplicado_409(client, register_and_confirm, otp_for):
    await _make_admin(client, register_and_confirm, otp_for)
    nombre = f"Jazz_{_uid()}"
    await client.post(f"{API}/admin/generos", json={"nombre": nombre})
    r = await client.post(f"{API}/admin/generos", json={"nombre": nombre})
    assert r.status_code == 409


async def test_admin_actualizar_genero(client, register_and_confirm, otp_for):
    await _make_admin(client, register_and_confirm, otp_for)
    r = await client.post(f"{API}/admin/generos", json={"nombre": f"Reggae_{_uid()}"})
    gen_id = r.json()["id"]
    nuevo = f"Reggae_Dancehall_{_uid()}"
    r = await client.patch(f"{API}/admin/generos/{gen_id}", json={"nombre": nuevo})
    assert r.status_code == 200
    assert r.json()["nombre"] == nuevo


async def test_admin_desactivar_genero(client, register_and_confirm, otp_for):
    await _make_admin(client, register_and_confirm, otp_for)
    r = await client.post(f"{API}/admin/generos", json={"nombre": f"Metal_{_uid()}"})
    gen_id = r.json()["id"]
    r = await client.patch(f"{API}/admin/generos/{gen_id}", json={"activo": False})
    assert r.status_code == 200
    assert r.json()["activo"] is False


async def test_admin_eliminar_genero(client, register_and_confirm, otp_for):
    await _make_admin(client, register_and_confirm, otp_for)
    r = await client.post(f"{API}/admin/generos", json={"nombre": f"Temp_{_uid()}"})
    gen_id = r.json()["id"]
    r = await client.delete(f"{API}/admin/generos/{gen_id}")
    assert r.status_code == 204


# ── Tests admin categorías ───────────────────────────────────────


async def test_admin_crear_categoria(client, register_and_confirm, otp_for):
    await _make_admin(client, register_and_confirm, otp_for)
    r = await client.post(f"{API}/admin/generos", json={"nombre": f"Urbano_{_uid()}"})
    gen_id = r.json()["id"]
    r = await client.post(
        f"{API}/admin/generos/{gen_id}/categorias", json={"nombre": f"Trap_{_uid()}"}
    )
    assert r.status_code == 201


async def test_admin_list_categorias(client, register_and_confirm, otp_for):
    await _make_admin(client, register_and_confirm, otp_for)
    r = await client.post(f"{API}/admin/generos", json={"nombre": f"Urbano_{_uid()}"})
    gen_id = r.json()["id"]
    await client.post(f"{API}/admin/generos/{gen_id}/categorias", json={"nombre": f"Trap_{_uid()}"})
    await client.post(f"{API}/admin/generos/{gen_id}/categorias", json={"nombre": f"Reggaeton_{_uid()}"})
    r = await client.get(f"{API}/admin/generos/{gen_id}/categorias")
    assert r.status_code == 200
    assert len(r.json()) == 2


async def test_admin_categoria_duplicada_409(client, register_and_confirm, otp_for):
    await _make_admin(client, register_and_confirm, otp_for)
    r = await client.post(f"{API}/admin/generos", json={"nombre": f"Rock_{_uid()}"})
    gen_id = r.json()["id"]
    nombre = f"Punk_{_uid()}"
    await client.post(f"{API}/admin/generos/{gen_id}/categorias", json={"nombre": nombre})
    r = await client.post(f"{API}/admin/generos/{gen_id}/categorias", json={"nombre": nombre})
    assert r.status_code == 409


async def test_admin_actualizar_categoria(client, register_and_confirm, otp_for):
    await _make_admin(client, register_and_confirm, otp_for)
    r = await client.post(f"{API}/admin/generos", json={"nombre": f"Pop_{_uid()}"})
    gen_id = r.json()["id"]
    r = await client.post(f"{API}/admin/generos/{gen_id}/categorias", json={"nombre": f"KPop_{_uid()}"})
    cat_id = r.json()["id"]
    nuevo = f"KoreanPop_{_uid()}"
    r = await client.patch(
        f"{API}/admin/generos/categorias/{cat_id}", json={"nombre": nuevo}
    )
    assert r.status_code == 200
    assert r.json()["nombre"] == nuevo


async def test_admin_desactivar_categoria(client, register_and_confirm, otp_for):
    await _make_admin(client, register_and_confirm, otp_for)
    r = await client.post(f"{API}/admin/generos", json={"nombre": f"Electronica_{_uid()}"})
    gen_id = r.json()["id"]
    r = await client.post(f"{API}/admin/generos/{gen_id}/categorias", json={"nombre": f"House_{_uid()}"})
    cat_id = r.json()["id"]
    r = await client.patch(f"{API}/admin/generos/categorias/{cat_id}", json={"activo": False})
    assert r.status_code == 200
    assert r.json()["activo"] is False


async def test_admin_eliminar_categoria(client, register_and_confirm, otp_for):
    await _make_admin(client, register_and_confirm, otp_for)
    r = await client.post(f"{API}/admin/generos", json={"nombre": f"Folk_{_uid()}"})
    gen_id = r.json()["id"]
    r = await client.post(f"{API}/admin/generos/{gen_id}/categorias", json={"nombre": f"Temp_{_uid()}"})
    cat_id = r.json()["id"]
    r = await client.delete(f"{API}/admin/generos/categorias/{cat_id}")
    assert r.status_code == 204


# ── Tests endpoint público ───────────────────────────────────────


async def test_public_generos_solo_activos(client, register_and_confirm, otp_for, make_client):
    await _make_admin(client, register_and_confirm, otp_for)
    nombre_activo = f"Activo_{_uid()}"
    nombre_inactivo = f"Inactivo_{_uid()}"
    await client.post(f"{API}/admin/generos", json={"nombre": nombre_activo})
    r2 = await client.post(f"{API}/admin/generos", json={"nombre": nombre_inactivo})
    await client.patch(f"{API}/admin/generos/{r2.json()['id']}", json={"activo": False})

    anon = await make_client()
    r = await anon.get(f"{API}/generos")
    assert r.status_code == 200
    nombres = [g["nombre"] for g in r.json()]
    assert nombre_activo in nombres
    assert nombre_inactivo not in nombres


async def test_public_generos_incluye_categorias_activas(client, register_and_confirm, otp_for, make_client):
    await _make_admin(client, register_and_confirm, otp_for)
    r = await client.post(f"{API}/admin/generos", json={"nombre": f"Electronica_{_uid()}"})
    gen_id = r.json()["id"]
    nombre_activo = f"Techno_{_uid()}"
    nombre_inactivo = f"House_{_uid()}"
    r = await client.post(f"{API}/admin/generos/{gen_id}/categorias", json={"nombre": nombre_inactivo})
    cat_inactivo_id = r.json()["id"]
    await client.post(f"{API}/admin/generos/{gen_id}/categorias", json={"nombre": nombre_activo})
    await client.patch(f"{API}/admin/generos/categorias/{cat_inactivo_id}", json={"activo": False})

    anon = await make_client()
    r = await anon.get(f"{API}/generos")
    assert r.status_code == 200
    for g in r.json():
        if g["id"] == gen_id:
            cat_nombres = [c["nombre"] for c in g["categorias"]]
            assert nombre_activo in cat_nombres
            assert nombre_inactivo not in cat_nombres


# ── Tests categorías por canal ───────────────────────────────────


async def test_crear_canal_con_categorias(client, register_and_confirm, otp_for, make_client):
    await _make_admin(client, register_and_confirm, otp_for)
    gen_id, cat1_id, cat2_id = await _crear_genero_con_categorias(client)

    cur = await make_client()
    await register_and_confirm(cur, "profesional")
    r = await cur.post(
        f"{API}/curador/medios",
        json={
            "nombre": f"Canal_{_uid()}",
            "tipo": "tiktok",
            "genero_ids": [gen_id],
            "categoria_ids": [cat1_id, cat2_id],
            "redes": [{"tipo": "tiktok", "url": f"https://tiktok.com/@{_uid()}", "es_principal": True}],
        },
    )
    assert r.status_code == 201
    data = r.json()
    assert cat1_id in data["categoria_ids"]
    assert cat2_id in data["categoria_ids"]


async def test_editar_canal_cambia_categorias(client, register_and_confirm, otp_for, make_client):
    await _make_admin(client, register_and_confirm, otp_for)
    gen_id, cat1_id, cat2_id = await _crear_genero_con_categorias(client)

    cur = await make_client()
    await register_and_confirm(cur, "profesional")
    r = await cur.post(
        f"{API}/curador/medios",
        json={
            "nombre": f"Canal_{_uid()}",
            "tipo": "tiktok",
            "genero_ids": [gen_id],
            "categoria_ids": [cat1_id],
            "redes": [{"tipo": "tiktok", "url": f"https://tiktok.com/@{_uid()}", "es_principal": True}],
        },
    )
    canal_id = r.json()["id"]

    r = await cur.patch(
        f"{API}/curador/medios/{canal_id}",
        json={"categoria_ids": [cat2_id]},
    )
    assert r.status_code == 200
    data = r.json()
    assert cat2_id in data["categoria_ids"]
    assert cat1_id not in data["categoria_ids"]


async def test_crear_canal_sin_categorias(client, register_and_confirm, otp_for, make_client):
    await _make_admin(client, register_and_confirm, otp_for)
    r = await client.post(f"{API}/admin/generos", json={"nombre": f"Test_{_uid()}"})
    gen_id = r.json()["id"]

    cur = await make_client()
    await register_and_confirm(cur, "profesional")
    r = await cur.post(
        f"{API}/curador/medios",
        json={
            "nombre": f"Canal_{_uid()}",
            "tipo": "blog",
            "genero_ids": [gen_id],
            "redes": [{"tipo": "website", "url": f"https://{_uid()}.com", "es_principal": True}],
        },
    )
    assert r.status_code == 201
    assert r.json()["categoria_ids"] == []
