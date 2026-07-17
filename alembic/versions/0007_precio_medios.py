"""precio_creditos en curador_medios + precio_snapshot en campana_medios + monto_usd en creditos_transacciones

Revision ID: 0007
Revises: 0006
Create Date: 2026-07-10
"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0007"
down_revision: Union[str, None] = "0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── curador_medios — precio por tipo de contenido ──
    op.add_column(
        "curador_medios",
        sa.Column(
            "precio_creditos",
            sa.Integer(),
            nullable=False,
            server_default="1",
        ),
    )
    op.create_check_constraint(
        "ck_curador_medios_precio",
        "curador_medios",
        "precio_creditos >= 1",
    )
    op.add_column(
        "curador_medios",
        sa.Column(
            "descripcion_precio",
            sa.String(length=100),
            nullable=True,
        ),
    )

    # ── campana_medios — snapshot de precio al enviar ──
    op.add_column(
        "campana_medios",
        sa.Column(
            "precio_snapshot",
            sa.Integer(),
            nullable=False,
            server_default="1",
        ),
    )

    # ── creditos_transacciones — trazabilidad USD ──
    op.add_column(
        "creditos_transacciones",
        sa.Column(
            "monto_usd",
            sa.Numeric(precision=10, scale=2),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("creditos_transacciones", "monto_usd")
    op.drop_column("campana_medios", "precio_snapshot")
    op.drop_constraint(
        "ck_curador_medios_precio", "curador_medios", type_="check"
    )
    op.drop_column("curador_medios", "descripcion_precio")
    op.drop_column("curador_medios", "precio_creditos")
