"""Servicio de envío de email transaccional (async).

Usa aiosmtplib apuntando a MailHog en dev (sin TLS ni auth) y Jinja2 para
renderizar los templates HTML de `src/infra/email_templates/`.

Nunca incluir secretos ni tokens en logs; el cuerpo del email sí lleva el
token/OTP porque es su propósito, pero no se loguea.
"""

from __future__ import annotations

from email.message import EmailMessage
from pathlib import Path

import aiosmtplib
import structlog
from jinja2 import Environment, FileSystemLoader, select_autoescape

from src.config.settings import get_settings

logger = structlog.get_logger()
settings = get_settings()

_TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "infra" / "email_templates"

_env = Environment(
    loader=FileSystemLoader(str(_TEMPLATES_DIR)),
    autoescape=select_autoescape(["html"]),
    enable_async=True,
)


async def send_email(to: str, subject: str, template: str, context: dict) -> None:
    """Renderiza `<template>.html` con `context` y lo envía por SMTP."""
    body = await _env.get_template(f"{template}.html").render_async(**context)

    message = EmailMessage()
    message["From"] = settings.smtp_from
    message["To"] = to
    message["Subject"] = subject
    message.set_content(
        "Este mensaje requiere un cliente compatible con HTML.",
    )
    message.add_alternative(body, subtype="html")

    await aiosmtplib.send(
        message,
        hostname=settings.smtp_host,
        port=settings.smtp_port,
        start_tls=False,  # MailHog no soporta STARTTLS en dev
    )
    logger.info("email.sent", to=to, template=template)


# ── Helpers por tipo de email ────────────────────────────────────

async def send_otp(to: str, codigo: str) -> None:
    await send_email(to, "Tu código de acceso a Resuena", "otp", {"codigo": codigo})


async def send_confirm_artista(to: str, nombre: str, url: str) -> None:
    await send_email(
        to, "Confirma tu cuenta de artista en Resuena",
        "confirm_artista", {"nombre": nombre, "url": url},
    )


async def send_confirm_profesional(to: str, nombre: str, url: str) -> None:
    await send_email(
        to, "Confirma tu cuenta en Resuena",
        "confirm_profesional", {"nombre": nombre, "url": url},
    )


async def send_reset(to: str, nombre: str, url: str) -> None:
    await send_email(
        to, "Restablece tu contraseña de Resuena",
        "reset", {"nombre": nombre, "url": url},
    )


async def send_aprobacion(to: str, nombre: str) -> None:
    await send_email(
        to, "¡Tu solicitud en Resuena fue aprobada!",
        "aprobacion", {"nombre": nombre},
    )


async def send_rechazo(to: str, nombre: str, motivo: str) -> None:
    await send_email(
        to, "Actualización de tu solicitud en Resuena",
        "rechazo", {"nombre": nombre, "motivo": motivo},
    )


async def send_admin_nueva_solicitud(
    to: str, nombre: str, correo: str, tipo_profesional: str, url_portfolio: str | None
) -> None:
    await send_email(
        to, "Nueva solicitud de curador — Resuena", "admin_solicitud",
        {
            "nombre": nombre,
            "correo": correo,
            "tipo_profesional": tipo_profesional,
            "url_portfolio": url_portfolio,
        },
    )
