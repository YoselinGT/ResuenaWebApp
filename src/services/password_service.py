"""Servicio de passwords: hashing BCrypt y validación de patrón fuerte.

Reglas no negociables (CLAUDE.md):
- BCrypt con cost ≥ 12.
- Nunca loguear el password ni el hash.

Patrón fuerte exigido: ≥ 8 caracteres con al menos una mayúscula, una minúscula,
un número y un símbolo.

Nota sobre el límite de BCrypt: BCrypt solo considera los primeros 72 bytes del
input y trunca el resto silenciosamente. Para soportar passwords/passphrases de
cualquier longitud sin esa pérdida, se pre-hashea con SHA-256 y se codifica en
base64 (44 bytes) antes de pasar a BCrypt — patrón estándar (p. ej. Dropbox).
"""

from __future__ import annotations

import base64
import hashlib
import re

import bcrypt

BCRYPT_ROUNDS = 12

# Whitelist de "símbolos" aceptados como carácter especial.
_PATTERN_CHECKS = (
    re.compile(r"[a-z]"),          # minúscula
    re.compile(r"[A-Z]"),          # mayúscula
    re.compile(r"[0-9]"),          # número
    re.compile(r"[^A-Za-z0-9]"),   # símbolo (cualquier no alfanumérico)
)

MIN_LENGTH = 8
MAX_LENGTH = 128


def _prepare(password: str) -> bytes:
    """Pre-hash SHA-256 + base64 para evadir el límite de 72 bytes de BCrypt."""
    digest = hashlib.sha256(password.encode("utf-8")).digest()
    return base64.b64encode(digest)


def hash_password(password: str) -> str:
    """Devuelve el hash BCrypt (cost 12) del password, listo para persistir."""
    return bcrypt.hashpw(_prepare(password), bcrypt.gensalt(rounds=BCRYPT_ROUNDS)).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """Verifica un password contra su hash. No lanza ante hash malformado."""
    try:
        return bcrypt.checkpw(_prepare(password), password_hash.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def validate_pattern(password: str) -> bool:
    """True si el password cumple el patrón fuerte; False en caso contrario."""
    if not (MIN_LENGTH <= len(password) <= MAX_LENGTH):
        return False
    return all(check.search(password) for check in _PATTERN_CHECKS)
