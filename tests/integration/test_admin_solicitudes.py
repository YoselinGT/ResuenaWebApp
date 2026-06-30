"""Tests del flujo admin de aprobación/rechazo de curadores (Fase 05)."""

from __future__ import annotations

import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from src.infra.db import SessionLocal
from src.main import app
from src.models.bitacora_eventos import BitacoraEvento
from src.models.solicitudes_curador import SolicitudCurador
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


async def aplicar_curador(client, register_and_confirm) -> str:
    correo = await register_and_confirm(client, "profesional")
    await client.post(f"{API}/auth/aplicar", json={"tipo_profesional": "blogger"})
    return correo


async def _solicitud_id(correo: str) -> str:
    async with SessionLocal() as s:
        uid = await s.scalar(select(Usuario.id).where(Usuario.correo == correo))
        return str(
            await s.scalar(
                select(SolicitudCurador.id)
                .where(SolicitudCurador.usuario_id == uid)
                .order_by(SolicitudCurador.created_at.desc())
            )
        )


async def test_aprobar_habilita_curador(make_client, register_and_confirm, otp_for):
    admin = await make_client()
    await make_admin(admin, register_and_confirm, otp_for)
    cur = await make_client()
    correo = await aplicar_curador(cur, register_and_confirm)
    sid = await _solicitud_id(correo)

    # Antes de aprobar no puede crear medios.
    pre = await cur.post(f"{API}/curador/medios", json={"nombre": "X", "tipo": "blog"})
    assert pre.status_code == 403

    r = await admin.post(f"{API}/admin/solicitudes/{sid}/aprobar")
    assert r.status_code == 200
    assert r.json()["estado"] == "aprobada"

    # Ahora sí.
    post = await cur.post(
        f"{API}/curador/medios", json={"nombre": "Mi Blog", "tipo": "blog"}
    )
    assert post.status_code == 201

    # Bitácora.
    async with SessionLocal() as s:
        ev = await s.scalar(
            select(BitacoraEvento).where(
                BitacoraEvento.entidad_id == sid,
                BitacoraEvento.accion == "aprobacion_curador",
            )
        )
    assert ev is not None


async def test_rechazar_bloquea_login(make_client, register_and_confirm, otp_for):
    admin = await make_client()
    await make_admin(admin, register_and_confirm, otp_for)
    cur = await make_client()
    correo = await aplicar_curador(cur, register_and_confirm)
    sid = await _solicitud_id(correo)

    r = await admin.post(
        f"{API}/admin/solicitudes/{sid}/rechazar",
        json={"motivo": "Portfolio insuficiente."},
    )
    assert r.status_code == 200
    assert r.json()["estado"] == "rechazada"

    # El curador rechazado no puede iniciar sesión.
    login = await cur.post(
        f"{API}/auth/login", json={"correo": correo, "password": STRONG_PW}
    )
    assert login.status_code == 403

    async with SessionLocal() as s:
        ev = await s.scalar(
            select(BitacoraEvento).where(
                BitacoraEvento.entidad_id == sid,
                BitacoraEvento.accion == "rechazo_curador",
            )
        )
    assert ev is not None


async def test_aprobar_sin_admin_403(make_client, register_and_confirm):
    cur = await make_client()
    correo = await aplicar_curador(cur, register_and_confirm)
    sid = await _solicitud_id(correo)
    # El propio curador (no admin) intenta aprobar su solicitud.
    r = await cur.post(f"{API}/admin/solicitudes/{sid}/aprobar")
    assert r.status_code == 403


async def test_reaprobar_409(make_client, register_and_confirm, otp_for):
    admin = await make_client()
    await make_admin(admin, register_and_confirm, otp_for)
    cur = await make_client()
    correo = await aplicar_curador(cur, register_and_confirm)
    sid = await _solicitud_id(correo)
    assert (await admin.post(f"{API}/admin/solicitudes/{sid}/aprobar")).status_code == 200
    assert (await admin.post(f"{API}/admin/solicitudes/{sid}/aprobar")).status_code == 409


async def test_patch_admin_protegido(make_client, register_and_confirm, otp_for):
    admin = await make_client()
    await make_admin(admin, register_and_confirm, otp_for)
    admin_id = (await admin.get(f"{API}/users/me")).json()["id"]
    # Un admin no puede editarse a sí mismo (ni a otros admins) por esta vía.
    r = await admin.patch(
        f"{API}/admin/usuarios/{admin_id}", json={"activo": False}
    )
    assert r.status_code == 403


async def test_solicitud_inexistente_404(make_client, register_and_confirm, otp_for):
    admin = await make_client()
    await make_admin(admin, register_and_confirm, otp_for)
    r = await admin.get(f"{API}/admin/solicitudes/{uuid.uuid4()}")
    assert r.status_code == 404
