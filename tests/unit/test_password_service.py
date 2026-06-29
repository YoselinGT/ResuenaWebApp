"""Tests unitarios del servicio de passwords (sin BD)."""

from __future__ import annotations

import pytest

from src.services.password_service import (
    hash_password,
    validate_pattern,
    verify_password,
)


def test_hash_verify_roundtrip():
    h = hash_password("Str0ng!Pass")
    assert verify_password("Str0ng!Pass", h) is True
    assert verify_password("otraCosa1!", h) is False


def test_hash_usa_bcrypt_cost_12():
    h = hash_password("Str0ng!Pass")
    assert h.startswith("$2b$12$")


def test_verify_no_lanza_con_hash_malformado():
    assert verify_password("x", "no-es-un-hash") is False


def test_prehash_evita_truncado_72_bytes():
    # Dos passwords idénticos en los primeros 72 bytes pero distintos después.
    base = "A1!" + "a" * 70  # 73 chars
    otro = "A1!" + "a" * 69 + "b"
    h = hash_password(base)
    # Con BCrypt puro ambos truncarían a 72 bytes y verificarían igual;
    # con pre-hash SHA-256 deben diferenciarse.
    assert verify_password(base, h) is True
    assert verify_password(otro, h) is False


@pytest.mark.parametrize(
    "password,esperado",
    [
        ("Str0ng!Pass", True),
        ("short1!A", True),       # 8 chars exactos
        ("alllower1!", False),     # sin mayúscula
        ("ALLUPPER1!", False),     # sin minúscula
        ("NoNumber!", False),      # sin número
        ("NoSymbol1A", False),     # sin símbolo
        ("Ab1!", False),           # < 8 chars
        ("", False),
    ],
)
def test_validate_pattern(password, esperado):
    assert validate_pattern(password) is esperado
