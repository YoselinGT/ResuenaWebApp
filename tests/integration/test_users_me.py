"""Tests de integración del módulo de perfil (`/users/me`) y `StorageService`.

El almacenamiento se aísla con un `StubProvider` que implementa el Protocol
`StorageProvider`, inyectado vía dependency override. Así los tests de foto no
dependen de LocalStack y se verifica de paso que `StorageService` es swappable
sin tocar el código de negocio.
"""

from __future__ import annotations

import uuid
from io import BytesIO

import pytest
from httpx import AsyncClient
from PIL import Image
from sqlalchemy import select

from src.infra.db import SessionLocal
from src.infra.storage import StorageService, get_storage_service
from src.main import app
from src.models.bitacora_eventos import BitacoraEvento
from src.models.usuarios import Usuario
from src.services.user_service import FOTO_URL_TTL_SECONDS

API = "/api"


# ── Stub de almacenamiento ───────────────────────────────────────
class StubProvider:
    """Implementa el Protocol StorageProvider en memoria."""

    def __init__(self) -> None:
        self.uploaded: dict[str, tuple[bytes, str]] = {}
        self.deleted: list[str] = []

    async def upload(self, key: str, data: bytes, content_type: str) -> str:
        self.uploaded[key] = (data, content_type)
        return key

    async def delete(self, key: str) -> None:
        self.deleted.append(key)

    async def presigned_url(self, key: str, expires_seconds: int = 3600) -> str:
        return f"stub://{key}?ttl={expires_seconds}"


@pytest.fixture
def stub_storage():
    """Inyecta un StorageService respaldado por el stub. Devuelve el stub."""
    stub = StubProvider()
    app.dependency_overrides[get_storage_service] = lambda: StorageService(stub)
    yield stub
    app.dependency_overrides.pop(get_storage_service, None)


def _jpeg(size: tuple[int, int] = (320, 200)) -> bytes:
    buf = BytesIO()
    Image.new("RGB", size, (90, 40, 160)).save(buf, "JPEG")
    return buf.getvalue()


def _png(size: tuple[int, int] = (64, 64)) -> bytes:
    buf = BytesIO()
    Image.new("RGBA", size, (0, 255, 0, 255)).save(buf, "PNG")
    return buf.getvalue()


async def _me(client: AsyncClient) -> dict:
    return (await client.get(f"{API}/users/me")).json()


# ── GET /users/me ────────────────────────────────────────────────
async def test_get_me_requires_session(client):
    r = await client.get(f"{API}/users/me")
    assert r.status_code == 401


async def test_get_me_curador_incluye_estado(client, register_and_confirm):
    await register_and_confirm(client, "profesional")
    await client.post(
        f"{API}/auth/aplicar", json={"tipo_profesional": "blogger"}
    )
    me = await _me(client)
    assert me["tipo"] == "curador"
    assert me["estado_curador"] == "pendiente"
    assert me["foto_url"] is None


