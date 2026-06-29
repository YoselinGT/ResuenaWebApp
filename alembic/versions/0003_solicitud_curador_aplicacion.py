"""solicitud curador — campos de aplicación (tipo_profesional, url_portfolio)

Revision ID: 0003
Revises: 0002
Create Date: 2026-06-28
"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "solicitudes_curador",
        sa.Column("tipo_profesional", sa.String(length=50), nullable=True),
    )
    op.add_column(
        "solicitudes_curador",
        sa.Column("url_portfolio", sa.String(length=500), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("solicitudes_curador", "url_portfolio")
    op.drop_column("solicitudes_curador", "tipo_profesional")
