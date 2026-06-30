"""Traducción centralizada de excepciones de dominio → respuestas HTTP.

Los services lanzan `ServiceError` (y subclases); aquí se mapean a códigos HTTP
con un envelope consistente. Mantiene los routers libres de lógica de errores.
"""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.services.exceptions import (
    ConflictError,
    ForbiddenError,
    InsufficientCreditsError,
    LockedError,
    NotFoundError,
    ServiceError,
    TokenConsumidoError,
    TokenExpiradoError,
    TokenInvalidoError,
    UnauthorizedError,
    UnsupportedMediaTypeError,
    ValidationError,
)

# Orden: de más específico a más general (se evalúa con isinstance).
_MAPPING: list[tuple[type[ServiceError], int, str]] = [
    (TokenExpiradoError, 410, "TOKEN_EXPIRED"),
    (TokenConsumidoError, 400, "TOKEN_CONSUMED"),
    (TokenInvalidoError, 400, "TOKEN_INVALID"),
    (ConflictError, 409, "CONFLICT"),
    (ValidationError, 422, "VALIDATION_ERROR"),
    (UnauthorizedError, 401, "UNAUTHORIZED"),
    (ForbiddenError, 403, "FORBIDDEN"),
    (LockedError, 423, "LOCKED"),
    (NotFoundError, 404, "NOT_FOUND"),
    (UnsupportedMediaTypeError, 415, "UNSUPPORTED_MEDIA_TYPE"),
    (InsufficientCreditsError, 409, "INSUFFICIENT_CREDITS"),
]


def _resolve(exc: ServiceError) -> tuple[int, str]:
    for cls, status, code in _MAPPING:
        if isinstance(exc, cls):
            return status, code
    return 400, "BAD_REQUEST"


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(ServiceError)
    async def _handle_service_error(_: Request, exc: ServiceError) -> JSONResponse:
        status, code = _resolve(exc)
        return JSONResponse(
            status_code=status,
            content={"error": {"code": code, "message": str(exc)}},
        )
