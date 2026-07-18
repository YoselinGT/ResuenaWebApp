"""Servicio CRUD de medios (canales) del curador.

Cada medio tiene géneros especializados en `curador_medio_generos`. El borrado
es lógico (`activo=False`). Toda operación verifica que el medio pertenezca al
curador autenticado (autorización a nivel de recurso).
"""

from __future__ import annotations

import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.settings import get_settings
from src.models.curador_medio_redes import CuradorMedioRed
from src.models.curador_medios import CuradorMedio
from src.models.dto.onboarding import (
    CuradorMedioDTO,
    CuradorMedioOutDTO,
    CuradorMedioRedOutDTO,
)
from src.models.enums import EstadoSolicitudCurador
from src.models.generos import CuradorMedioGenero, GeneroMusical
from src.models.solicitudes_curador import SolicitudCurador
from src.models.usuarios import Usuario
from src.services import bitacora_service, email_service
from src.services.exceptions import NotFoundError, ValidationError

settings = get_settings()


async def _ensure_generos(session: AsyncSession, genero_ids: list[int]) -> None:
    if not genero_ids:
        return
    encontrados = set(
        (await session.scalars(
            select(GeneroMusical.id).where(GeneroMusical.id.in_(set(genero_ids)))
        )).all()
    )
    faltantes = set(genero_ids) - encontrados
    if faltantes:
        raise ValidationError(f"Géneros inexistentes: {sorted(faltantes)}")


async def _genero_ids(session: AsyncSession, medio_id: uuid.UUID) -> list[int]:
    return list(
        (await session.scalars(
            select(CuradorMedioGenero.genero_id).where(
                CuradorMedioGenero.medio_id == medio_id
            )
        )).all()
    )


def _to_out(medio: CuradorMedio, genero_ids: list[int]) -> CuradorMedioOutDTO:
    redes_out = [
        CuradorMedioRedOutDTO(
            id=str(r.id),
            tipo=r.tipo,
            url=r.url,
            es_principal=r.es_principal,
        )
        for r in (medio.redes or [])
    ]
    return CuradorMedioOutDTO(
        id=str(medio.id),
        nombre=medio.nombre,
        tipo=medio.tipo.value if hasattr(medio.tipo, "value") else medio.tipo,
        url=medio.url,
        descripcion=medio.descripcion,
        audiencia_estimada=medio.audiencia_estimada,
        precio_creditos=medio.precio_creditos,
        descripcion_precio=medio.descripcion_precio,
        genero_ids=genero_ids,
        redes=redes_out,
    )


async def _get_propio(
    session: AsyncSession, medio_id: uuid.UUID, curador_id: uuid.UUID
) -> CuradorMedio:
    medio = await session.get(CuradorMedio, medio_id)
    if medio is None or medio.curador_id != curador_id or not medio.activo:
        raise NotFoundError("Medio no encontrado")
    return medio


async def _on_canal_creado(
    session: AsyncSession, curador_id: uuid.UUID, medio_id: uuid.UUID
) -> None:
    """Notifica al admin que hay un canal nuevo para revisar.

    Crea solicitud si no existe (idempotente). Siempre envía notificación
    porque cada canal necesita revisión independiente del admin.
    """
    existe = await session.scalar(
        select(SolicitudCurador).where(
            SolicitudCurador.usuario_id == curador_id
        )
    )
    if not existe:
        solicitud = SolicitudCurador(
            usuario_id=curador_id,
            estado=EstadoSolicitudCurador.pendiente,
        )
        session.add(solicitud)
        await session.flush()

    usuario = await session.get(Usuario, curador_id)
    if usuario:
        await email_service.send_admin_nueva_solicitud(
            settings.admin_email,
            usuario.nombre_completo,
            usuario.correo,
            "curador",
        )
    await bitacora_service.registrar(
        session,
        accion="canal_creado_pendiente_revision",
        entidad="curador_medios",
        entidad_id=str(medio_id),
        autor_id=curador_id,
    )


