"""invitaciones de sello — tabla invitaciones_sello

Revision ID: 0005
Revises: 0004
Create Date: 2026-06-29
"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enum nuevo para el estado de la invitación. create_type=False evita que
    # create_table lo emita una segunda vez (lo creamos explícitamente aquí).
    estado = postgresql.ENUM(
        "pendiente",
        "aceptada",
        "rechazada",
        name="estado_invitacion_sello",
        create_type=False,
    )
    estado.create(op.get_bind(), checkfirst=True)

    # rol_sello_artista ya existe (creado en 0001); no recrear el tipo.
    rol = postgresql.ENUM(name="rol_sello_artista", create_type=False)

    op.create_table(
        "invitaciones_sello",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("sello_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("correo", sa.String(length=255), nullable=False),
        sa.Column(
            "invitado_artista_id", postgresql.UUID(as_uuid=True), nullable=True
        ),
        sa.Column("rol", rol, nullable=False),
        sa.Column("invitado_por", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("token", sa.String(length=255), nullable=False),
        sa.Column(
            "estado",
            estado,
            server_default="pendiente",
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_invitaciones_sello"),
        sa.ForeignKeyConstraint(
            ["sello_id"],
            ["sellos_discograficos.id"],
            name="fk_invitaciones_sello_sello_id_sellos_discograficos",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["invitado_artista_id"],
            ["usuarios.id"],
            name="fk_invitaciones_sello_invitado_artista_id_usuarios",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["invitado_por"],
            ["usuarios.id"],
            name="fk_invitaciones_sello_invitado_por_usuarios",
            ondelete="SET NULL",
        ),
        sa.UniqueConstraint("token", name="uq_invitaciones_sello_token"),
    )
    op.create_index(
        "idx_invitaciones_sello_correo",
        "invitaciones_sello",
        ["correo", "estado"],
    )


def downgrade() -> None:
    op.drop_index(
        "idx_invitaciones_sello_correo", table_name="invitaciones_sello"
    )
    op.drop_table("invitaciones_sello")
    postgresql.ENUM(name="estado_invitacion_sello").drop(
        op.get_bind(), checkfirst=True
    )