# ── PATCH /users/me ──────────────────────────────────────────────
async def test_patch_ignora_campos_no_editables(client, register_and_confirm):
    correo = await register_and_confirm(client, "artista")
    r = await client.patch(
        f"{API}/users/me",
        json={
            "nombre_completo": "Nombre Nuevo",
            "correo": "atacante@evil.com",
            "tipo": "curador",
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["nombre_completo"] == "Nombre Nuevo"
    assert body["correo"] == correo  # correo NO cambió
    assert body["tipo"] == "artista"  # tipo NO cambió


async def test_patch_sanitiza_xss(client, register_and_confirm):
    await register_and_confirm(client, "artista")
    r = await client.patch(
        f"{API}/users/me",
        json={"nombre_completo": "<script>alert(1)</script>Ada"},
    )
    assert r.status_code == 200
    assert "<" not in r.json()["nombre_completo"]


async def test_patch_registra_bitacora(client, register_and_confirm):
    await register_and_confirm(client, "artista")
    me = await _me(client)
    await client.patch(f"{API}/users/me", json={"nombre_completo": "Otro Nombre"})

    async with SessionLocal() as s:
        evento = await s.scalar(
            select(BitacoraEvento)
            .where(
                BitacoraEvento.autor_id == uuid.UUID(me["id"]),
                BitacoraEvento.accion == "Actualización de perfil propio",
            )
            .order_by(BitacoraEvento.created_at.desc())
        )
    assert evento is not None
    assert evento.detalle["cambios"]["nombre_completo"]["despues"] == "Otro Nombre"


# ── Foto de perfil (con StorageService stub) ─────────────────────
async def test_upload_png_rechazado_415(client, register_and_confirm, stub_storage):
    await register_and_confirm(client, "artista")
    r = await client.post(
        f"{API}/users/me/photo",
        files={"file": ("foto.png", _png(), "image/png")},
    )
    assert r.status_code == 415
    assert stub_storage.uploaded == {}  # no se subió nada


async def test_upload_jpg_ok(client, register_and_confirm, stub_storage):
    await register_and_confirm(client, "artista")
    me = await _me(client)
    r = await client.post(
        f"{API}/users/me/photo",
        files={"file": ("foto.jpg", _jpeg((640, 360)), "image/jpeg")},
    )
    assert r.status_code == 200

    key = f"perfiles-avatar/{me['id']}.jpg"
    # foto_path se guarda como la CLAVE, no como URL
    async with SessionLocal() as s:
        foto_path = await s.scalar(
            select(Usuario.foto_path).where(Usuario.id == uuid.UUID(me["id"]))
        )
    assert foto_path == key

    # el stub recibió el objeto, reencodeado a JPEG 200×200
    assert key in stub_storage.uploaded
    data, content_type = stub_storage.uploaded[key]
    assert content_type == "image/jpeg"
    assert Image.open(BytesIO(data)).size == (200, 200)


async def test_get_me_foto_url_presigned_con_ttl(
    client, register_and_confirm, stub_storage
):
    await register_and_confirm(client, "artista")
    await client.post(
        f"{API}/users/me/photo",
        files={"file": ("foto.jpg", _jpeg(), "image/jpeg")},
    )
    me = await _me(client)
    assert me["foto_url"] is not None
    # El stub codifica el TTL en la URL: confirma que se pasa FOTO_URL_TTL_SECONDS.
    assert f"ttl={FOTO_URL_TTL_SECONDS}" in me["foto_url"]


async def test_delete_photo_idempotente(client, register_and_confirm, stub_storage):
    await register_and_confirm(client, "artista")
    me = await _me(client)
    key = f"perfiles-avatar/{me['id']}.jpg"
    await client.post(
        f"{API}/users/me/photo",
        files={"file": ("foto.jpg", _jpeg(), "image/jpeg")},
    )

    r1 = await client.delete(f"{API}/users/me/photo")
    assert r1.status_code == 200
    assert r1.json()["foto_url"] is None
    assert key in stub_storage.deleted

    async with SessionLocal() as s:
        foto_path = await s.scalar(
            select(Usuario.foto_path).where(Usuario.id == uuid.UUID(me["id"]))
        )
    assert foto_path is None

    # Segundo delete sin foto: idempotente, no vuelve a llamar al storage.
    r2 = await client.delete(f"{API}/users/me/photo")
    assert r2.status_code == 200
    assert stub_storage.deleted.count(key) == 1


# ── StorageService swappable (Protocol) ──────────────────────────
async def test_storage_service_usa_provider_inyectado():
    stub = StubProvider()
    svc = StorageService(stub)

    returned = await svc.upload("k/x.jpg", b"data", "image/jpeg")
    assert returned == "k/x.jpg"
    assert stub.uploaded["k/x.jpg"] == (b"data", "image/jpeg")

    url = await svc.presigned_url("k/x.jpg", 120)
    assert url == "stub://k/x.jpg?ttl=120"

    await svc.delete("k/x.jpg")
    assert stub.deleted == ["k/x.jpg"]


async def test_config_publica_sin_sesion(client):
    r = await client.get(f"{API}/config/public")
    assert r.status_code == 200
    body = r.json()
    assert "titulo_plataforma" in body and "mensaje_bienvenida" in body
