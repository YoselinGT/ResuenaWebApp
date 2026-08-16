"""Router de campañas musicales (`/campanas`).

Endpoints para que artistas creen, editen y gestionen sus campañas.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, File, Query, Response, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.infra.db import get_session
from src.middleware.auth import CurrentUser
from src.middleware.roles import require_artista
from src.models.dto.campanas import (
    CampanaCreateBody,
    CampanaListResponse,
    CampanaResponse,
    CampanaUpdateBody,
    CuradorSelectBody,
)
from src.models.enums import EstadoCampana
from src.services import campana_service

router = APIRouter(prefix="/campanas", tags=["campanas"])


# ── POST /campanas ──────────────────────────────────────────────


@router.post("", response_model=CampanaResponse, status_code=status.HTTP_201_CREATED)
async def create_campana(
    body: CampanaCreateBody,
    session: AsyncSession = Depends(get_session),
    user: CurrentUser = Depends(require_artista),
) -> CampanaResponse:
    """Crea una nueva campaña en estado borrador."""
    campana = await campana_service.create_campana(
        session=session,
        artista_id=uuid.UUID(user.id),
        titulo=body.titulo,
        genero_id=body.genero_id,
        descripcion=body.descripcion,
    )
    await session.commit()
    return CampanaResponse(
        id=str(campana.id),
        artista_id=str(campana.artista_id),
        sello_id=str(campana.sello_id) if campana.sello_id else None,
        titulo=campana.titulo,
        descripcion=campana.descripcion,
        url_audio=campana.url_audio,
        url_imagen=campana.url_imagen,
        url_material=campana.url_material,
        genero_id=campana.genero_id,
        estado=campana.estado.value,
        creditos_usados=campana.creditos_usados,
        created_at=campana.created_at,
        updated_at=campana.updated_at,
    )


# ── PATCH /campanas/:id ─────────────────────────────────────────


@router.patch("/{campana_id}", response_model=CampanaResponse)
async def update_campana(
    campana_id: uuid.UUID,
    body: CampanaUpdateBody,
    session: AsyncSession = Depends(get_session),
    user: CurrentUser = Depends(require_artista),
) -> CampanaResponse:
    """Actualiza campos de una campaña en borrador."""
    campana = await campana_service.update_campana(
        session=session,
        campana_id=campana_id,
        artista_id=uuid.UUID(user.id),
        titulo=body.titulo,
        descripcion=body.descripcion,
        genero_id=body.genero_id,
    )
    await session.commit()
    return CampanaResponse(
        id=str(campana.id),
        artista_id=str(campana.artista_id),
        sello_id=str(campana.sello_id) if campana.sello_id else None,
        titulo=campana.titulo,
        descripcion=campana.descripcion,
        url_audio=campana.url_audio,
        url_imagen=campana.url_imagen,
        url_material=campana.url_material,
        genero_id=campana.genero_id,
        estado=campana.estado.value,
        creditos_usados=campana.creditos_usados,
        created_at=campana.created_at,
        updated_at=campana.updated_at,
    )


# ── GET /campanas ───────────────────────────────────────────────


@router.get("", response_model=dict)
async def list_campanas(
    estado: EstadoCampana | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
    user: CurrentUser = Depends(require_artista),
) -> dict:
    """Lista campañas del artista con filtro por estado."""
    campanas, total = await campana_service.list_campanas(
        session=session,
        artista_id=uuid.UUID(user.id),
        estado=estado,
        page=page,
        page_size=page_size,
    )
    return {
        "items": [
            CampanaListResponse(
                id=str(c.id),
                titulo=c.titulo,
                estado=c.estado.value,
                genero_id=c.genero_id,
                creditos_usados=c.creditos_usados,
                url_imagen=c.url_imagen,
                created_at=c.created_at,
                updated_at=c.updated_at,
            )
            for c in campanas
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


# ── GET /campanas/:id ───────────────────────────────────────────


@router.get("/{campana_id}", response_model=CampanaResponse)
async def get_campana(
    campana_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    user: CurrentUser = Depends(require_artista),
) -> CampanaResponse:
    """Obtiene el detalle de una campaña con sus medios."""
    from src.models.dto.campanas import CampanaMedioResponse

    campana = await campana_service.get_campana(
        session=session,
        campana_id=campana_id,
        artista_id=uuid.UUID(user.id),
    )
    return CampanaResponse(
        id=str(campana.id),
        artista_id=str(campana.artista_id),
        sello_id=str(campana.sello_id) if campana.sello_id else None,
        titulo=campana.titulo,
        descripcion=campana.descripcion,
        url_audio=campana.url_audio,
        url_imagen=campana.url_imagen,
        url_material=campana.url_material,
        genero_id=campana.genero_id,
        estado=campana.estado.value,
        creditos_usados=campana.creditos_usados,
        created_at=campana.created_at,
        updated_at=campana.updated_at,
        medios=[
            CampanaMedioResponse(
                id=str(m.id),
                medio_id=str(m.medio_id),
                curador_id=str(m.curador_id),
                estado=m.estado.value,
                precio_snapshot=m.precio_snapshot,
                creditos_retenidos=m.creditos_retenidos,
                fecha_limite=m.fecha_limite,
            )
            for m in campana.medios
        ],
    )


# ── DELETE /campanas/:id ────────────────────────────────────────


@router.delete("/{campana_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def delete_campana(
    campana_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    user: CurrentUser = Depends(require_artista),
):
    """Elimina una campaña en borrador."""
    await campana_service.delete_campana(
        session=session,
        campana_id=campana_id,
        artista_id=uuid.UUID(user.id),
    )
    await session.commit()


# ── POST /campanas/:id/curadores ────────────────────────────────


@router.post("/{campana_id}/curadores", response_model=CampanaResponse)
async def add_curadores(
    campana_id: uuid.UUID,
    body: CuradorSelectBody,
    session: AsyncSession = Depends(get_session),
    user: CurrentUser = Depends(require_artista),
) -> CampanaResponse:
    """Vincula curadores a una campaña."""
    await campana_service.add_medios_to_campana(
        session=session,
        campana_id=campana_id,
        artista_id=uuid.UUID(user.id),
        profesional_ids=body.profesional_ids,
    )
    await session.commit()

    # Recargar campaña con medios actualizados
    from src.models.dto.campanas import CampanaMedioResponse

    campana = await campana_service.get_campana(
        session=session,
        campana_id=campana_id,
        artista_id=uuid.UUID(user.id),
    )
    return CampanaResponse(
        id=str(campana.id),
        artista_id=str(campana.artista_id),
        sello_id=str(campana.sello_id) if campana.sello_id else None,
        titulo=campana.titulo,
        descripcion=campana.descripcion,
        url_audio=campana.url_audio,
        url_imagen=campana.url_imagen,
        url_material=campana.url_material,
        genero_id=campana.genero_id,
        estado=campana.estado.value,
        creditos_usados=campana.creditos_usados,
        created_at=campana.created_at,
        updated_at=campana.updated_at,
        medios=[
            CampanaMedioResponse(
                id=str(m.id),
                medio_id=str(m.medio_id),
                curador_id=str(m.curador_id),
                estado=m.estado.value,
                precio_snapshot=m.precio_snapshot,
                creditos_retenidos=m.creditos_retenidos,
                fecha_limite=m.fecha_limite,
            )
            for m in campana.medios
        ],
    )


# ── POST /campanas/:id/enviar ───────────────────────────────────


@router.post("/{campana_id}/enviar", response_model=dict)
async def enviar_campana(
    campana_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    user: CurrentUser = Depends(require_artista),
) -> dict:
    """Envía una campaña o retorna info de créditos faltantes."""
    result = await campana_service.enviar_campana(
        session=session,
        campana_id=campana_id,
        artista_id=uuid.UUID(user.id),
    )
    await session.commit()

    if result["status"] == "sin_creditos":
        return {
            "status": "sin_creditos",
            "creditos_necesarios": result["creditos_necesarios"],
            "creditos_disponibles": result["creditos_disponibles"],
            "creditos_faltantes": result["creditos_faltantes"],
        }

    campana = result["campana"]
    from src.models.dto.campanas import CampanaMedioResponse

    return {
        "status": "enviada",
        "campana": CampanaResponse(
            id=str(campana.id),
            artista_id=str(campana.artista_id),
            sello_id=str(campana.sello_id) if campana.sello_id else None,
            titulo=campana.titulo,
            descripcion=campana.descripcion,
            url_audio=campana.url_audio,
            url_imagen=campana.url_imagen,
            url_material=campana.url_material,
            genero_id=campana.genero_id,
            estado=campana.estado.value,
            creditos_usados=campana.creditos_usados,
            created_at=campana.created_at,
            updated_at=campana.updated_at,
        ),
    }


# ── Uploads ─────────────────────────────────────────────────────


@router.post("/{campana_id}/upload/audio", response_model=CampanaResponse)
async def upload_audio(
    campana_id: uuid.UUID,
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
    user: CurrentUser = Depends(require_artista),
) -> CampanaResponse:
    """Sube audio de campaña (MP3/WAV, máx 50MB)."""
    from src.services.campana_upload_service import upload_audio

    campana = await campana_service._get_campana(session, campana_id)
    await campana_service._ensure_owner(campana, uuid.UUID(user.id))
    await campana_service._ensure_borrador(campana)

    key = await upload_audio(campana_id, file)
    campana.url_audio = key
    await session.commit()

    return CampanaResponse(
        id=str(campana.id),
        artista_id=str(campana.artista_id),
        sello_id=str(campana.sello_id) if campana.sello_id else None,
        titulo=campana.titulo,
        descripcion=campana.descripcion,
        url_audio=campana.url_audio,
        url_imagen=campana.url_imagen,
        url_material=campana.url_material,
        genero_id=campana.genero_id,
        estado=campana.estado.value,
        creditos_usados=campana.creditos_usados,
        created_at=campana.created_at,
        updated_at=campana.updated_at,
    )


@router.post("/{campana_id}/upload/imagen", response_model=CampanaResponse)
async def upload_imagen(
    campana_id: uuid.UUID,
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
    user: CurrentUser = Depends(require_artista),
) -> CampanaResponse:
    """Sube imagen de portada (JPG/PNG, máx 5MB, redimensionada a 800x800)."""
    from src.services.campana_upload_service import upload_imagen

    campana = await campana_service._get_campana(session, campana_id)
    await campana_service._ensure_owner(campana, uuid.UUID(user.id))
    await campana_service._ensure_borrador(campana)

    key = await upload_imagen(campana_id, file)
    campana.url_imagen = key
    await session.commit()

    return CampanaResponse(
        id=str(campana.id),
        artista_id=str(campana.artista_id),
        sello_id=str(campana.sello_id) if campana.sello_id else None,
        titulo=campana.titulo,
        descripcion=campana.descripcion,
        url_audio=campana.url_audio,
        url_imagen=campana.url_imagen,
        url_material=campana.url_material,
        genero_id=campana.genero_id,
        estado=campana.estado.value,
        creditos_usados=campana.creditos_usados,
        created_at=campana.created_at,
        updated_at=campana.updated_at,
    )


@router.post("/{campana_id}/upload/material", response_model=CampanaResponse)
async def upload_material(
    campana_id: uuid.UUID,
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
    user: CurrentUser = Depends(require_artista),
) -> CampanaResponse:
    """Sube material adicional (ZIP, máx 100MB)."""
    from src.services.campana_upload_service import upload_material

    campana = await campana_service._get_campana(session, campana_id)
    await campana_service._ensure_owner(campana, uuid.UUID(user.id))
    await campana_service._ensure_borrador(campana)

    key = await upload_material(campana_id, file)
    campana.url_material = key
    await session.commit()

    return CampanaResponse(
        id=str(campana.id),
        artista_id=str(campana.artista_id),
        sello_id=str(campana.sello_id) if campana.sello_id else None,
        titulo=campana.titulo,
        descripcion=campana.descripcion,
        url_audio=campana.url_audio,
        url_imagen=campana.url_imagen,
        url_material=campana.url_material,
        genero_id=campana.genero_id,
        estado=campana.estado.value,
        creditos_usados=campana.creditos_usados,
        created_at=campana.created_at,
        updated_at=campana.updated_at,
    )
