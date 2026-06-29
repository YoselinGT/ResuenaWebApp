"""Router de sellos discográficos (`/sellos`).

Requiere sesión de artista. La lógica vive en `sello_service`.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.infra.db import get_session
from src.infra.storage import StorageService, get_storage_service
from src.middleware.auth import CurrentUser, require_tipo
from src.models.dto.sellos import (
    InvitacionDetalleDTO,
    InvitacionOutDTO,
    InvitarBody,
    MiembroDTO,
    SelloDetalleDTO,
    SelloOutDTO,
    TransferOwnershipBody,
)
from src.models.enums import TipoUsuario
from src.services import sello_service

router = APIRouter(prefix="/sellos", tags=["sellos"])

_solo_artista = require_tipo(TipoUsuario.artista.value)


@router.get("/mio", response_model=SelloDetalleDTO | None)
async def mi_sello(
    session: AsyncSession = Depends(get_session),
    user: CurrentUser = Depends(_solo_artista),
    storage: StorageService = Depends(get_storage_service),
) -> SelloDetalleDTO | None:
    return await sello_service.get_mi_sello(session, storage, uuid.UUID(user.id))


@router.get("/invitacion/{token}", response_model=InvitacionDetalleDTO)
async def ver_invitacion(
    token: str,
    session: AsyncSession = Depends(get_session),
    user: CurrentUser = Depends(_solo_artista),
    storage: StorageService = Depends(get_storage_service),
) -> InvitacionDetalleDTO:
    return await sello_service.get_invitacion(session, storage, token)


@router.post("/aceptar-invitacion/{token}", response_model=SelloDetalleDTO)
async def aceptar_invitacion(
    token: str,
    session: AsyncSession = Depends(get_session),
    user: CurrentUser = Depends(_solo_artista),
    storage: StorageService = Depends(get_storage_service),
) -> SelloDetalleDTO:
    return await sello_service.aceptar_invitacion(
        session, storage, uuid.UUID(user.id), token
    )


@router.post(
    "/rechazar-invitacion/{token}", status_code=status.HTTP_204_NO_CONTENT
)
async def rechazar_invitacion(
    token: str,
    session: AsyncSession = Depends(get_session),
    user: CurrentUser = Depends(_solo_artista),
):
    await sello_service.rechazar_invitacion(session, uuid.UUID(user.id), token)


@router.post("/{sello_id}/salir", status_code=status.HTTP_204_NO_CONTENT)
async def salir_del_sello(
    sello_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    user: CurrentUser = Depends(_solo_artista),
):
    await sello_service.salir_del_sello(session, uuid.UUID(user.id), sello_id)


@router.post("/{sello_id}/transferir-ownership", response_model=SelloDetalleDTO)
async def transferir_ownership(
    sello_id: uuid.UUID,
    body: TransferOwnershipBody,
    session: AsyncSession = Depends(get_session),
    user: CurrentUser = Depends(_solo_artista),
    storage: StorageService = Depends(get_storage_service),
) -> SelloDetalleDTO:
    return await sello_service.transferir_ownership(
        session, storage, uuid.UUID(user.id), sello_id, body.nuevo_owner_id
    )


@router.get("/{sello_id}/artistas", response_model=list[MiembroDTO])
async def listar_artistas(
    sello_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    user: CurrentUser = Depends(_solo_artista),
    storage: StorageService = Depends(get_storage_service),
) -> list[MiembroDTO]:
    return await sello_service.listar_artistas(
        session, storage, uuid.UUID(user.id), sello_id
    )


@router.patch("/{sello_id}", response_model=SelloDetalleDTO)
async def editar_sello(
    sello_id: uuid.UUID,
    nombre: str | None = Form(None),
    descripcion: str | None = Form(None),
    website: str | None = Form(None),
    logo: UploadFile | None = File(None),
    session: AsyncSession = Depends(get_session),
    user: CurrentUser = Depends(_solo_artista),
    storage: StorageService = Depends(get_storage_service),
) -> SelloDetalleDTO:
    logo_bytes = await logo.read() if logo is not None and logo.filename else None
    if logo_bytes == b"":
        logo_bytes = None
    return await sello_service.update_sello(
        session,
        storage,
        uuid.UUID(user.id),
        sello_id,
        nombre=nombre,
        descripcion=descripcion,
        website=website,
        logo=logo_bytes,
    )


@router.post(
    "/{sello_id}/invitar",
    response_model=InvitacionOutDTO,
    status_code=status.HTTP_201_CREATED,
)
async def invitar_a_sello(
    sello_id: uuid.UUID,
    body: InvitarBody,
    session: AsyncSession = Depends(get_session),
    user: CurrentUser = Depends(_solo_artista),
) -> InvitacionOutDTO:
    return await sello_service.invitar(
        session, uuid.UUID(user.id), sello_id, body.correo, body.rol
    )


@router.delete(
    "/{sello_id}/miembros/{artista_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def eliminar_miembro(
    sello_id: uuid.UUID,
    artista_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    user: CurrentUser = Depends(_solo_artista),
):
    await sello_service.eliminar_miembro(
        session, uuid.UUID(user.id), sello_id, artista_id
    )


@router.post("", response_model=SelloOutDTO, status_code=status.HTTP_201_CREATED)
async def crear_sello(
    nombre: str = Form(...),
    descripcion: str | None = Form(None),
    website: str | None = Form(None),
    logo: UploadFile | None = File(None),
    session: AsyncSession = Depends(get_session),
    user: CurrentUser = Depends(_solo_artista),
    storage: StorageService = Depends(get_storage_service),
) -> SelloOutDTO:
    logo_bytes = await logo.read() if logo is not None and logo.filename else None
    if logo_bytes == b"":
        logo_bytes = None
    return await sello_service.create_sello(
        session,
        storage,
        uuid.UUID(user.id),
        nombre=nombre,
        descripcion=descripcion,
        website=website,
        logo=logo_bytes,
    )
