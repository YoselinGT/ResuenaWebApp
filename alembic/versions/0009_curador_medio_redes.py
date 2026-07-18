"""curador_medio_redes — redes sociales por canal

Revision ID: 0009
Revises: 0008
Create Date: 2026-07-10
"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0009"
down_revision: Union[str, None] = "0008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "curador_medio_redes",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "medio_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("curador_medios.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("tipo", sa.String(20), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column(
            "es_principal",
            sa.Boolean(),
            nullable=False,
            server_default="false",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )
    op.create_check_constraint(
        "tipo",
        "curador_medio_redes",
        (
            "tipo IN ('instagram','tiktok','youtube','spotify','facebook',"
            "'twitter','soundcloud','bandcamp','website','otro')"
        ),
    )
    op.create_index(
        "ix_curador_medio_redes_medio_id",
        "curador_medio_redes",
        ["medio_id"],
    )

    # Migrar URL existente de curador_medios → curador_medio_redes
    # Mapear TipoMedio → TipoRedSocial para valores que no coinciden
    op.execute("""
        INSERT INTO curador_medio_redes (medio_id, tipo, url, es_principal)
        SELECT
            id,
            CASE tipo::text
                WHEN 'playlist' THEN 'spotify'
                WHEN 'blog'     THEN 'website'
                WHEN 'radio'    THEN 'website'
                WHEN 'eventos'  THEN 'website'
                ELSE tipo::text
            END,
            url,
            true
        FROM curador_medios
        WHERE url IS NOT NULL AND url != ''
    """)


def downgrade() -> None:
    op.drop_index("ix_curador_medio_redes_medio_id", table_name="curador_medio_redes")
    op.drop_constraint(
        "tipo", "curador_medio_redes", type_="check"
    )
    op.drop_table("curador_medio_redes")
