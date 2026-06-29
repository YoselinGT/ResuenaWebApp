"""Tipos ENUM del dominio, centralizados para evitar duplicar tipos PostgreSQL.

Cada enum se materializa como un tipo ENUM nativo de PostgreSQL. Se usa
`values_callable` para que en la BD se almacene el `.value` (minúsculas),
no el nombre del miembro.
"""

from __future__ import annotations

import enum

from sqlalchemy import Enum as SAEnum


def pg_enum(enum_cls: type[enum.Enum], name: str) -> SAEnum:
    """Construye un `Enum` de SQLAlchemy que persiste el `.value` del miembro."""
    return SAEnum(
        enum_cls,
        name=name,
        values_callable=lambda obj: [e.value for e in obj],
    )


class TipoUsuario(str, enum.Enum):
    artista = "artista"
    curador = "curador"


class RolSelloArtista(str, enum.Enum):
    owner = "owner"
    manager = "manager"
    artista = "artista"


class EstadoSolicitudCurador(str, enum.Enum):
    pendiente = "pendiente"
    aprobada = "aprobada"
    rechazada = "rechazada"


class EstadoInvitacionSello(str, enum.Enum):
    pendiente = "pendiente"
    aceptada = "aceptada"
    rechazada = "rechazada"


class TipoMedio(str, enum.Enum):
    playlist = "playlist"
    blog = "blog"
    instagram = "instagram"
    tiktok = "tiktok"
    youtube = "youtube"
    facebook = "facebook"
    twitter = "twitter"
    radio = "radio"
    website = "website"
    eventos = "eventos"
    otro = "otro"


class TipoPreferenciaGenero(str, enum.Enum):
    preferido = "preferido"
    excluido = "excluido"


class TipoLanzamientos(str, enum.Enum):
    nuevos = "nuevos"
    post = "post"
    ambos = "ambos"


class TipoRedSocial(str, enum.Enum):
    spotify = "spotify"
    instagram = "instagram"
    youtube = "youtube"
    tiktok = "tiktok"
    facebook = "facebook"
    twitter = "twitter"
    soundcloud = "soundcloud"
    bandcamp = "bandcamp"
    website = "website"
    otro = "otro"


class TipoTransaccionCredito(str, enum.Enum):
    compra = "compra"
    gasto = "gasto"
    devolucion = "devolucion"
    retiro = "retiro"


class EstadoCampana(str, enum.Enum):
    borrador = "borrador"
    enviada = "enviada"
    en_revision = "en_revision"
    completada = "completada"
    cancelada = "cancelada"


class EstadoCampanaMedio(str, enum.Enum):
    pendiente = "pendiente"
    aceptada = "aceptada"
    rechazada = "rechazada"
    entregada = "entregada"
    expirada = "expirada"


class TipoEntrega(str, enum.Enum):
    blog = "blog"
    playlist = "playlist"
    reel = "reel"
    link = "link"
    post = "post"


class EstadoSolicitudRetiro(str, enum.Enum):
    pendiente = "pendiente"
    aprobada = "aprobada"
    rechazada = "rechazada"
    pagada = "pagada"


class TipoToken(str, enum.Enum):
    registro = "registro"
    reset = "reset"
    confirmacion_email = "confirmacion_email"
