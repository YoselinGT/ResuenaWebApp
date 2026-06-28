"""Tests de integración de los endpoints de autenticación.

Corren contra Postgres + Redis + MailHog reales vía ASGI en memoria.
"""

from __future__ import annotations

from src.models.enums import TipoToken
from tests.conftest import API, STRONG_PW


async def _login_otp(client, correo, token_for, otp_for) -> dict:
    """Helper: login + verificación OTP. Devuelve la respuesta de /otp/verify."""
    r = await client.post(f"{API}/login", json={"correo": correo, "password": STRONG_PW})
    sid = r.json()["pre_auth_session_id"]
    code = await otp_for(sid)
    return await client.post(
        f"{API}/otp/verify", json={"pre_auth_session_id": sid, "code": code}
    )


async def test_happy_path_artista(client, register_and_confirm, token_for, otp_for):
    correo = await register_and_confirm(client, "artista")
    r = await _login_otp(client, correo, token_for, otp_for)
    assert r.status_code == 200
    assert r.json()["usuario"]["correo"] == correo
    me = await client.get(f"{API}/me")
    assert me.status_code == 200
    assert me.json()["tipo"] == "artista"


async def test_me_sin_sesion_401(client):
    r = await client.get(f"{API}/me")
    assert r.status_code == 401


async def test_correo_duplicado_409(client, unique_email):
    correo = unique_email()
    body = {"nombre_completo": "Dup", "correo": correo, "password": STRONG_PW}
    assert (await client.post(f"{API}/register/artista", json=body)).status_code == 201
    assert (await client.post(f"{API}/register/artista", json=body)).status_code == 409


async def test_password_debil_rechazada(client, unique_email):
    body = {"nombre_completo": "Weak", "correo": unique_email(), "password": "weakpass"}
    # Pydantic (min_length) o el service (patrón) → ambos son 4xx de validación.
    assert (await client.post(f"{API}/register/artista", json=body)).status_code == 422


async def test_login_password_incorrecta_401(client, register_and_confirm):
    correo = await register_and_confirm(client, "artista")
    r = await client.post(f"{API}/login", json={"correo": correo, "password": "Wr0ng!Pass"})
    assert r.status_code == 401


async def test_otp_incorrecto_401_y_luego_correcto(client, register_and_confirm, otp_for):
    correo = await register_and_confirm(client, "artista")
    r = await client.post(f"{API}/login", json={"correo": correo, "password": STRONG_PW})
    sid = r.json()["pre_auth_session_id"]
    bad = await client.post(
        f"{API}/otp/verify", json={"pre_auth_session_id": sid, "code": "000000"}
    )
    assert bad.status_code == 401
    code = await otp_for(sid)  # sesión no invalidada: el código sigue vigente
    ok = await client.post(
        f"{API}/otp/verify", json={"pre_auth_session_id": sid, "code": code}
    )
    assert ok.status_code == 200


async def test_confirm_token_invalido_400(client):
    r = await client.get(f"{API}/confirm/token-inexistente")
    assert r.status_code == 400


async def test_forgot_y_reset(client, register_and_confirm, token_for):
    correo = await register_and_confirm(client, "artista")
    assert (await client.post(f"{API}/forgot-password", json={"correo": correo})).status_code == 200
    reset_tok = await token_for(correo, TipoToken.reset)
    nueva = "NewStr0ng!2"
    assert (
        await client.post(f"{API}/reset-password/{reset_tok}", json={"password": nueva})
    ).status_code == 200
    # Token de un solo uso: reuso → 400.
    assert (
        await client.post(f"{API}/reset-password/{reset_tok}", json={"password": nueva})
    ).status_code == 400


async def test_forgot_correo_inexistente_igual_200(client, unique_email):
    r = await client.post(f"{API}/forgot-password", json={"correo": unique_email()})
    assert r.status_code == 200  # no revela si el correo existe


async def test_profesional_no_aprobado_login_403(client, register_and_confirm):
    correo = await register_and_confirm(client, "profesional")
    r = await client.post(f"{API}/login", json={"correo": correo, "password": STRONG_PW})
    assert r.status_code == 403


async def test_bloqueo_tras_5_intentos_fallidos(client, register_and_confirm):
    correo = await register_and_confirm(client, "artista")
    codes = []
    for _ in range(5):
        r = await client.post(
            f"{API}/login", json={"correo": correo, "password": "Wr0ng!Pass"}
        )
        codes.append(r.status_code)
    assert codes[:4] == [401, 401, 401, 401]
    assert codes[4] == 423
    # Aún con la password correcta sigue bloqueado.
    r = await client.post(f"{API}/login", json={"correo": correo, "password": STRONG_PW})
    assert r.status_code == 423
