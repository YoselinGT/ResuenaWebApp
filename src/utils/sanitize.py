"""Sanitización de entradas de texto (defensa contra XSS / inyección de markup).

Para campos de texto plano (nombres, títulos): se eliminan etiquetas HTML y
caracteres de control, y se normaliza el espacio en blanco. El escape final para
render lo hacen React (frontend) y Jinja2 con autoescape (emails); esto es
defensa en profundidad para lo que se persiste.
"""

from __future__ import annotations

import re

# Etiquetas HTML/XML completas (<...>) incluyendo las mal cerradas.
_TAG_RE = re.compile(r"<[^>]*>")
# Caracteres de control (excepto nada: los nombres no llevan saltos ni tabs).
_CONTROL_RE = re.compile(r"[\x00-\x1f\x7f]")
# Cualquier corchete angular residual tras quitar etiquetas.
_ANGLE_RE = re.compile(r"[<>]")
# Espacios repetidos.
_WS_RE = re.compile(r"\s+")


def clean_text(value: str | None) -> str | None:
    """Limpia un texto plano. Devuelve None si la entrada es None.

    Quita etiquetas HTML, caracteres de control y corchetes angulares, y
    colapsa el espacio en blanco. El resultado puede quedar vacío si la entrada
    era solo markup; el caller decide si eso es válido.
    """
    if value is None:
        return None
    cleaned = _TAG_RE.sub("", value)
    cleaned = _CONTROL_RE.sub("", cleaned)
    cleaned = _ANGLE_RE.sub("", cleaned)
    cleaned = _WS_RE.sub(" ", cleaned)
    return cleaned.strip()
