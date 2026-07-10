"""Router de créditos (`/creditos`)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.infra.db import get_session
from src.middleware.auth import CurrentUser, get_current_user
from src.middleware.roles import require_artista
from src.models.dto.creditos import (
    BalanceDTO,
    CheckoutURLDTO,
    PaginatedTransaccionesDTO,
)
from src.models.dto.paquetes import (
    CheckoutBodyUSD,
    PaqueteCamposCalculados,
    PaquetePublicoResponse,
)
from src.services import paquetes_service, stripe_service, wallet_service
from src.services.exceptions import ValidationError
from src.services.stripe_service import WebhookInvalidError

router = APIRouter(prefix="/creditos", tags=["creditos"])


@router.get("/paquetes", response_model=list[PaquetePublicoResponse])
async def paquetes(
    session: AsyncSession = Depends(get_session),
    _user: CurrentUser = Depends(get_current_user),
) -> list[PaquetePublicoResponse]:
    items = await paquetes_service.list_activos(session)
    return [
        PaquetePublicoResponse(
            id=p["id"],
            nombre=p["nombre"],
            cantidad_creditos=p["cantidad_creditos"],
            precio_total_usd=p["precio_total_usd"],
            descripcion=p["descripcion"],
            destacado=p["destacado"],
            calculado=PaqueteCamposCalculados(**p["calculado"]),
        )
        for p in items
    ]


@router.get("/balance", response_model=BalanceDTO)
async def balance(
    session: AsyncSession = Depends(get_session),
    user: CurrentUser = Depends(get_current_user),
) -> BalanceDTO:
    wallet = await wallet_service.get_balance(session, uuid.UUID(user.id))
    return BalanceDTO(
        saldo_creditos=wallet.saldo_creditos,
        saldo_pendiente_retiro=wallet.saldo_pendiente_retiro,
    )


@router.get("/historial", response_model=PaginatedTransaccionesDTO)
async def historial(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
    user: CurrentUser = Depends(get_current_user),
) -> PaginatedTransaccionesDTO:
    return await wallet_service.list_historial(
        session, uuid.UUID(user.id), page, page_size
    )


@router.post("/checkout", response_model=CheckoutURLDTO)
async def checkout(
    body: CheckoutBodyUSD,
    session: AsyncSession = Depends(get_session),
    user: CurrentUser = Depends(require_artista),
) -> CheckoutURLDTO:
    config = await paquetes_service.get_creditos_config(session)

    if body.paquete_id is not None:
        # Compra de paquete
        paquete = await paquetes_service.get_by_id(
            session, uuid.UUID(body.paquete_id)
        )
        if not paquete.activo:
            raise ValidationError("Paquete inactivo")
        precio_neto = paquete.precio_total_usd
        cantidad = paquete.cantidad_creditos
        nombre_producto = f"{paquete.nombre} — {paquete.cantidad_creditos} créditos"
    elif body.cantidad_creditos is not None:
        # Compra individual
        precio_neto = config.precio_individual_usd * body.cantidad_creditos
        cantidad = body.cantidad_creditos
        nombre_producto = f"{cantidad} créditos sueltos"
    else:
        raise ValidationError("Debes indicar paquete_id o cantidad_creditos")

    artista_paga = paquetes_service.calcular_precio_artista(
        precio_neto,
        config.stripe.escenario_default,
        stripe=config.stripe,
    )

    url = await stripe_service.create_checkout_session(
        uuid.UUID(user.id),
        cantidad,
        artista_paga,
        nombre_producto=nombre_producto,
        precio_neto_usd=precio_neto,
        paquete_id=body.paquete_id,
    )
    return CheckoutURLDTO(checkout_url=url)


@router.post("/webhook")
async def webhook(
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> Response:
    """Webhook de Stripe (sin sesión). Verifica firma; 400 si es inválida."""
    payload = await request.body()
    signature = request.headers.get("stripe-signature", "")
    try:
        await stripe_service.handle_webhook(session, payload, signature)
    except WebhookInvalidError:
        return Response(status_code=status.HTTP_400_BAD_REQUEST)
    return Response(status_code=status.HTTP_200_OK)
