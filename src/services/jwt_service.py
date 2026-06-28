"""Servicio JWT — emisión y verificación del token de sesión.

El JWT viaja en una cookie HttpOnly + Secure + SameSite=Lax (regla no negociable).
Algoritmo HS256 con `APP_SECRET_KEY`. Expiración configurable.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from jose import JWTError, jwt

from src.config.settings import get_settings

settings = get_settings()

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 12  # 12 horas

COOKIE_NAME = "resuena_session"


def create_access_token(usuario_id: str, tipo: str, perfil_id: int) -> str:
    """Emite un JWT firmado para el usuario autenticado."""
    now = datetime.now(UTC)
    payload = {
        "sub": str(usuario_id),
        "tipo": tipo,
        "perfil_id": perfil_id,
        "iat": now,
        "exp": now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(payload, settings.app_secret_key, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    """Decodifica y valida el JWT. Devuelve el payload o None si es inválido."""
    try:
        return jwt.decode(token, settings.app_secret_key, algorithms=[ALGORITHM])
    except JWTError:
        return None


def cookie_kwargs() -> dict:
    """Atributos de la cookie de sesión según el entorno."""
    return {
        "key": COOKIE_NAME,
        "httponly": True,
        # En dev (http) Secure impediría enviar la cookie; se exige en prod.
        "secure": settings.is_production,
        "samesite": "lax",
        "max_age": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "path": "/",
    }
