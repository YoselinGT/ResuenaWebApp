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
    CheckoutBody,
    CheckoutURLDTO,
    PaginatedTransaccionesDTO,
    PaqueteDTO,
)
from src.services import stripe_service, wallet_service
from src.services.exceptions import ValidationError
from src.services.stripe_service import WebhookInvalidError

router = APIRouter(prefix="/creditos", tags=["creditos"])


@router.get("/paquetes", response_model=list[PaqueteDTO])
async def paquetes(
    session: AsyncSession = Depends(get_session),
    user: CurrentUser = Depends(get_current_user),
) -> list[PaqueteDTO]:
    return await wallet_service.list_paquetes(session)


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
    body: CheckoutBody,
    session: AsyncSession = Depends(get_session),
    user: CurrentUser = Depends(require_artista),
) -> CheckoutURLDTO:
    if body.cantidad_creditos not in wallet_service.PAQUETES_CREDITOS:
        raise ValidationError("Paquete de créditos no válido")
    precio = await wallet_service.get_precio_credito(session)
    url = await stripe_service.create_checkout_session(
        uuid.UUID(user.id), body.cantidad_creditos, precio
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
