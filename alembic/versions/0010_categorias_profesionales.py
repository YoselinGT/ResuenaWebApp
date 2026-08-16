"""categorias_profesionales + profesional_categorias

Revision ID: 0010
Revises: 0009
Create Date: 2026-07-10
"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0010"
down_revision: Union[str, None] = "0009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── categorias_profesionales ──
    op.create_table(
        "categorias_profesionales",
        sa.Column(
            "id",
            sa.Integer(),
            primary_key=True,
            autoincrement=True,
        ),
        sa.Column(
            "genero_id",
            sa.Integer(),
            sa.ForeignKey("generos_musicales.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("nombre", sa.String(100), nullable=False),
        sa.Column(
            "activo",
            sa.Boolean(),
            nullable=False,
            server_default="true",
        ),
    )
    op.create_index(
        "ix_categorias_profesionales_genero_id",
        "categorias_profesionales",
        ["genero_id"],
    )
    op.create_unique_constraint(
        "uq_categorias_profesionales_genero_nombre",
        "categorias_profesionales",
        ["genero_id", "nombre"],
    )

    # ── profesional_categorias ──
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


def downgrade() -> None:
    op.drop_table("profesional_categorias")
    op.drop_constraint(
        "uq_categorias_profesionales_genero_nombre",
        "categorias_profesionales",
        type_="unique",
    )
    op.drop_index(
        "ix_categorias_profesionales_genero_id",
        table_name="categorias_profesionales",
    )
    op.drop_table("categorias_profesionales")
