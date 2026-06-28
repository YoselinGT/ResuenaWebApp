"""Router de autenticación.

Cada endpoint delega la lógica al `auth_service`; aquí solo se mapean DTOs,
cookies de sesión y respuestas HTTP. Las excepciones de dominio las traduce el
handler central (src/api/errors.py).
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.infra.db import get_session
from src.models.dto.auth import (
    AplicarDTO,
    ForgotPasswordDTO,
    LoginDTO,
    LoginResponseDTO,
    OTPVerifyDTO,
    RegisterDTO,
    ResetPasswordDTO,
    UsuarioPublicoDTO,
)
from src.models.enums import TipoUsuario
from src.middleware.auth import CurrentUser, get_current_user, require_tipo
from src.models.usuarios import Usuario
from src.services import auth_service
from src.services.exceptions import UnauthorizedError
from src.services.jwt_service import COOKIE_NAME, cookie_kwargs, create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


def _to_public(usuario) -> UsuarioPublicoDTO:
    return UsuarioPublicoDTO(
        id=str(usuario.id),
        nombre_completo=usuario.nombre_completo,
        correo=usuario.correo,
        tipo=usuario.tipo.value if hasattr(usuario.tipo, "value") else usuario.tipo,
    )


@router.post("/register/artista", status_code=status.HTTP_201_CREATED)
async def register_artista(
    dto: RegisterDTO, session: AsyncSession = Depends(get_session)
) -> dict:
    await auth_service.register(session, dto, TipoUsuario.artista)
    return {"mensaje": "Cuenta creada. Revisa tu correo para confirmarla."}


@router.post("/register/profesional", status_code=status.HTTP_201_CREATED)
async def register_profesional(
    dto: RegisterDTO, session: AsyncSession = Depends(get_session)
) -> dict:
    await auth_service.register(session, dto, TipoUsuario.curador)
    return {"mensaje": "Cuenta creada. Revisa tu correo para confirmarla."}


@router.get("/confirm/{token}")
async def confirm(
    token: str,
    response: Response,
    session: AsyncSession = Depends(get_session),
) -> dict:
    usuario = await auth_service.confirm(session, token)
    # Tras confirmar el email se emite la sesión: el usuario ya probó posesión
    # del correo y necesita acceso inmediato para completar onboarding (y, en
    # profesionales, enviar su aplicación). El login con OTP es para reingresos.
    jwt = create_access_token(str(usuario.id), usuario.tipo.value, usuario.perfil_id)
    response.set_cookie(value=jwt, **cookie_kwargs())
    # Profesionales → /aplicar; artistas → wizard de onboarding.
    siguiente = "/aplicar" if usuario.tipo == TipoUsuario.curador else "/onboarding/generos"
    return {"mensaje": "Cuenta confirmada", "siguiente": siguiente}


@router.post("/aplicar", status_code=status.HTTP_201_CREATED)
async def aplicar(
    dto: AplicarDTO,
    session: AsyncSession = Depends(get_session),
    user: CurrentUser = Depends(require_tipo(TipoUsuario.curador.value)),
) -> dict:
    await auth_service.aplicar(session, uuid.UUID(user.id), dto)
    return {"mensaje": "Solicitud enviada. Te avisaremos cuando sea revisada."}


@router.post("/login", response_model=LoginResponseDTO)
async def login(
    dto: LoginDTO, session: AsyncSession = Depends(get_session)
) -> LoginResponseDTO:
    sid = await auth_service.login(session, dto)
    return LoginResponseDTO(pre_auth_session_id=sid)


@router.post("/otp/verify")
async def otp_verify(
    dto: OTPVerifyDTO,
    response: Response,
    session: AsyncSession = Depends(get_session),
) -> dict:
    usuario = await auth_service.verify_otp(session, dto.pre_auth_session_id, dto.code)
    token = create_access_token(
        str(usuario.id), usuario.tipo.value, usuario.perfil_id
    )
    response.set_cookie(value=token, **cookie_kwargs())
    return {"usuario": _to_public(usuario).model_dump()}


@router.post("/forgot-password")
async def forgot_password(
    dto: ForgotPasswordDTO, session: AsyncSession = Depends(get_session)
) -> dict:
    await auth_service.forgot_password(session, dto.correo)
    # Siempre 200, no revela si el correo existe.
    return {"mensaje": "Si el correo existe, enviamos instrucciones de recuperación."}


@router.post("/reset-password/{token}")
async def reset_password(
    token: str, dto: ResetPasswordDTO, session: AsyncSession = Depends(get_session)
) -> dict:
    await auth_service.reset_password(session, token, dto)
    return {"mensaje": "Contraseña actualizada. Ya puedes iniciar sesión."}


@router.post("/logout")
async def logout(response: Response) -> dict:
    response.delete_cookie(key=COOKIE_NAME, path="/")
    return {"mensaje": "Sesión cerrada"}


@router.get("/me", response_model=UsuarioPublicoDTO)
async def me(
    session: AsyncSession = Depends(get_session),
    user: CurrentUser = Depends(get_current_user),
) -> UsuarioPublicoDTO:
    usuario = await session.get(Usuario, uuid.UUID(user.id))
    if usuario is None:
        raise UnauthorizedError("Usuario no encontrado")
    return _to_public(usuario)
