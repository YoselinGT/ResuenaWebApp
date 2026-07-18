"""Servicio de autenticación: registro, confirmación, login, OTP, reset.

Orquesta password/token/otp/email/bitácora. Lanza excepciones de dominio tipadas
(nunca HTTPException). Realiza su propia unidad de trabajo (commit) y envía emails
únicamente después de un commit exitoso.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.settings import get_settings
from src.infra.redis_client import get_redis
from src.models.dto.auth import LoginDTO, RegisterDTO, ResetPasswordDTO
from src.models.enums import (
    EstadoSolicitudCurador,
    TipoToken,
    TipoUsuario,
)
from src.models.parametros_config import ParametroConfig
from src.models.solicitudes_curador import SolicitudCurador
from src.models.usuarios import Usuario
from src.services import (
    bitacora_service,
    email_service,
    otp_service,
    password_service,
    token_service,
)
from src.services.exceptions import (
    ConflictError,
    ForbiddenError,
    LockedError,
    UnauthorizedError,
    ValidationError,
)

settings = get_settings()

PERFIL_ARTISTA = 2
PERFIL_CURADOR = 3

CONFIRM_TTL_MIN = 60 * 24  # 24 h
RESET_TTL_MIN = 60         # 1 h
PREAUTH_TTL_SECONDS = 600  # 10 min

_PREAUTH_PREFIX = "preauth:"


# ── Helpers ──────────────────────────────────────────────────────
async def _get_int_param(session: AsyncSession, clave: str, default: int) -> int:
    valor = await session.scalar(
        select(ParametroConfig.valor_cifrado).where(ParametroConfig.clave == clave)
    )
    try:
        return int(valor) if valor is not None else default
    except ValueError:
        return default


async def _find_by_correo(session: AsyncSession, correo: str) -> Usuario | None:
    return await session.scalar(select(Usuario).where(Usuario.correo == correo))


# ── Registro ─────────────────────────────────────────────────────
async def register(
    session: AsyncSession, dto: RegisterDTO, tipo: TipoUsuario
) -> Usuario:
    correo = dto.correo.lower()
    if await _find_by_correo(session, correo) is not None:
        raise ConflictError("Ya existe una cuenta con ese correo")
    if not password_service.validate_pattern(dto.password):
        raise ValidationError(
            "La contraseña debe tener mínimo 8 caracteres, con mayúscula, "
            "minúscula, número y símbolo"
        )

    usuario = Usuario(
        nombre_completo=dto.nombre_completo,
        correo=correo,
        password_hash=password_service.hash_password(dto.password),
        tipo=tipo,
        perfil_id=PERFIL_ARTISTA if tipo == TipoUsuario.artista else PERFIL_CURADOR,
        activo=False,  # pendiente de confirmar email
    )
    session.add(usuario)
    await session.flush()

    raw_token = await token_service.create(
        session, TipoToken.confirmacion_email, usuario.id, CONFIRM_TTL_MIN
    )
    await bitacora_service.registrar(
        session, accion="registro", entidad="usuarios",
        entidad_id=usuario.id, autor_id=usuario.id, detalle={"tipo": tipo.value},
    )
    await session.commit()

    url = f"{settings.frontend_url}/confirm/{raw_token}"
    if tipo == TipoUsuario.artista:
        await email_service.send_confirm_artista(correo, usuario.nombre_completo, url)
    else:
        await email_service.send_confirm_profesional(correo, usuario.nombre_completo, url)
    return usuario


# ── Confirmación de email ────────────────────────────────────────
async def confirm(session: AsyncSession, raw_token: str) -> Usuario:
    token = await token_service.consume(session, raw_token, TipoToken.confirmacion_email)
    usuario = await session.get(Usuario, token.usuario_id)
    if usuario is None:
        raise UnauthorizedError("Token sin usuario asociado")
    usuario.activo = True
    await bitacora_service.registrar(
        session, accion="registro_confirmado", entidad="usuarios",
        entidad_id=usuario.id, autor_id=usuario.id,
    )
    await session.commit()
    return usuario


# ── Login (paso 1: credenciales → OTP) ───────────────────────────
async def login(session: AsyncSession, dto: LoginDTO) -> str:
    """Valida credenciales y dispara OTP. Devuelve el `pre_auth_session_id`."""
    correo = dto.correo.lower()
    usuario = await _find_by_correo(session, correo)
    credenciales_invalidas = UnauthorizedError("Correo o contraseña incorrectos")

    if usuario is None:
        raise credenciales_invalidas

    now = datetime.now(UTC)
    if usuario.blocked_until is not None and usuario.blocked_until > now:
        raise LockedError(usuario.blocked_until.isoformat())

    if not password_service.verify_password(dto.password, usuario.password_hash):
        usuario.intentos_fallidos += 1
        max_intentos = await _get_int_param(session, "max_intentos_login", 5)
        bloqueado = False
        if usuario.intentos_fallidos >= max_intentos:
            horas = await _get_int_param(session, "block_duration_hours", 6)
            usuario.blocked_until = now + timedelta(hours=horas)
            usuario.intentos_fallidos = 0
            bloqueado = True
        await bitacora_service.registrar(
            session, accion="login_fallido", entidad="usuarios", entidad_id=usuario.id,
        )
        await session.commit()
        if bloqueado:
            raise LockedError(usuario.blocked_until.isoformat())
        raise credenciales_invalidas

    if not usuario.activo:
        raise ForbiddenError("Debes confirmar tu correo para iniciar sesión")

    if usuario.tipo == TipoUsuario.curador:
        aprobada = await session.scalar(
            select(SolicitudCurador.id).where(
                SolicitudCurador.usuario_id == usuario.id,
                SolicitudCurador.estado == EstadoSolicitudCurador.aprobada,
            )
        )
        if aprobada is None:
            raise ForbiddenError("Tu solicitud de curador está en revisión")

    usuario.intentos_fallidos = 0
    await session.commit()

    sid = uuid.uuid4().hex
    await get_redis().set(f"{_PREAUTH_PREFIX}{sid}", str(usuario.id), ex=PREAUTH_TTL_SECONDS)
    code = await otp_service.generate(sid)
    await email_service.send_otp(usuario.correo, code)
    return sid


# ── Login (paso 2: verificar OTP → usuario autenticado) ──────────
async def verify_otp(session: AsyncSession, pre_auth_session_id: str, code: str) -> Usuario:
    if not await otp_service.verify(pre_auth_session_id, code):
        # No se invalida la sesión pre-autenticada: el usuario puede reintentar.
        raise UnauthorizedError("Código de verificación inválido")

    key = f"{_PREAUTH_PREFIX}{pre_auth_session_id}"
    user_id = await get_redis().get(key)
    if user_id is None:
        raise UnauthorizedError("Sesión de pre-autenticación expirada")
    await get_redis().delete(key)

    usuario = await session.get(Usuario, uuid.UUID(user_id))
    if usuario is None:
        raise UnauthorizedError("Usuario no encontrado")

    await bitacora_service.registrar(
        session, accion="login_exitoso", entidad="usuarios",
        entidad_id=usuario.id, autor_id=usuario.id,
    )
    await session.commit()
    return usuario


# ── Reset de password ────────────────────────────────────────────
async def forgot_password(session: AsyncSession, correo: str) -> None:
    """Genera token de reset y envía email. Idempotente y silencioso (siempre 200)."""
    usuario = await _find_by_correo(session, correo.lower())
    if usuario is None:
        return  # No revelar si el correo existe
    raw_token = await token_service.create(
        session, TipoToken.reset, usuario.id, RESET_TTL_MIN
    )
    await session.commit()
    url = f"{settings.frontend_url}/reset/{raw_token}"
    await email_service.send_reset(usuario.correo, usuario.nombre_completo, url)


async def reset_password(
    session: AsyncSession, raw_token: str, dto: ResetPasswordDTO
) -> None:
    if not password_service.validate_pattern(dto.password):
        raise ValidationError(
            "La contraseña debe tener mínimo 8 caracteres, con mayúscula, "
            "minúscula, número y símbolo"
        )
    token = await token_service.consume(session, raw_token, TipoToken.reset)
    usuario = await session.get(Usuario, token.usuario_id)
    if usuario is None:
        raise UnauthorizedError("Token sin usuario asociado")
    usuario.password_hash = password_service.hash_password(dto.password)
    usuario.intentos_fallidos = 0
    usuario.blocked_until = None
    await bitacora_service.registrar(
        session, accion="reset_password", entidad="usuarios",
        entidad_id=usuario.id, autor_id=usuario.id,
    )
    await session.commit()
