"""paquetes_creditos table + seed Stripe/config USD params

Revision ID: 0006
Revises: 0005
Create Date: 2026-07-07
"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Parámetros USD / Stripe que se seedean en esta migración.
PARAMETROS_USD = [
    {
        "clave": "precio_credito_individual_usd",
        "valor": "2.00",
        "descripcion": "Precio neto de 1 crédito suelto en USD",
    },
    {
        "clave": "comision_resuena_pct",
        "valor": "50",
        "descripcion": "Comisión % que retiene Resuena al curador",
    },
    {
        "clave": "stripe_pct_nacional",
        "valor": "0.036",
        "descripcion": "Fee % Stripe tarjeta nacional MX",
    },
    {
        "clave": "stripe_fixed_usd",
        "valor": "0.17",
        "descripcion": "Fee fijo Stripe por transacción (en USD)",
    },
    {
        "clave": "stripe_pct_internacional",
        "valor": "0.005",
        "descripcion": "Fee adicional % tarjeta internacional",
    },
    {
        "clave": "stripe_pct_conversion_moneda",
        "valor": "0.02",
        "descripcion": "Fee adicional % conversión de moneda",
    },
    {
        "clave": "stripe_pct_oxxo",
        "valor": "0.04",
        "descripcion": "Fee % OXXO Pay (reemplaza nacional)",
    },
    {
        "clave": "stripe_fixed_disputa_usd",
        "valor": "8.57",
        "descripcion": "Fee fijo USD por disputa ($150 MXN)",
    },
    {
        "clave": "stripe_escenario_default",
        "valor": "nacional",
        "descripcion": "Escenario default: nacional|internacional|oxxo",
    },
]


def upgrade() -> None:
    # ── Tabla paquetes_creditos (reemplaza los paquetes hardcodeados) ──
    op.create_table(
        "paquetes_creditos",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("nombre", sa.String(length=255), nullable=False),
        sa.Column("cantidad_creditos", sa.Integer(), nullable=False),
        sa.Column(
            "precio_total_usd",
            sa.Numeric(precision=10, scale=2),
            nullable=False,
        ),
        sa.Column("comision_pct", sa.Integer(), nullable=True),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column(
            "activo",
            sa.Boolean(),
            server_default="true",
            nullable=False,
        ),
        sa.Column(
            "visible",
            sa.Boolean(),
            server_default="true",
            nullable=False,
        ),
        sa.Column(
            "destacado",
            sa.Boolean(),
            server_default="false",
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_paquetes_creditos")),
        sa.CheckConstraint(
            "cantidad_creditos > 0",
            name=op.f("ck_paquetes_creditos_cantidad_positiva"),
        ),
        sa.CheckConstraint(
            "precio_total_usd > 0",
            name=op.f("ck_paquetes_creditos_precio_positivo"),
        ),
    )
    op.create_index(
        "idx_paquetes_creditos_activo_visible",
        "paquetes_creditos",
        ["activo", "visible"],
        unique=False,
    )

    # ── Seed de parámetros USD / Stripe (ON CONFLICT idempotente) ──
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
            for p in PARAMETROS_USD
        ],
    )


def downgrade() -> None:
    # ── Eliminar parámetros USD / Stripe seedeados ──
    op.execute(
        "DELETE FROM parametros_config WHERE clave IN ("
        + ", ".join(f"'{p['clave']}'" for p in PARAMETROS_USD)
        + ")"
    )

    # ── Eliminar tabla paquetes_creditos ──
    op.drop_index(
        "idx_paquetes_creditos_activo_visible",
        table_name="paquetes_creditos",
    )
    op.drop_table("paquetes_creditos")
