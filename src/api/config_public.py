"""Router de configuración pública (`/config`).

Endpoint sin sesión: expone solo parámetros no sensibles para la UI pública.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.infra.db import get_session
from src.services import config_service

router = APIRouter(prefix="/config", tags=["config"])


class PublicConfigDTO(BaseModel):
    titulo_plataforma: str
    mensaje_bienvenida: str


@router.get("/public", response_model=PublicConfigDTO)
async def public_config(
    session: AsyncSession = Depends(get_session),
) -> PublicConfigDTO:
    data = await config_service.get_public_config(session)
    return PublicConfigDTO(**data)
