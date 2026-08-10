"""add_conexao_instagram

Revision ID: f3a9c2b7d1e4
Revises: 85c1fedfb7c5
Create Date: 2026-08-10 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "f3a9c2b7d1e4"
down_revision: Union[str, None] = "85c1fedfb7c5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    statusconexaoinstagram = postgresql.ENUM(
        "initiated",
        "active",
        "failed",
        "expired",
        "inactive",
        "revoked",
        name="statusconexaoinstagram",
    )
    statusconexaoinstagram.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "conexoes_instagram",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("empresa_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("conectado_por_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("composio_connected_account_id", sa.String(64), nullable=False),
        sa.Column(
            postgresql.ENUM(
                "initiated",
                "active",
                "failed",
                "expired",
                "inactive",
                "revoked",
                name="statusconexaoinstagram",
                create_type=False,
            ),
            name="status",
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
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["empresa_id"], ["empresas.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["conectado_por_id"], ["usuarios.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("empresa_id"),
    )


def downgrade() -> None:
    op.drop_table("conexoes_instagram")
    op.execute("DROP TYPE IF EXISTS statusconexaoinstagram")
