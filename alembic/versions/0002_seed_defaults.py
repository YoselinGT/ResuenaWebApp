"""seed defaults — perfiles, géneros musicales y parámetros de configuración

Revision ID: 0002
Revises: 0001
Create Date: 2026-06-28
"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Perfiles base con IDs estables (el código y otros seeds asumen 1=Admin).
PERFILES = [
    {"id": 1, "nombre": "Admin", "descripcion": "Administrador del sistema (protegido)"},
    {"id": 2, "nombre": "Artista", "descripcion": "Artista o sello que crea campañas"},
    {"id": 3, "nombre": "Curador", "descripcion": "Curador que recibe y evalúa campañas"},
]

# Géneros base. Se insertan sin id explícito (la secuencia asigna 1..20).
GENEROS = [
    "Pop", "Indie", "Electrónica", "Hip-hop", "Rock", "Regional Mexicano",
    "Jazz", "Clásica", "R&B", "Cumbia", "Salsa", "Metal", "Reggaeton",
    "Trap", "Corridos", "Folk", "Soul", "Funk", "Ambient", "House",
]

# Parámetros de configuración con sus valores por defecto (no secretos).
PARAMETROS = [
    {"clave": "creditos_por_medio", "valor": "1",
     "descripcion": "Créditos que cuesta enviar una campaña a un medio"},
    {"clave": "dias_limite_respuesta", "valor": "6",
     "descripcion": "Días que tiene el curador para aceptar/rechazar"},
    {"clave": "precio_credito_mxn", "valor": "50",
     "descripcion": "Precio de un crédito en pesos mexicanos"},
    {"clave": "minimo_palabras_resena", "valor": "150",
     "descripcion": "Mínimo de palabras para una reseña de blogger"},
    {"clave": "porcentaje_comision", "valor": "20",
     "descripcion": "Comisión de la plataforma sobre retiros (%)"},
    {"clave": "max_intentos_login", "valor": "5",
     "descripcion": "Intentos de login fallidos antes de bloquear"},
    {"clave": "block_duration_hours", "valor": "6",
     "descripcion": "Horas de bloqueo tras exceder intentos de login"},
]


def upgrade() -> None:
    perfiles_tbl = sa.table(
        "perfiles",
        sa.column("id", sa.Integer),
        sa.column("nombre", sa.String),
        sa.column("descripcion", sa.Text),
    )
    op.bulk_insert(perfiles_tbl, PERFILES)
    # La secuencia no avanza al insertar IDs explícitos: la sincronizamos para
    # que futuros perfiles no colisionen con 1/2/3.
    op.execute(
        "SELECT setval(pg_get_serial_sequence('perfiles', 'id'), "
        "(SELECT MAX(id) FROM perfiles))"
    )

    generos_tbl = sa.table(
        "generos_musicales",
        sa.column("nombre", sa.String),
    )
    op.bulk_insert(generos_tbl, [{"nombre": n} for n in GENEROS])

    params_tbl = sa.table(
        "parametros_config",
        sa.column("clave", sa.String),
        sa.column("valor_cifrado", sa.Text),
        sa.column("es_secreto", sa.Boolean),
        sa.column("descripcion", sa.Text),
    )
    op.bulk_insert(
        params_tbl,
        [
            {
                "clave": p["clave"],
                "valor_cifrado": p["valor"],
                "es_secreto": False,
                "descripcion": p["descripcion"],
            }
            for p in PARAMETROS
        ],
    )


def downgrade() -> None:
    op.execute(
        "DELETE FROM parametros_config WHERE clave IN ("
        + ", ".join(f"'{p['clave']}'" for p in PARAMETROS)
        + ")"
    )
    op.execute(
        "DELETE FROM generos_musicales WHERE nombre IN ("
        + ", ".join(f"'{n}'" for n in GENEROS)
        + ")"
    )
    op.execute("DELETE FROM perfiles WHERE id IN (1, 2, 3)")
