"""Router de onboarding/perfil y catálogos públicos.

Las rutas de onboarding requieren sesión; las de medios, además, rol curador.
Los catálogos son públicos. La lógica vive en los services correspondientes.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.infra.db import get_session
from src.middleware.auth import CurrentUser, get_current_user, require_tipo
from src.models.dto.onboarding import (
    CuradorMedioDTO,
    CuradorMedioOutDTO,
    GeneroDTO,
    GenerosBody,
    IdiomaDTO,
    IdiomasBody,
    OnboardingProgressDTO,
    PreferenciasBody,
    RedSocialDTO,
    RedSocialOutDTO,
    RegionDTO,
    RegionesBody,
)
from src.models.enums import TipoUsuario
from src.models.usuario_redes import UsuarioRed
from src.services import (
    catalogo_service,
    curador_medio_service,
    onboarding_service,
)
from src.services.exceptions import NotFoundError
from sqlalchemy import select

router = APIRouter(tags=["onboarding"])

_solo_curador = require_tipo(TipoUsuario.curador.value)


def _uid(user: CurrentUser) -> uuid.UUID:
    return uuid.UUID(user.id)


# ── Catálogos (públicos) ─────────────────────────────────────────
@router.get("/catalogos/generos", response_model=list[GeneroDTO])
async def catalogo_generos(session: AsyncSession = Depends(get_session)):
    return await catalogo_service.get_generos(session)


@router.get("/catalogos/idiomas", response_model=list[IdiomaDTO])
async def catalogo_idiomas(session: AsyncSession = Depends(get_session)):
    return await catalogo_service.get_idiomas(session)


@router.get("/catalogos/regiones", response_model=list[RegionDTO])
async def catalogo_regiones(session: AsyncSession = Depends(get_session)):
    return await catalogo_service.get_regiones(session)


# ── Progreso ─────────────────────────────────────────────────────
@router.get("/onboarding/progreso", response_model=OnboardingProgressDTO)
async def progreso(
    session: AsyncSession = Depends(get_session),
    user: CurrentUser = Depends(get_current_user),
):
    return await onboarding_service.get_progreso(session, _uid(user))


# ── Guardado por paso ────────────────────────────────────────────
@router.put("/onboarding/generos", response_model=OnboardingProgressDTO)
async def put_generos(
    body: GenerosBody,
    session: AsyncSession = Depends(get_session),
    user: CurrentUser = Depends(get_current_user),
):
    await onboarding_service.save_generos(session, _uid(user), body.genero_ids)
    return await onboarding_service.get_progreso(session, _uid(user))


@router.put("/onboarding/idiomas", response_model=OnboardingProgressDTO)
async def put_idiomas(
    body: IdiomasBody,
    session: AsyncSession = Depends(get_session),
    user: CurrentUser = Depends(get_current_user),
):
    await onboarding_service.save_idiomas(session, _uid(user), body.codigos)
    return await onboarding_service.get_progreso(session, _uid(user))


@router.put("/onboarding/regiones", response_model=OnboardingProgressDTO)
async def put_regiones(
    body: RegionesBody,
    session: AsyncSession = Depends(get_session),
    user: CurrentUser = Depends(get_current_user),
):
    await onboarding_service.save_regiones(session, _uid(user), body.codigos)
    return await onboarding_service.get_progreso(session, _uid(user))


@router.put("/onboarding/preferencias", response_model=OnboardingProgressDTO)
async def put_preferencias(
    body: PreferenciasBody,
    session: AsyncSession = Depends(get_session),
    user: CurrentUser = Depends(get_current_user),
):
    await onboarding_service.save_preferencias(
        session, _uid(user), body.apertura_musical,
        body.acepta_todos_idiomas, body.tipo_lanzamientos,
    )
    return await onboarding_service.get_progreso(session, _uid(user))


# ── Redes sociales ───────────────────────────────────────────────
@router.get("/onboarding/redes", response_model=list[RedSocialOutDTO])
async def list_redes(
    session: AsyncSession = Depends(get_session),
    user: CurrentUser = Depends(get_current_user),
):
    redes = (
        await session.scalars(
            select(UsuarioRed).where(UsuarioRed.usuario_id == _uid(user))
        )
    ).all()
    return [
        RedSocialOutDTO(id=str(r.id), tipo=r.tipo.value, url=r.url) for r in redes
    ]


@router.post("/onboarding/redes", response_model=OnboardingProgressDTO,
             status_code=status.HTTP_201_CREATED)
async def add_red(
    red: RedSocialDTO,
    session: AsyncSession = Depends(get_session),
    user: CurrentUser = Depends(get_current_user),
):
    # Reemplaza el conjunto: agrega la nueva manteniendo las existentes.
    existentes = (
        await session.scalars(
            select(UsuarioRed).where(UsuarioRed.usuario_id == _uid(user))
        )
    ).all()
    actuales = [RedSocialDTO(tipo=e.tipo, url=e.url) for e in existentes]
    actuales.append(red)
    await onboarding_service.save_redes(session, _uid(user), actuales)
    return await onboarding_service.get_progreso(session, _uid(user))


@router.delete("/onboarding/redes/{red_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_red(
    red_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    user: CurrentUser = Depends(get_current_user),
):
    red = await session.get(UsuarioRed, red_id)
    if red is None or red.usuario_id != _uid(user):
        raise NotFoundError("Red social no encontrada")
    await session.delete(red)
    await session.commit()


# ── Medios del curador (solo curadores) ──────────────────────────
@router.get("/onboarding/medios", response_model=list[CuradorMedioOutDTO])
async def list_medios(
    session: AsyncSession = Depends(get_session),
    user: CurrentUser = Depends(_solo_curador),
):
    return await curador_medio_service.list_medios(session, _uid(user))


@router.post("/onboarding/medios", response_model=CuradorMedioOutDTO,
             status_code=status.HTTP_201_CREATED)
async def add_medio(
    dto: CuradorMedioDTO,
    session: AsyncSession = Depends(get_session),
    user: CurrentUser = Depends(_solo_curador),
):
    return await curador_medio_service.add_medio(session, _uid(user), dto)


@router.put("/onboarding/medios/{medio_id}", response_model=CuradorMedioOutDTO)
async def update_medio(
    medio_id: uuid.UUID,
    dto: CuradorMedioDTO,
    session: AsyncSession = Depends(get_session),
    user: CurrentUser = Depends(_solo_curador),
):
    return await curador_medio_service.update_medio(session, medio_id, _uid(user), dto)


@router.delete("/onboarding/medios/{medio_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_medio(
    medio_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    user: CurrentUser = Depends(_solo_curador),
):
    await curador_medio_service.delete_medio(session, medio_id, _uid(user))
