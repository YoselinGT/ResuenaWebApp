"""Router admin de paquetes de créditos (`/admin/paquetes` y `/admin/config/creditos`).

Solo accesible para usuarios con perfil Admin (1). Los services lanzan
excepciones de dominio; este router las traduce a códigos HTTP.
"""

from __future__ import annotations

import uuid
from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.infra.db import get_session
from src.middleware.auth import CurrentUser
from src.middleware.roles import require_admin
from src.models.dto.paquetes import (
    ConfigCreditosResponse,
    ConfigCreditosUpdateBody,
    PaqueteAdminResponse,
    PaqueteCamposCalculados,
    PaqueteCreateBody,
    PaqueteUpdateBody,
)
from src.services import paquetes_service

router = APIRouter(prefix="/admin", tags=["admin-paquetes"])


# ── GET /admin/paquetes ───────────────────────────────────────────


@router.get("/paquetes", response_model=list[PaqueteAdminResponse])
async def list_paquetes(
    session: AsyncSession = Depends(get_session),
    _user: CurrentUser = Depends(require_admin),
) -> list[PaqueteAdminResponse]:
    items = await paquetes_service.list_all(session)
    return [
        PaqueteAdminResponse(
            id=p["id"],
            nombre=p["nombre"],
            cantidad_creditos=p["cantidad_creditos"],
            precio_total_usd=p["precio_total_usd"],
            comision_pct=p["comision_pct"],
            descripcion=p["descripcion"],
            activo=p["activo"],
            visible=p["visible"],
            destacado=p["destacado"],
            transacciones_count=p["transacciones_count"],
            calculado=PaqueteCamposCalculados(**p["calculado"]),
            created_at=p["created_at"],
            updated_at=p["updated_at"],
        )
        for p in items
    ]


# ── POST /admin/paquetes ─────────────────────────────────────────


@router.post("/paquetes", response_model=PaqueteAdminResponse, status_code=201)
async def create_paquete(
    body: PaqueteCreateBody,
    session: AsyncSession = Depends(get_session),
    _user: CurrentUser = Depends(require_admin),
) -> PaqueteAdminResponse:
    config = await paquetes_service.get_creditos_config(session)
    paquete = await paquetes_service.create(
        session,
        nombre=body.nombre,
        cantidad_creditos=body.cantidad_creditos,
        precio_total_usd=body.precio_total_usd,
        comision_pct=body.comision_pct,
        descripcion=body.descripcion,
        activo=body.activo,
        visible=body.visible,
        destacado=body.destacado,
    )
    campos = paquetes_service.calcular_campos(
        paquete, config.comision_resuena_pct, config.stripe
    )
    return PaqueteAdminResponse(
        id=str(paquete.id),
        nombre=paquete.nombre,
        cantidad_creditos=paquete.cantidad_creditos,
        precio_total_usd=paquete.precio_total_usd,
        comision_pct=paquete.comision_pct,
        descripcion=paquete.descripcion,
        activo=paquete.activo,
        visible=paquete.visible,
        destacado=paquete.destacado,
        transacciones_count=0,
        calculado=PaqueteCamposCalculados(**campos),
        created_at=paquete.created_at,
        updated_at=paquete.updated_at,
    )


# ── PATCH /admin/paquetes/:id ────────────────────────────────────


