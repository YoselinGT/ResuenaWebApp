"""Servicio de OTP (one-time password) para el segundo factor de login.

Genera un código numérico de 6 dígitos y lo guarda en Redis con TTL de 10 min,
asociado al `pre_auth_session_id` emitido al validar credenciales. El código se
consume (borra) solo cuando la verificación es correcta; un código incorrecto
no invalida la sesión pre-autenticada (el usuario puede reintentar).
"""

from __future__ import annotations

import secrets

from src.infra.redis_client import get_redis

OTP_TTL_SECONDS = 600  # 10 minutos
_OTP_DIGITS = 6


def _key(pre_auth_session_id: str) -> str:
    return f"otp:{pre_auth_session_id}"


async def generate(pre_auth_session_id: str) -> str:
    """Genera y almacena un OTP de 6 dígitos; devuelve el código (para email)."""
    code = f"{secrets.randbelow(10 ** _OTP_DIGITS):0{_OTP_DIGITS}d}"
    await get_redis().set(_key(pre_auth_session_id), code, ex=OTP_TTL_SECONDS)
    return code


async def verify(pre_auth_session_id: str, code: str) -> bool:
    """Valida el OTP. Si coincide, lo consume y devuelve True. No lanza."""
    stored = await get_redis().get(_key(pre_auth_session_id))
    if stored is None:
        return False
    if not secrets.compare_digest(stored, code):
        return False
    await get_redis().delete(_key(pre_auth_session_id))
    return True
