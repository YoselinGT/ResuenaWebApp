"""Servicio de géneros musicales y categorías profesionales.

CRUD de catálogos para admin + consulta pública. Los géneros tienen
sub-categorías (ej. "Urbano" → ["Trap", "Reggaeton"]). Los profesionales
seleccionan categorías para declarar su especialidad.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.generos import CategoriaProfesional, GeneroMusical
from src.services.exceptions import ConflictError, NotFoundError, ValidationError


# ── Géneros ─────────────────────────────────────────────────────


async def list_generos_admin(session: AsyncSession) -> list[GeneroMusical]:
    """Todos los géneros con sus categorías (admin)."""
    result = await session.execute(
        select(GeneroMusical)
        .options(selectinload(GeneroMusical.categorias))
        .order_by(GeneroMusical.nombre)
    )
    return list(result.scalars().all())


async def list_generos_public(session: AsyncSession) -> list[GeneroMusical]:
    """Solo géneros activos con categorías activas (público)."""
    result = await session.execute(
        select(GeneroMusical)
        .options(selectinload(GeneroMusical.categorias))
        .where(GeneroMusical.activo.is_(True))
        .order_by(GeneroMusical.nombre)
    )
    generos = list(result.scalars().all())
    # Filtrar categorías inactivas en memoria
    for g in generos:
        g.categorias = [c for c in g.categorias if c.activo]
    return generos


async def get_genero(session: AsyncSession, genero_id: int) -> GeneroMusical:
    """Obtiene un género por ID o lanza NotFoundError."""
    genero = await session.get(GeneroMusical, genero_id)
    if genero is None:
        raise NotFoundError("Género no encontrado")
    return genero


async def create_genero(session: AsyncSession, nombre: str) -> GeneroMusical:
    """Crea un género. Valida nombre duplicado."""
    nombre = nombre.strip()
    if not nombre:
        raise ValidationError("El nombre es requerido")

    existe = await session.scalar(
        select(GeneroMusical.id).where(GeneroMusical.nombre == nombre)
    )
    if existe is not None:
        raise ConflictError(f"Ya existe un género con el nombre '{nombre}'")

    genero = GeneroMusical(nombre=nombre)
    session.add(genero)
    await session.flush()
    return genero


async def update_genero(
    session: AsyncSession,
    genero_id: int,
    nombre: str | None = None,
    activo: bool | None = None,
) -> GeneroMusical:
    """Actualiza nombre y/o estado activo de un género."""
    genero = await get_genero(session, genero_id)

    if nombre is not None:
        nombre = nombre.strip()
        if not nombre:
            raise ValidationError("El nombre no puede estar vacío")
        duplicado = await session.scalar(
            select(GeneroMusical.id).where(
                GeneroMusical.nombre == nombre,
                GeneroMusical.id != genero_id,
            )
        )
        if duplicado is not None:
            raise ConflictError(f"Ya existe un género con el nombre '{nombre}'")
        genero.nombre = nombre

    if activo is not None:
        genero.activo = activo

    await session.flush()
    return genero


async def delete_genero(session: AsyncSession, genero_id: int) -> None:
    """Elimina un género solo si no tiene campañas asociadas."""
    from src.models.campanas import Campana

    genero = await get_genero(session, genero_id)

    tiene_campanas = await session.scalar(
        select(Campana.id).where(Campana.genero_id == genero_id).limit(1)
    )
    if tiene_campanas is not None:
        raise ConflictError(
            "No se puede eliminar este género porque tiene campañas asociadas. "
            "Desactívalo en su lugar."
        )

    await session.delete(genero)
    await session.flush()


# ── Categorías ──────────────────────────────────────────────────


async def list_categorias(
    session: AsyncSession, genero_id: int
) -> list[CategoriaProfesional]:
    """Categorías de un género (admin, incluye inactivas)."""
    await get_genero(session, genero_id)  # valida que existe
    result = await session.execute(
        select(CategoriaProfesional)
        .where(CategoriaProfesional.genero_id == genero_id)
        .order_by(CategoriaProfesional.nombre)
    )
    return list(result.scalars().all())


async def create_categoria(
    session: AsyncSession, genero_id: int, nombre: str
) -> CategoriaProfesional:
    """Crea una categoría dentro de un género."""
    await get_genero(session, genero_id)  # valida que existe
    nombre = nombre.strip()
    if not nombre:
        raise ValidationError("El nombre es requerido")

    existe = await session.scalar(
        select(CategoriaProfesional.id).where(
            CategoriaProfesional.genero_id == genero_id,
            CategoriaProfesional.nombre == nombre,
        )
    )
    if existe is not None:
        raise ConflictError(
            f"Ya existe una categoría '{nombre}' en este género"
        )

    cat = CategoriaProfesional(genero_id=genero_id, nombre=nombre)
    session.add(cat)
    await session.flush()
    return cat


async def update_categoria(
    session: AsyncSession,
    categoria_id: int,
    nombre: str | None = None,
    activo: bool | None = None,
) -> CategoriaProfesional:
    """Actualiza nombre y/o estado activo de una categoría."""
    cat = await session.get(CategoriaProfesional, categoria_id)
    if cat is None:
        raise NotFoundError("Categoría no encontrada")

    if nombre is not None:
        nombre = nombre.strip()
        if not nombre:
            raise ValidationError("El nombre no puede estar vacío")
        duplicado = await session.scalar(
            select(CategoriaProfesional.id).where(
                CategoriaProfesional.genero_id == cat.genero_id,
                CategoriaProfesional.nombre == nombre,
                CategoriaProfesional.id != categoria_id,
            )
        )
        if duplicado is not None:
            raise ConflictError(
                f"Ya existe una categoría '{nombre}' en este género"
            )
        cat.nombre = nombre

    if activo is not None:
        cat.activo = activo

    await session.flush()
    return cat


async def delete_categoria(session: AsyncSession, categoria_id: int) -> None:
    """Elimina una categoría solo si no hay canales usándola."""
    from src.models.generos import CuradorMedioCategoria

    cat = await session.get(CategoriaProfesional, categoria_id)
    if cat is None:
        raise NotFoundError("Categoría no encontrada")

    tiene_canales = await session.scalar(
        select(CuradorMedioCategoria.medio_id)
        .where(CuradorMedioCategoria.categoria_id == categoria_id)
        .limit(1)
    )
    if tiene_canales is not None:
        raise ConflictError(
            "No se puede eliminar esta categoría porque hay canales "
            "que la usan. Desactívala en su lugar."
        )

    await session.delete(cat)
    await session.flush()


async def validate_categorias_activas(
    session: AsyncSession, categoria_ids: list[int]
) -> list[CategoriaProfesional]:
    """Valida que todas las categorías existen y pertenecen a géneros activos.

    Retorna las categorías encontradas o lanza ValidationError.
    """
    from src.models.generos import GeneroMusical

    result = await session.execute(
        select(CategoriaProfesional)
        .join(GeneroMusical, CategoriaProfesional.genero_id == GeneroMusical.id)
        .where(
            CategoriaProfesional.id.in_(categoria_ids),
            CategoriaProfesional.activo.is_(True),
            GeneroMusical.activo.is_(True),
        )
    )
    cats = list(result.scalars().all())
    encontrados = {c.id for c in cats}
    faltantes = set(categoria_ids) - encontrados
    if faltantes:
        raise ValidationError(
            f"Categorías inválidas o inactivas: {sorted(faltantes)}"
        )
    return cats
