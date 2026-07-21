"""Servicio unificado de gestión de medios (canales) del curador.

Consolida la funcionalidad de onboarding y dashboard en un solo servicio:
- CRUD de medios con redes sociales y géneros
- Estadísticas por medio
- Toggle activo/inactivo con protección de campañas activas
- Notificación al admin al crear nuevos canales

Toda operación verifica que el medio pertenezca al curador autenticado.
"""

from __future__ import annotations

import uuid

from sqlalchemy import delete, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.settings import get_settings
from src.models.campana_medios import CampanaMedio
from src.models.curador_medio_redes import CuradorMedioRed
from src.models.curador_medios import CuradorMedio
from src.models.dto.curador_medios import (
    MedioConStatsDTO,
    MedioCreateBody,
    MedioOutDTO,
    MedioRedDTO,
    MedioRedOutDTO,
    MedioStatsDetalleDTO,
    MedioStatsDTO,
    MedioUpdateBody,
    MesStatDTO,
)
from src.models.enums import EstadoCampanaMedio, EstadoSolicitudCurador
from src.models.generos import CuradorMedioCategoria, CuradorMedioGenero, GeneroMusical
from src.models.solicitudes_curador import SolicitudCurador
from src.models.usuarios import Usuario
from src.services import bitacora_service, email_service
from src.services.exceptions import ConflictError, NotFoundError, ValidationError

settings = get_settings()

# Estados que cuentan como "campaña activa" en el medio (bloquean desactivar).
_ESTADOS_ACTIVOS = (EstadoCampanaMedio.pendiente, EstadoCampanaMedio.aceptada)


# ── Helpers ──────────────────────────────────────────────────────


async def ensure_generos(session: AsyncSession, genero_ids: list[int]) -> None:
    """Valida que los géneros existan. Lanza ValidationError si faltan."""
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


async def genero_ids(session: AsyncSession, medio_id: uuid.UUID) -> list[int]:
    """Retorna los IDs de géneros de un medio."""
    return list(
        (await session.scalars(
            select(CuradorMedioGenero.genero_id).where(
                CuradorMedioGenero.medio_id == medio_id
            )
        )).all()
    )


async def categoria_ids(session: AsyncSession, medio_id: uuid.UUID) -> list[int]:
    """Retorna los IDs de categorías de un medio."""
    return list(
        (await session.scalars(
            select(CuradorMedioCategoria.categoria_id).where(
                CuradorMedioCategoria.medio_id == medio_id
            )
        )).all()
    )


async def _stats(session: AsyncSession, medio_id: uuid.UUID) -> MedioStatsDTO:
    """Estadísticas agregadas de un medio."""
    row = (
        await session.execute(
            select(
                func.count().label("recibidas"),
                func.count()
                .filter(CampanaMedio.estado == EstadoCampanaMedio.aceptada)
                .label("aceptadas"),
                func.count()
                .filter(CampanaMedio.estado == EstadoCampanaMedio.entregada)
                .label("entregadas"),
            ).where(CampanaMedio.medio_id == medio_id)
        )
    ).one()
    recibidas, aceptadas, entregadas = row.recibidas, row.aceptadas, row.entregadas
    tasa = round((aceptadas + entregadas) / recibidas, 2) if recibidas else 0.0
    return MedioStatsDTO(
        recibidas=recibidas,
        aceptadas=aceptadas,
        entregadas=entregadas,
        tasa_aceptacion=tasa,
    )


def _to_redes_out(medio: CuradorMedio) -> list[MedioRedOutDTO]:
    """Convierte las redes del medio a DTOs de salida."""
    return [
        MedioRedOutDTO(
            id=str(r.id),
            tipo=r.tipo,
            url=r.url,
            es_principal=r.es_principal,
        )
        for r in (medio.redes or [])
    ]