@router.patch("/paquetes/{paquete_id}", response_model=PaqueteAdminResponse)
async def update_paquete(
    paquete_id: uuid.UUID,
    body: PaqueteUpdateBody,
    session: AsyncSession = Depends(get_session),
    _user: CurrentUser = Depends(require_admin),
) -> PaqueteAdminResponse:
    config = await paquetes_service.get_creditos_config(session)
    paquete = await paquetes_service.update(
        session,
        paquete_id,
        nombre=body.nombre,
        descripcion=body.descripcion,
        precio_total_usd=body.precio_total_usd,
        comision_pct=body.comision_pct,
        comision_pct_set=body.comision_pct is not None or body.model_fields_set == {"comision_pct"},
        activo=body.activo,
        visible=body.visible,
        destacado=body.destacado,
    )
    campos = paquetes_service.calcular_campos(
        paquete, config.comision_resuena_pct, config.stripe
    )
    return PaqueteAdminResponse(
        id=str(paquete.id),
        nombre=paquete.nombre,
        cantidad_creditos=paquete.cantidad_creditos,
        precio_total_usd=paquete.precio_total_usd,
        comision_pct=paquete.comision_pct,
        descripcion=paquete.descripcion,
        activo=paquete.activo,
        visible=paquete.visible,
        destacado=paquete.destacado,
        transacciones_count=0,
        calculado=PaqueteCamposCalculados(**campos),
        created_at=paquete.created_at,
        updated_at=paquete.updated_at,
    )


# ── GET /admin/config/creditos ───────────────────────────────────


@router.get("/config/creditos", response_model=ConfigCreditosResponse)
async def get_config_creditos(
    session: AsyncSession = Depends(get_session),
    _user: CurrentUser = Depends(require_admin),
) -> ConfigCreditosResponse:
    config = await paquetes_service.get_creditos_config(session)
    return ConfigCreditosResponse(
        precio_credito_individual_usd=config.precio_individual_usd,
        comision_resuena_pct=config.comision_resuena_pct,
        stripe_pct_nacional=config.stripe.pct_nacional,
        stripe_fixed_usd=config.stripe.fixed_usd,
        stripe_pct_internacional=config.stripe.pct_internacional,
        stripe_pct_conversion_moneda=config.stripe.pct_conversion_moneda,
        stripe_pct_oxxo=config.stripe.pct_oxxo,
        stripe_fixed_disputa_usd=Decimal("8.57"),  # se lee pero no se expone en config editable
        stripe_escenario_default=config.stripe.escenario_default,
    )


# ── PATCH /admin/config/creditos ─────────────────────────────────


@router.patch("/config/creditos", response_model=ConfigCreditosResponse)
async def update_config_creditos(
    body: ConfigCreditosUpdateBody,
    session: AsyncSession = Depends(get_session),
    _user: CurrentUser = Depends(require_admin),
) -> ConfigCreditosResponse:
    from src.models.parametros_config import ParametroConfig

    # Mapeo de campo → clave en BD
    field_map = {
        "precio_credito_individual_usd": "precio_credito_individual_usd",
        "comision_resuena_pct": "comision_resuena_pct",
        "stripe_pct_nacional": "stripe_pct_nacional",
        "stripe_fixed_usd": "stripe_fixed_usd",
        "stripe_pct_internacional": "stripe_pct_internacional",
        "stripe_pct_conversion_moneda": "stripe_pct_conversion_moneda",
        "stripe_pct_oxxo": "stripe_pct_oxxo",
        "stripe_fixed_disputa_usd": "stripe_fixed_disputa_usd",
        "stripe_escenario_default": "stripe_escenario_default",
    }

    updates = body.model_dump(exclude_unset=True)
    for field, clave in field_map.items():
        if field in updates:
            valor = str(updates[field])
            await session.execute(
                ParametroConfig.__table__.update()
                .where(ParametroConfig.clave == clave)
                .values(valor_cifrado=valor)
            )

    await session.flush()
    await session.commit()
    config = await paquetes_service.get_creditos_config(session)
    return ConfigCreditosResponse(
        precio_credito_individual_usd=config.precio_individual_usd,
        comision_resuena_pct=config.comision_resuena_pct,
        stripe_pct_nacional=config.stripe.pct_nacional,
        stripe_fixed_usd=config.stripe.fixed_usd,
        stripe_pct_internacional=config.stripe.pct_internacional,
        stripe_pct_conversion_moneda=config.stripe.pct_conversion_moneda,
        stripe_pct_oxxo=config.stripe.pct_oxxo,
        stripe_fixed_disputa_usd=Decimal("8.57"),
        stripe_escenario_default=config.stripe.escenario_default,
    )
