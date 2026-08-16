"""Servicio de campañas musicales.

CRUD de campañas, gestión de medios vinculados, uploads a S3 y
flujo de envío con retención de créditos.
"""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.campana_medios import CampanaMedio
from src.models.campanas import Campana
from src.models.curador_medios import CuradorMedio
from src.models.enums import EstadoCampana, EstadoCampanaMedio
from src.models.generos import GeneroMusical
from src.models.usuarios import Usuario
from src.services.exceptions import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
    ValidationError,
)


# ── Helpers ──────────────────────────────────────────────────────


async def _get_campana(session: AsyncSession, campana_id: uuid.UUID) -> Campana:
    """Obtiene una campaña o lanza NotFoundError."""
    campana = await session.get(Campana, campana_id)
    if campana is None:
        raise NotFoundError("Campaña no encontrada")
    return campana


async def _ensure_owner(campana: Campana, artista_id: uuid.UUID) -> None:
    """Valida que el artista es dueño de la campaña."""
    if campana.artista_id != artista_id:
        raise ForbiddenError("No eres el dueño de esta campaña")


async def _ensure_borrador(campana: Campana) -> None:
    """Valida que la campaña está en estado borrador."""
    if campana.estado != EstadoCampana.borrador:
        raise ConflictError(
            "Solo se pueden editar campañas en estado borrador"
        )


async def _ensure_genero(session: AsyncSession, genero_id: int) -> None:
    """Valida que el género existe y está activo."""
    genero = await session.get(GeneroMusical, genero_id)
    if genero is None or not genero.activo:
        raise ValidationError("Género no válido o inactivo")


# ── CRUD Campañas ────────────────────────────────────────────────


async def create_campana(
    session: AsyncSession,
    artista_id: uuid.UUID,
    titulo: str,
    genero_id: int,
    descripcion: str | None = None,
    sello_id: uuid.UUID | None = None,
) -> Campana:
    """Crea una nueva campaña en estado borrador."""
    await _ensure_genero(session, genero_id)

    campana = Campana(
        artista_id=artista_id,
        sello_id=sello_id,
        titulo=titulo.strip(),
        descripcion=descripcion,
        genero_id=genero_id,
        estado=EstadoCampana.borrador,
        creditos_usados=0,
    )
    session.add(campana)
    await session.flush()
    return campana


async def update_campana(
    session: AsyncSession,
    campana_id: uuid.UUID,
    artista_id: uuid.UUID,
    titulo: str | None = None,
    descripcion: str | None = None,
    genero_id: int | None = None,
) -> Campana:
    """Actualiza campos de una campaña en borrador."""
    campana = await _get_campana(session, campana_id)
    await _ensure_owner(campana, artista_id)
    await _ensure_borrador(campana)

    if titulo is not None:
        campana.titulo = titulo.strip()
    if descripcion is not None:
        campana.descripcion = descripcion
    if genero_id is not None:
        await _ensure_genero(session, genero_id)
        campana.genero_id = genero_id

    await session.flush()
    return campana


async def get_campana(
    session: AsyncSession,
    campana_id: uuid.UUID,
    artista_id: uuid.UUID,
) -> Campana:
    """Obtiene el detalle de una campaña con sus medios."""
    campana = await _get_campana(session, campana_id)
    await _ensure_owner(campana, artista_id)

    # Cargar medios relacionados
    result = await session.execute(
        select(CampanaMedio).where(CampanaMedio.campana_id == campana_id)
    )
    campana.medios = list(result.scalars().all())
    return campana