async def add_medio(
    session: AsyncSession, curador_id: uuid.UUID, dto: CuradorMedioDTO
) -> CuradorMedioOutDTO:
    await _ensure_generos(session, dto.genero_ids)

    # Encontrar la URL principal (red con es_principal=true, o la primera)
    redes_data = list(dto.redes)
    principal = next((r for r in redes_data if r.es_principal), redes_data[0])
    # Si ninguna tiene es_principal, marcar la primera
    if not any(r.es_principal for r in redes_data):
        redes_data[0] = redes_data[0].model_copy(update={"es_principal": True})

    medio = CuradorMedio(
        curador_id=curador_id,
        nombre=dto.nombre,
        tipo=dto.tipo,
        url=principal.url,
        descripcion=dto.descripcion,
        audiencia_estimada=dto.audiencia_estimada,
        precio_creditos=dto.precio_creditos,
        descripcion_precio=dto.descripcion_precio,
    )
    session.add(medio)
    await session.flush()

    # Crear redes
    session.add_all(
        [
            CuradorMedioRed(
                medio_id=medio.id,
                tipo=r.tipo.value if hasattr(r.tipo, "value") else r.tipo,
                url=r.url,
                es_principal=r.es_principal,
            )
            for r in redes_data
        ]
    )

    # Crear géneros
    session.add_all(
        [
            CuradorMedioGenero(medio_id=medio.id, genero_id=gid)
            for gid in dict.fromkeys(dto.genero_ids)
        ]
    )
    await _on_canal_creado(session, curador_id, medio.id)
    await session.commit()
    await session.refresh(medio, ["redes"])
    return _to_out(medio, list(dict.fromkeys(dto.genero_ids)))


async def update_medio(
    session: AsyncSession,
    medio_id: uuid.UUID,
    curador_id: uuid.UUID,
    dto: CuradorMedioDTO,
) -> CuradorMedioOutDTO:
    medio = await _get_propio(session, medio_id, curador_id)
    await _ensure_generos(session, dto.genero_ids)

    # Encontrar la URL principal
    redes_data = list(dto.redes)
    principal = next((r for r in redes_data if r.es_principal), redes_data[0])
    if not any(r.es_principal for r in redes_data):
        redes_data[0] = redes_data[0].model_copy(update={"es_principal": True})

    medio.nombre = dto.nombre
    medio.tipo = dto.tipo
    medio.url = principal.url
    medio.descripcion = dto.descripcion
    medio.audiencia_estimada = dto.audiencia_estimada
    medio.precio_creditos = dto.precio_creditos
    medio.descripcion_precio = dto.descripcion_precio

    # Reemplazar géneros (destructivo)
    await session.execute(
        delete(CuradorMedioGenero).where(CuradorMedioGenero.medio_id == medio_id)
    )
    session.add_all(
        [
            CuradorMedioGenero(medio_id=medio_id, genero_id=gid)
            for gid in dict.fromkeys(dto.genero_ids)
        ]
    )

    # Reemplazar redes (destructivo)
    await session.execute(
        delete(CuradorMedioRed).where(CuradorMedioRed.medio_id == medio_id)
    )
    session.add_all(
        [
            CuradorMedioRed(
                medio_id=medio_id,
                tipo=r.tipo.value if hasattr(r.tipo, "value") else r.tipo,
                url=r.url,
                es_principal=r.es_principal,
            )
            for r in redes_data
        ]
    )

    await session.commit()
    await session.refresh(medio, ["redes"])
    return _to_out(medio, list(dict.fromkeys(dto.genero_ids)))


async def delete_medio(
    session: AsyncSession, medio_id: uuid.UUID, curador_id: uuid.UUID
) -> None:
    medio = await _get_propio(session, medio_id, curador_id)
    medio.activo = False
    await session.commit()


async def list_medios(
    session: AsyncSession, curador_id: uuid.UUID
) -> list[CuradorMedioOutDTO]:
    medios = (
        await session.scalars(
            select(CuradorMedio)
            .where(CuradorMedio.curador_id == curador_id, CuradorMedio.activo.is_(True))
            .order_by(CuradorMedio.created_at)
        )
    ).all()
    return [_to_out(m, await _genero_ids(session, m.id)) for m in medios]