async def _to_dto(
    session: AsyncSession, medio: CuradorMedio, include_stats: bool = True
) -> MedioOutDTO:
    """Convierte un medio ORM a DTO unificado."""
    stats = await _stats(session, medio.id) if include_stats else None
    return MedioOutDTO(
        id=str(medio.id),
        nombre=medio.nombre,
        tipo=medio.tipo.value if hasattr(medio.tipo, "value") else medio.tipo,
        url=medio.url,
        descripcion=medio.descripcion,
        audiencia_estimada=medio.audiencia_estimada,
        precio_creditos=medio.precio_creditos,
        descripcion_precio=medio.descripcion_precio,
        estado_revision=medio.estado_revision,
        motivo_rechazo=medio.motivo_rechazo,
        activo=medio.activo,
        genero_ids=await genero_ids(session, medio.id),
        categoria_ids=await categoria_ids(session, medio.id),
        redes=_to_redes_out(medio),
        stats=stats,
    )


async def _get_propio(
    session: AsyncSession, medio_id: uuid.UUID, curador_id: uuid.UUID,
    *,
    require_activo: bool = False,
) -> CuradorMedio:
    """Carga un medio del curador. → 404 si no es suyo."""
    medio = await session.get(CuradorMedio, medio_id)
    if medio is None or medio.curador_id != curador_id:
        raise NotFoundError("Medio no encontrado")
    if require_activo and not medio.activo:
        raise NotFoundError("Medio no encontrado")
    return medio


def _encontrar_principal(redes_data: list[MedioRedDTO]) -> MedioRedDTO:
    """Encuentra la red principal o marca la primera como principal."""
    principal = next((r for r in redes_data if r.es_principal), None)
    if principal is None:
        redes_data[0] = redes_data[0].model_copy(update={"es_principal": True})
        principal = redes_data[0]
    return principal


# ── Side effects ─────────────────────────────────────────────────


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


# ── CRUD ─────────────────────────────────────────────────────────


async def crear(
    session: AsyncSession, curador_id: uuid.UUID, body: MedioCreateBody
) -> MedioOutDTO:
    """Crea un medio con redes y géneros. Notifica al admin."""
    await ensure_generos(session, body.genero_ids)

    redes_data = list(body.redes)
    principal = _encontrar_principal(redes_data)

    medio = CuradorMedio(
        curador_id=curador_id,
        nombre=body.nombre,
        tipo=body.tipo,
        url=principal.url,
        descripcion=body.descripcion,
        audiencia_estimada=body.audiencia_estimada,
        precio_creditos=body.precio_creditos,
        descripcion_precio=body.descripcion_precio,
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
            for gid in dict.fromkeys(body.genero_ids)
        ]
    )

    # Crear categorías
    if body.categoria_ids:
        session.add_all(
            [
                CuradorMedioCategoria(medio_id=medio.id, categoria_id=cid)
                for cid in dict.fromkeys(body.categoria_ids)
            ]
        )

    await _on_canal_creado(session, curador_id, medio.id)
    await session.commit()
    await session.refresh(medio, ["redes"])
    return await _to_dto(session, medio)


