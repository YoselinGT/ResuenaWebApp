"""estado_revision por canal en curador_medios

Revision ID: 0008
Revises: 0007
Create Date: 2026-07-10
"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0008"
down_revision: Union[str, None] = "0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── curador_medios — estado de revisión por canal ──
    op.add_column(
        "curador_medios",
        sa.Column(
            "estado_revision",
            sa.String(20),
            nullable=False,
            server_default="pendiente",
        ),
    )
    op.create_check_constraint(
        "ck_curador_medios_estado_revision",
        "curador_medios",
        "estado_revision IN ('pendiente','aprobado','rechazado')",
    )
    op.add_column(
        "curador_medios",
        sa.Column("motivo_rechazo", sa.Text(), nullable=True),
    )
    op.add_column(
        "curador_medios",
        sa.Column(
            "revisado_por",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
    )
    op.create_foreign_key(
        "fk_curador_medios_revisado_por",
        "curador_medios",
        "usuarios",
        ["revisado_por"],
        ["id"],
        ondelete="SET NULL",
    )
    op.add_column(
        "curador_medios",
        sa.Column(
            "revisado_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_curador_medios_estado_revision",
        "curador_medios",
        ["estado_revision"],
    )


def downgrade() -> None:
    op.drop_index("ix_curador_medios_estado_revision", table_name="curador_medios")
    op.drop_constraint(
        "fk_curador_medios_revisado_por", "curador_medios", type_="foreignkey"
    )
    op.drop_constraint(
        "ck_curador_medios_estado_revision", "curador_medios", type_="check"
    )
    op.drop_column("curador_medios", "revisado_at")
    op.drop_column("curador_medios", "revisado_por")
    op.drop_column("curador_medios", "motivo_rechazo")
    op.drop_column("curador_medios", "estado_revision")
