"""Fixtures compartidos de pytest.

Los tests de integración corren contra la infraestructura de desarrollo real
(Postgres + Redis + MailHog) usando el ASGI app en memoria vía httpx. Para
aislar, cada test usa correos únicos (uuid). Helpers leen el token de la BD y
el OTP de Redis para completar los flujos sin depender del email.
"""

from __future__ import annotations

import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from src.infra.db import SessionLocal
from src.infra.redis_client import get_redis
from src.main import app
from src.models.enums import TipoToken
from src.models.tokens import Token
from src.models.usuarios import Usuario

API = "/api/auth"
STRONG_PW = "Str0ng!Pass"


@pytest.fixture(autouse=True)
async def _reset_redis():
    """Cada test usa su propio cliente Redis en su event loop.

    El singleton de `redis_client` quedaría atado al loop del primer test;
    pytest-asyncio crea un loop por test, así que lo reseteamos y cerramos.
    """
    import src.infra.redis_client as rc

    rc._client = None
    yield
    if rc._client is not None:
        await rc._client.aclose()
        rc._client = None


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def unique_email():
    return lambda: f"t_{uuid.uuid4().hex[:12]}@test.com"


@pytest.fixture
def token_for():
    """Devuelve el último token (por tipo) de un usuario, leído de la BD."""

    async def _get(correo: str, tipo: TipoToken = TipoToken.confirmacion_email) -> str:
        async with SessionLocal() as s:
            uid = await s.scalar(select(Usuario.id).where(Usuario.correo == correo))
            return await s.scalar(
                select(Token.token)
                .where(Token.usuario_id == uid, Token.tipo == tipo)
                .order_by(Token.created_at.desc())
            )

    return _get


@pytest.fixture
def otp_for():
    """Devuelve el OTP almacenado en Redis para un pre_auth_session_id."""

    async def _get(sid: str) -> str | None:
        return await get_redis().get(f"otp:{sid}")

    return _get


@pytest.fixture
def register_and_confirm(token_for):
    """Registra y confirma un usuario; el client queda con sesión (cookie).

    `tipo` es el segmento de URL: 'artista' o 'profesional'.
    Devuelve el correo creado.
    """

    async def _do(client: AsyncClient, tipo: str = "artista") -> str:
        correo = f"t_{uuid.uuid4().hex[:12]}@test.com"
        await client.post(
            f"{API}/register/{tipo}",
            json={"nombre_completo": "Test User", "correo": correo, "password": STRONG_PW},
        )
        tok = await token_for(correo)
        await client.get(f"{API}/confirm/{tok}")  # setea cookie de sesión
        return correo

    return _do
