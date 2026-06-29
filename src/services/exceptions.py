"""Excepciones de dominio de la capa de servicios.

Los services lanzan estas excepciones tipadas; el router las traduce a códigos
HTTP (ver src/api). Nunca se lanza HTTPException desde un service.
"""

from __future__ import annotations


class ServiceError(Exception):
    """Base de todos los errores de dominio."""


class NotFoundError(ServiceError):
    """Recurso inexistente. → 404."""


class ConflictError(ServiceError):
    """Conflicto de estado/unicidad (ej. correo duplicado). → 409."""


class ValidationError(ServiceError):
    """Entrada inválida según reglas de negocio. → 400/422."""


class UnauthorizedError(ServiceError):
    """Credenciales inválidas o sesión no autenticada. → 401."""


class ForbiddenError(ServiceError):
    """Autenticado pero sin permiso para la acción. → 403."""


class LockedError(ServiceError):
    """Cuenta bloqueada temporalmente. → 423."""


# ── Tokens ───────────────────────────────────────────────────────
class TokenInvalidoError(ServiceError):
    """Token inexistente o no corresponde al tipo esperado. → 400."""


class TokenExpiradoError(ServiceError):
    """Token vencido. → 410 Gone."""


class TokenConsumidoError(ServiceError):
    """Token de un solo uso ya utilizado. → 400."""
