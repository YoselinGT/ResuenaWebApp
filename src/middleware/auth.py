"""Middleware y dependencias de autenticación.

`AuthMiddleware` decodifica el JWT de la cookie en cada request y deja el usuario
en `request.state.user` (o None). No bloquea: las rutas públicas siguen abiertas.
La protección por ruta se hace con las dependencias `get_current_user` /
`require_tipo`, que sí lanzan excepciones de dominio.
"""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from src.services.exceptions import ForbiddenError, UnauthorizedError
from src.services.jwt_service import COOKIE_NAME, decode_access_token


@dataclass
class CurrentUser:
    id: str
    tipo: str
    perfil_id: int


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request.state.user = None
        token = request.cookies.get(COOKIE_NAME)
        if token:
            payload = decode_access_token(token)
            if payload and payload.get("sub"):
                request.state.user = CurrentUser(
                    id=payload["sub"],
                    tipo=payload.get("tipo", ""),
                    perfil_id=payload.get("perfil_id", 0),
                )
        return await call_next(request)


def get_current_user(request: Request) -> CurrentUser:
    """Dependencia: exige sesión válida. → 401 si no hay usuario."""
    user = getattr(request.state, "user", None)
    if user is None:
        raise UnauthorizedError("No autenticado")
    return user


def require_tipo(*tipos: str):
    """Factory de dependencia: exige que el usuario sea de uno de los tipos dados."""

    def _dep(request: Request) -> CurrentUser:
        user = get_current_user(request)
        if user.tipo not in tipos:
            raise ForbiddenError("No tienes permiso para esta acción")
        return user

    return _dep
