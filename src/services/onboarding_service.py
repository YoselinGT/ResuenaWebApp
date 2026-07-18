"""Servicio de onboarding: progreso y guardado idempotente de cada paso.

Cada `save_*` reemplaza el conjunto previo del usuario (upsert por set). Se valida
la existencia de FKs (géneros, idiomas, regiones) y se lanza `ValidationError`
(→ 422) en vez de dejar que la BD lance IntegrityError (→ 500).
"""

from __future__ import annotations

import uuid

from sqlalchemy import delete, exists, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.catalogos import Idioma, Region
from src.models.curador_medios import CuradorMedio
from src.models.dto.onboarding import OnboardingProgressDTO, RedSocialDTO
from src.models.enums import TipoLanzamientos, TipoPreferenciaGenero
from src.models.generos import GeneroMusical, UsuarioGenero
from src.models.usuario_preferencias import (
    UsuarioPreferenciaIdioma,
    UsuarioPreferenciaRegion,
    UsuarioPreferencias,
)
from src.models.usuario_redes import UsuarioRed
from src.services.exceptions import ValidationError


async def _ensure_generos_existen(session: AsyncSession, genero_ids: list[int]) -> None:
    ids = set(genero_ids)
    encontrados = set(
        (await session.scalars(
            select(GeneroMusical.id).where(GeneroMusical.id.in_(ids))
        )).all()
    )
    faltantes = ids - encontrados
    if faltantes:
        raise ValidationError(f"Géneros inexistentes: {sorted(faltantes)}")


async def save_generos(
    session: AsyncSession,
    usuario_id: uuid.UUID,
    genero_ids: list[int],
    tipo: TipoPreferenciaGenero = TipoPreferenciaGenero.preferido,
) -> None:
    await _ensure_generos_existen(session, genero_ids)
    await session.execute(
        delete(UsuarioGenero).where(
            UsuarioGenero.usuario_id == usuario_id, UsuarioGenero.tipo == tipo
        )
    )
    session.add_all(
        [
            UsuarioGenero(usuario_id=usuario_id, genero_id=gid, tipo=tipo)
            for gid in dict.fromkeys(genero_ids)
        ]
    )
    await session.commit()


async def save_idiomas(
    session: AsyncSession, usuario_id: uuid.UUID, codigos: list[str]
) -> None:
    codigos = [c.lower() for c in codigos]
    validos = set(
        (await session.scalars(select(Idioma.codigo).where(Idioma.codigo.in_(codigos)))).all()
    )
    faltantes = set(codigos) - validos
    if faltantes:
        raise ValidationError(f"Idiomas inexistentes: {sorted(faltantes)}")
    await session.execute(
        delete(UsuarioPreferenciaIdioma).where(
            UsuarioPreferenciaIdioma.usuario_id == usuario_id
        )
    )
    session.add_all(
        [
            UsuarioPreferenciaIdioma(usuario_id=usuario_id, idioma_codigo=c)
            for c in dict.fromkeys(codigos)
        ]
    )
    await session.commit()


async def save_regiones(
    session: AsyncSession, usuario_id: uuid.UUID, codigos: list[str]
) -> None:
    codigos = [c.upper() for c in codigos]
    validos = set(
        (await session.scalars(select(Region.codigo).where(Region.codigo.in_(codigos)))).all()
    )
    faltantes = set(codigos) - validos
    if faltantes:
        raise ValidationError(f"Regiones inexistentes: {sorted(faltantes)}")
    await session.execute(
        delete(UsuarioPreferenciaRegion).where(
            UsuarioPreferenciaRegion.usuario_id == usuario_id
        )
    )
    session.add_all(
        [
            UsuarioPreferenciaRegion(usuario_id=usuario_id, region_codigo=c)
            for c in dict.fromkeys(codigos)
        ]
    )
    await session.commit()


async def save_redes(
    session: AsyncSession, usuario_id: uuid.UUID, redes: list[RedSocialDTO]
) -> None:
    await session.execute(
        delete(UsuarioRed).where(UsuarioRed.usuario_id == usuario_id)
    )
    session.add_all(
        [UsuarioRed(usuario_id=usuario_id, tipo=r.tipo, url=r.url) for r in redes]
    )
    await session.commit()


async def save_preferencias(
    session: AsyncSession,
    usuario_id: uuid.UUID,
    apertura_musical: int,
    acepta_todos_idiomas: bool,
    tipo_lanzamientos: TipoLanzamientos | None,
) -> None:
    pref = await session.get(UsuarioPreferencias, usuario_id)
    if pref is None:
        pref = UsuarioPreferencias(usuario_id=usuario_id)
        session.add(pref)
    pref.apertura_musical = apertura_musical
    pref.acepta_todos_idiomas = acepta_todos_idiomas
    pref.tipo_lanzamientos = tipo_lanzamientos
    await session.commit()


async def get_progreso(
    session: AsyncSession, usuario_id: uuid.UUID, tipo_usuario: str = "artista"
) -> OnboardingProgressDTO:
    async def _hay(condicion) -> bool:
        return bool(await session.scalar(select(exists().where(condicion))))

    # Para curadores, el paso "redes" no cuenta — sus redes son de sus canales
    redes_ok = False
    if tipo_usuario != "curador":
        redes_ok = await _hay(UsuarioRed.usuario_id == usuario_id)

    # Contar medios activos del curador
    medios_count = 0
    if tipo_usuario == "curador":
        medios_count = await session.scalar(
            select(func.count())
            .select_from(CuradorMedio)
            .where(
                CuradorMedio.curador_id == usuario_id,
                CuradorMedio.activo.is_(True),
            )
        ) or 0

    return OnboardingProgressDTO(
        generos=await _hay(UsuarioGenero.usuario_id == usuario_id),
        idiomas=await _hay(UsuarioPreferenciaIdioma.usuario_id == usuario_id),
        regiones=await _hay(UsuarioPreferenciaRegion.usuario_id == usuario_id),
        redes=redes_ok,
        medios=medios_count > 0,
        preferencias=await _hay(UsuarioPreferencias.usuario_id == usuario_id),
        medios_count=medios_count,
    )
