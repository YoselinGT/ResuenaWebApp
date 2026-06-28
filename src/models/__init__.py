"""Paquete de modelos ORM.

Importar TODOS los modelos aquí garantiza que `Base.metadata` esté completa
cuando Alembic hace autogenerate (alembic/env.py importa este paquete).
"""

from src.models.base import Base, CreatedAtMixin, TimestampMixin, UUIDPrimaryKeyMixin
from src.models.bitacora_eventos import BitacoraEvento
from src.models.campana_medios import CampanaMedio
from src.models.campanas import Campana
from src.models.catalogos import Idioma, Region
from src.models.creditos import CreditoTransaccion, Wallet
from src.models.curador_medios import CuradorMedio
from src.models.entregas import EntregaContenido
from src.models.generos import CuradorMedioGenero, GeneroMusical, UsuarioGenero
from src.models.ips_bloqueadas import IpBloqueada
from src.models.parametros_config import ParametroConfig
from src.models.perfiles import Perfil
from src.models.sellos import SelloArtista, SelloDiscografico
from src.models.solicitudes_curador import SolicitudCurador
from src.models.solicitudes_retiro import SolicitudRetiro
from src.models.tokens import Token
from src.models.usuario_preferencias import (
    UsuarioPreferenciaIdioma,
    UsuarioPreferenciaRegion,
    UsuarioPreferencias,
)
from src.models.usuario_redes import UsuarioRed
from src.models.usuarios import Usuario

__all__ = [
    "Base",
    "UUIDPrimaryKeyMixin",
    "TimestampMixin",
    "CreatedAtMixin",
    "Perfil",
    "Usuario",
    "SelloDiscografico",
    "SelloArtista",
    "SolicitudCurador",
    "CuradorMedio",
    "GeneroMusical",
    "UsuarioGenero",
    "CuradorMedioGenero",
    "Idioma",
    "Region",
    "UsuarioPreferencias",
    "UsuarioPreferenciaIdioma",
    "UsuarioPreferenciaRegion",
    "UsuarioRed",
    "CreditoTransaccion",
    "Wallet",
    "Campana",
    "CampanaMedio",
    "EntregaContenido",
    "SolicitudRetiro",
    "BitacoraEvento",
    "IpBloqueada",
    "Token",
    "ParametroConfig",
]