async def editar(
    session: AsyncSession,
    medio_id: uuid.UUID,
    curador_id: uuid.UUID,
    body: MedioUpdateBody,
) -> MedioOutDTO:
    """Edita un medio (parcial). Reemplaza redes y géneros si se proporcionan."""
    medio = await _get_propio(session, medio_id, curador_id)

    if body.nombre is not None:
        medio.nombre = body.nombre
    if body.descripcion is not None:
        medio.descripcion = body.descripcion or None
    if body.audiencia_estimada is not None:
        medio.audiencia_estimada = body.audiencia_estimada
    if body.precio_creditos is not None:
        medio.precio_creditos = body.precio_creditos
    if body.descripcion_precio is not None:
        medio.descripcion_precio = body.descripcion_precio or None

    # Actualizar géneros si se proporcionan
    if body.genero_ids is not None:
        await ensure_generos(session, body.genero_ids)
        await session.execute(
            CuradorMedioGenero.__table__.delete().where(
                CuradorMedioGenero.medio_id == medio_id
            )
        )
        session.add_all(
            [
                CuradorMedioGenero(medio_id=medio_id, genero_id=gid)
                for gid in dict.fromkeys(body.genero_ids)
            ]
        )

    # Actualizar categorías si se proporcionan
    if body.categoria_ids is not None:
        await session.execute(
            CuradorMedioCategoria.__table__.delete().where(
                CuradorMedioCategoria.medio_id == medio_id
            )
        )
        if body.categoria_ids:
            session.add_all(
                [
                    CuradorMedioCategoria(medio_id=medio_id, categoria_id=cid)
                    for cid in dict.fromkeys(body.categoria_ids)
                ]
            )

    # Actualizar redes si se proporcionan (reemplazo destructivo)
    if body.redes is not None:
        redes_data = list(body.redes)
        principal = _encontrar_principal(redes_data)
        medio.url = principal.url

        await session.execute(
            CuradorMedioRed.__table__.delete().where(
                CuradorMedioRed.medio_id == medio_id
            )
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
    return await _to_dto(session, medio)


async def delete_medio(
    session: AsyncSession, medio_id: uuid.UUID, curador_id: uuid.UUID
) -> None:
    """Borrado lógico de un medio."""
    medio = await _get_propio(session, medio_id, curador_id, require_activo=True)
    medio.activo = False
    await session.commit()


async def toggle_activo(
    session: AsyncSession, medio_id: uuid.UUID, curador_id: uuid.UUID
) -> MedioOutDTO:
    """Activa/desactiva un medio. Bloquea si hay campañas activas."""
    medio = await _get_propio(session, medio_id, curador_id)

    if medio.activo:
        activas = await session.scalar(
            select(func.count())
            .select_from(CampanaMedio)
            .where(
                CampanaMedio.medio_id == medio_id,
                CampanaMedio.estado.in_(_ESTADOS_ACTIVOS),
            )
        )
        if activas:
            raise ConflictError("Tienes campañas activas en este medio")

    medio.activo = not medio.activo
    await session.commit()
    return await _to_dto(session, medio)


# ── Listados ─────────────────────────────────────────────────────


async def list_medios(
    session: AsyncSession, curador_id: uuid.UUID
) -> list[MedioOutDTO]:
    """Lista medios activos del curador (con stats)."""
    medios = (
        await session.scalars(
            select(CuradorMedio)
            .where(CuradorMedio.curador_id == curador_id, CuradorMedio.activo.is_(True))
            .order_by(CuradorMedio.created_at)
        )
    ).all()
    return [await _to_dto(session, m) for m in medios]


async def list_con_stats(
    session: AsyncSession, curador_id: uuid.UUID
) -> list[MedioOutDTO]:
    """Lista todos los medios del curador (activos e inactivos, con stats)."""
    medios = (
        await session.scalars(
            select(CuradorMedio)
            .where(CuradorMedio.curador_id == curador_id)
            .order_by(CuradorMedio.created_at)
        )
    ).all()
    return [await _to_dto(session, m) for m in medios]


async def stats_detalladas(
    session: AsyncSession, medio_id: uuid.UUID, curador_id: uuid.UUID
) -> MedioStatsDetalleDTO:
    """Estadísticas detalladas de un medio con desglose mensual."""
    await _get_propio(session, medio_id, curador_id)
    base = await _stats(session, medio_id)

    mes_col = func.to_char(
        func.date_trunc("month", CampanaMedio.created_at), "YYYY-MM"
    )
    filas = (
        await session.execute(
            select(mes_col.label("mes"), func.count().label("n"))
            .where(
                CampanaMedio.medio_id == medio_id,
                CampanaMedio.created_at >= text("now() - interval '6 months'"),
            )
            .group_by(mes_col)
            .order_by(mes_col)
        )
    ).all()

    return MedioStatsDetalleDTO(
        recibidas=base.recibidas,
        aceptadas=base.aceptadas,
        entregadas=base.entregadas,
        tasa_aceptacion=base.tasa_aceptacion,
        por_mes=[MesStatDTO(mes=mes, recibidas=n) for mes, n in filas],
    )
