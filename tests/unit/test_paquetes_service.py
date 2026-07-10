"""Tests unitarios — paquetes_service (Fase 06b)."""

from __future__ import annotations

from decimal import Decimal

import pytest

from src.services.paquetes_service import (
    StripeConfig,
    calcular_precio_artista,
)


def _default_stripe() -> StripeConfig:
    return StripeConfig(
        pct_nacional=Decimal("0.036"),
        fixed_usd=Decimal("0.17"),
        pct_internacional=Decimal("0.005"),
        pct_conversion_moneda=Decimal("0.02"),
        pct_oxxo=Decimal("0.04"),
        escenario_default="nacional",
    )


class TestCalcularPrecioArtista:
    def test_nacional(self):
        stripe = _default_stripe()
        result = calcular_precio_artista(
            Decimal("18.00"), "nacional", stripe=stripe
        )
        assert result == Decimal("18.83")

    def test_internacional(self):
        stripe = _default_stripe()
        result = calcular_precio_artista(
            Decimal("18.00"), "internacional", stripe=stripe
        )
        assert result == Decimal("18.94")

    def test_internacional_con_conversion(self):
        stripe = _default_stripe()
        result = calcular_precio_artista(
            Decimal("18.00"), "internacional", con_conversion=True, stripe=stripe
        )
        assert result == Decimal("19.26")

    def test_oxxo(self):
        stripe = _default_stripe()
        result = calcular_precio_artista(
            Decimal("18.00"), "oxxo", stripe=stripe
        )
        assert result == Decimal("18.92")

    def test_nacional_precio_pequeno(self):
        stripe = _default_stripe()
        result = calcular_precio_artista(
            Decimal("2.00"), "nacional", stripe=stripe
        )
        assert result == Decimal("2.10")