async def list_campanas(
    session: AsyncSession,
    artista_id: uuid.UUID,
    estado: EstadoCampana | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Campana], int]:
    """Lista campañas del artista con filtro por estado."""
    query = select(Campana).where(Campana.artista_id == artista_id)

    if estado is not None:
        query = query.where(Campana.estado == estado)

    # Contar total
    count_query = select(func.count()).select_from(query.subquery())
    total = await session.scalar(count_query) or 0

    # Paginar
    query = query.order_by(Campana.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await session.execute(query)
    campanas = list(result.scalars().all())
    return campanas, total


async def delete_campana(
    session: AsyncSession,
    campana_id: uuid.UUID,
    artista_id: uuid.UUID,
) -> None:
    """Elimina una campaña en borrador y sus archivos S3."""
    campana = await _get_campana(session, campana_id)
    await _ensure_owner(campana, artista_id)
    await _ensure_borrador(campana)

    # Eliminar archivos S3 si existen
    from src.infra.storage import get_storage_service

    storage = get_storage_service()

    if campana.url_audio:
        await storage.delete(campana.url_audio)
    if campana.url_imagen:
        await storage.delete(campana.url_imagen)
    if campana.url_material:
        await storage.delete(campana.url_material)

    # Eliminar medios vinculados primero
    await session.execute(
        CampanaMedio.__table__.delete().where(CampanaMedio.campana_id == campana_id)
    )

    # Eliminar campaña
    await session.delete(campana)
    await session.flush()


# ── Medios vinculados ────────────────────────────────────────────


async def add_medios_to_campana(
    session: AsyncSession,
    campana_id: uuid.UUID,
    artista_id: uuid.UUID,
    profesional_ids: list[str],
) -> list[CampanaMedio]:
    """Vincula curadores a una campaña."""
    campana = await _get_campana(session, campana_id)
    await _ensure_owner(campana, artista_id)
    await _ensure_borrador(campana)

    medios_creados = []
    for prof_id_str in profesional_ids:
        prof_id = uuid.UUID(prof_id_str)

        # Verificar que el curador existe y tiene al menos un canal aprobado
        canal = await session.scalar(
            select(CuradorMedio).where(
                CuradorMedio.curador_id == prof_id,
                CuradorMedio.estado_revision == "aprobado",
                CuradorMedio.activo.is_(True),
            )
        )
        if canal is None:
            raise ValidationError(
                f"Curador {prof_id_str} no tiene canales aprobados"
            )

        # Verificar que no esté ya vinculado
        existing = await session.scalar(
            select(CampanaMedio).where(
                CampanaMedio.campana_id == campana_id,
                CuradorMedio.curador_id == prof_id,
            )
        )
        if existing is not None:
            continue  # Skip si ya está vinculado

        medio = CampanaMedio(
            campana_id=campana_id,
            medio_id=canal.id,
            curador_id=prof_id,
            estado=EstadoCampanaMedio.pendiente,
            precio_snapshot=canal.precio_creditos,
        )
        session.add(medio)
        medios_creados.append(medio)

    await session.flush()
    return medios_creados


# ── Envío ────────────────────────────────────────────────────────


async def enviar_campana(
    session: AsyncSession,
    campana_id: uuid.UUID,
    artista_id: uuid.UUID,
) -> dict:
    """Envía una campaña o retorna info de créditos faltantes.

    Retorna:
        - {"status": "enviada", "campana": ...} si tiene créditos suficientes
        - {"status": "sin_creditos", "creditos_faltantes": N} si no tiene créditos
    """
    from src.services.wallet_service import deduct_credits, get_balance

    campana = await _get_campana(session, campana_id)
    await _ensure_owner(campana, artista_id)
    await _ensure_borrador(campana)

    # Validar que tiene audio
    if not campana.url_audio:
        raise ValidationError("La campaña debe tener un audio cargado")

    # Validar que tiene imagen
    if not campana.url_imagen:
        raise ValidationError("La campaña debe tener una imagen de portada")

    # Validar que tiene al menos un medio vinculado
    medios = (
        await session.scalars(
            select(CampanaMedio).where(CampanaMedio.campana_id == campana_id)
        )
    ).all()
    if not medios:
        raise ValidationError("Debes seleccionar al menos un curador")

    # Calcular créditos necesarios
    creditos_necesarios = sum(m.precio_snapshot for m in medios)

    # Verificar saldo
    wallet = await get_balance(session, artista_id)
    creditos_disponibles = wallet.saldo_creditos

    if creditos_disponibles < creditos_necesarios:
        return {
            "status": "sin_creditos",
            "creditos_necesarios": creditos_necesarios,
            "creditos_disponibles": creditos_disponibles,
            "creditos_faltantes": creditos_necesarios - creditos_disponibles,
        }

    # Descontar créditos
    await deduct_credits(
        session,
        usuario_id=artista_id,
        monto=creditos_necesarios,
        descripcion=f"Envío de campaña: {campana.titulo}",
        campana_id=campana_id,
    )

    # Actualizar medios
    for medio in medios:
        medio.creditos_retenidos = medio.precio_snapshot
        medio.estado = EstadoCampanaMedio.pendiente

    # Actualizar campaña
    campana.estado = EstadoCampana.enviada
    campana.creditos_usados = creditos_necesarios
    await session.flush()

    return {
        "status": "enviada",
        "campana": campana,
    }
