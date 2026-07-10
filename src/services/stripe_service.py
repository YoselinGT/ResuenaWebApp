"""Integración con Stripe Checkout (modo test) y webhooks.

Reglas no negociables:
- La firma de los webhooks se verifica SIEMPRE antes de procesar datos.
- Nunca se loguea la clave secreta ni el cuerpo del webhook.

El SDK de Stripe es síncrono; las llamadas de red se ejecutan en un threadpool
(`asyncio.to_thread`) para no bloquear el event loop. La acreditación de créditos
es idempotente por `payment_intent` (ver `wallet_service.add_credits`).
"""

from __future__ import annotations

import asyncio
import uuid

import stripe
import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.settings import get_settings
from src.services import wallet_service
from src.services.exceptions import ValidationError

logger = structlog.get_logger()
settings = get_settings()

stripe.api_key = settings.stripe_secret_key


# Error tipado para firma/payload inválidos (el router lo traduce a 400).
class WebhookInvalidError(ValidationError):
    """Firma o payload de webhook inválido. → 400."""


async def create_checkout_session(
    usuario_id: uuid.UUID,
    cantidad_creditos: int,
    artista_paga_usd,
    *,
    nombre_producto: str = "Crédito Resuena",
    precio_neto_usd=None,
    paquete_id: str | None = None,
) -> str:
    """Crea una Checkout Session con price_data dinámico en USD."""
    # Convertir a centavos para Stripe
    unit_amount = round(float(artista_paga_usd) * 100)

    metadata = {
        "usuario_id": str(usuario_id),
        "cantidad_creditos": str(cantidad_creditos),
    }
    if paquete_id is not None:
        metadata["paquete_id"] = paquete_id
    if precio_neto_usd is not None:
        metadata["precio_neto_usd"] = str(precio_neto_usd)

    session = await asyncio.to_thread(
        stripe.checkout.Session.create,
        mode="payment",
        success_url=(
            f"{settings.frontend_url}/artista/creditos/success"
            "?session_id={CHECKOUT_SESSION_ID}"
        ),
        cancel_url=f"{settings.frontend_url}/artista/creditos/cancel",
        client_reference_id=str(usuario_id),
        metadata=metadata,
        line_items=[
            {
                "quantity": 1,
                "price_data": {
                    "currency": "usd",
                    "unit_amount": unit_amount,
                    "product_data": {"name": nombre_producto},
                },
            }
        ],
    )
    return session.url


async def handle_webhook(
    db: AsyncSession, payload: bytes, signature: str
) -> None:
    """Verifica la firma y procesa el evento. → WebhookInvalidError si la firma falla."""
    try:
        event = stripe.Webhook.construct_event(
            payload, signature, settings.stripe_webhook_secret
        )
    except (ValueError, stripe.error.SignatureVerificationError) as exc:
        raise WebhookInvalidError("Firma de webhook inválida") from exc

    if event["type"] != "checkout.session.completed":
        return  # eventos no relevantes se ignoran (200 OK)

    obj = event["data"]["object"]
    metadata = obj.get("metadata") or {}
    usuario_id = metadata.get("usuario_id") or obj.get("client_reference_id")
    cantidad = metadata.get("cantidad_creditos")
    # `payment_intent` da idempotencia estable; cae a session id si faltara.
    referencia = obj.get("payment_intent") or obj.get("id")

    if not usuario_id or not cantidad:
        logger.warning("stripe.webhook.metadata_incompleta", session=obj.get("id"))
        return

    await wallet_service.add_credits(
        db,
        uuid.UUID(usuario_id),
        int(cantidad),
        descripcion=f"Compra de {cantidad} créditos",
        referencia=referencia,
    )
    logger.info("stripe.webhook.creditos_acreditados", referencia=referencia)
