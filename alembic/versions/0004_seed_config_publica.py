"""seed config pública — titulo_plataforma y mensaje_bienvenida

Revision ID: 0004
Revises: 0003
Create Date: 2026-06-28
"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Parámetros públicos consumidos por GET /config/public (no secretos).
PARAMETROS_PUBLICOS = [
    {
        "clave": "titulo_plataforma",
        "valor": "Resuena",
        "descripcion": "Título de la plataforma mostrado en la UI pública",
    },
    {
        "clave": "mensaje_bienvenida",
        "valor": "Conecta tu música con la audiencia correcta.",
        "descripcion": "Mensaje de bienvenida mostrado en el dashboard",
    },
]


def upgrade() -> None:
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
            for p in PARAMETROS_PUBLICOS
        ],
    )


def downgrade() -> None:
    op.execute(
        "DELETE FROM parametros_config WHERE clave IN ("
        + ", ".join(f"'{p['clave']}'" for p in PARAMETROS_PUBLICOS)
        + ")"
    )
