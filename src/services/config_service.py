"""Servicio de configuración del sistema.

Lee parámetros de `parametros_config`. La variante pública solo expone claves
no secretas y nunca devuelve valores marcados como `es_secreto`.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.parametros_config import ParametroConfig

# Claves públicas y sus valores por defecto (si faltaran en BD).
PUBLIC_DEFAULTS: dict[str, str] = {
    "titulo_plataforma": "Resuena",
    "mensaje_bienvenida": "Conecta tu música con la audiencia correcta.",
}


async def get_public_config(session: AsyncSession) -> dict[str, str]:
    """Devuelve la configuración pública ({clave: valor}).

    Solo lee parámetros no secretos; las claves ausentes caen a su default.
    """
    rows = await session.execute(
        select(ParametroConfig.clave, ParametroConfig.valor_cifrado).where(
            ParametroConfig.clave.in_(PUBLIC_DEFAULTS.keys()),
            ParametroConfig.es_secreto.is_(False),
        )
    )
    encontrados = dict(rows.all())
    return {
        clave: (encontrados.get(clave) or default)
        for clave, default in PUBLIC_DEFAULTS.items()
    }
