"""curador_medio_categorias: categorías por canal (reemplaza profesional_categorias)

Revision ID: 0011
Revises: 0010
Create Date: 2026-07-18
"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "0011"
down_revision: Union[str, None] = "0010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Nueva tabla: categorías por canal ──
    op.create_table(
        "curador_medio_categorias",
        sa.Column(
            "medio_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("curador_medios.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "categoria_id",
            sa.Integer(),
            sa.ForeignKey("categorias_profesionales.id", ondelete="RESTRICT"),
            primary_key=True,
        ),
    )

    # ── Eliminar tabla vieja: categorías por usuario ──
    op.drop_table("profesional_categorias")


def downgrade() -> None:
    # Recrear profesional_categorias
    op.create_table(
        "profesional_categorias",
        sa.Column(
            "usuario_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("usuarios.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "categoria_id",
            sa.Integer(),
            sa.ForeignKey("categorias_profesionales.id", ondelete="RESTRICT"),
            primary_key=True,
        ),
    )

    # Eliminar curador_medio_categorias
    op.drop_table("curador_medio_categorias")
