"""initial_schema

Revision ID: 85c1fedfb7c5
Revises:
Create Date: 2026-06-01 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "85c1fedfb7c5"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enums
    tipounidade = postgresql.ENUM(
        "fabrica", "centro_distribuicao", "escritorio", name="tipounidade"
    )
    tipounidade.create(op.get_bind(), checkfirst=True)

    roleusuario = postgresql.ENUM(
        "admin", "gerente", "operador", "visualizador", name="roleusuario"
    )
    roleusuario.create(op.get_bind(), checkfirst=True)

    statusprojeto = postgresql.ENUM(
        "rascunho",
        "aguardando_aprovacao",
        "em_producao",
        "concluido",
        "cancelado",
        name="statusprojeto",
    )
    statusprojeto.create(op.get_bind(), checkfirst=True)

    # Tabela empresas
    op.create_table(
        "empresas",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("nome", sa.String(200), nullable=False),
        sa.Column("nome_fantasia", sa.String(200), nullable=True),
        sa.Column("cnpj", sa.String(18), nullable=False),
        sa.Column("email", sa.String(254), nullable=False),
        sa.Column("telefone", sa.String(20), nullable=True),
        sa.Column("cep", sa.String(9), nullable=True),
        sa.Column("logradouro", sa.String(300), nullable=True),
        sa.Column("numero", sa.String(20), nullable=True),
        sa.Column("complemento", sa.String(100), nullable=True),
        sa.Column("bairro", sa.String(100), nullable=True),
        sa.Column("cidade", sa.String(100), nullable=True),
        sa.Column("estado", sa.String(2), nullable=True),
        sa.Column("horario_inicio", sa.Time(), nullable=True),
        sa.Column("horario_fim", sa.Time(), nullable=True),
        sa.Column("dias_funcionamento", sa.ARRAY(sa.String()), nullable=True),
        sa.Column("logo_url", sa.String(500), nullable=True),
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
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("cnpj"),
    )

    # Tabela unidades
    op.create_table(
        "unidades",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("empresa_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("nome", sa.String(200), nullable=False),
        sa.Column(
            postgresql.ENUM(
                "fabrica", "centro_distribuicao", "escritorio",
                name="tipounidade", create_type=False,
            ),
            name="tipo",
            nullable=False,
        ),
        sa.Column("codigo", sa.String(20), nullable=True),
        sa.Column("email", sa.String(254), nullable=True),
        sa.Column("telefone", sa.String(20), nullable=True),
        sa.Column("cep", sa.String(9), nullable=True),
        sa.Column("logradouro", sa.String(300), nullable=True),
        sa.Column("numero", sa.String(20), nullable=True),
        sa.Column("complemento", sa.String(100), nullable=True),
        sa.Column("bairro", sa.String(100), nullable=True),
        sa.Column("cidade", sa.String(100), nullable=True),
        sa.Column("estado", sa.String(2), nullable=True),
        sa.Column("is_sede", sa.Boolean(), nullable=False),
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
        sa.PrimaryKeyConstraint("id"),
    )

    # Tabela usuarios
    op.create_table(
        "usuarios",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("empresa_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("unidade_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("nome", sa.String(200), nullable=False),
        sa.Column("email", sa.String(254), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column(
            postgresql.ENUM(
                "admin", "gerente", "operador", "visualizador",
                name="roleusuario", create_type=False,
            ),
            name="role",
            nullable=False,
        ),
        sa.Column("telefone", sa.String(20), nullable=True),
        sa.Column("avatar_url", sa.String(500), nullable=True),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("must_change_password", sa.Boolean(), nullable=False),
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
        sa.ForeignKeyConstraint(["empresa_id"], ["empresas.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["unidade_id"], ["unidades.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )

    # Tabela refresh_tokens
    op.create_table(
        "refresh_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("usuario_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("token_hash", sa.String(255), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("user_agent", sa.String(500), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash"),
    )

    # Tabela projetos
    op.create_table(
        "projetos",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("empresa_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("unidade_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("criado_por_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("responsavel_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("codigo", sa.String(50), nullable=False),
        sa.Column("nome", sa.String(300), nullable=False),
        sa.Column("descricao", sa.Text(), nullable=True),
        sa.Column(
            postgresql.ENUM(
                "rascunho",
                "aguardando_aprovacao",
                "em_producao",
                "concluido",
                "cancelado",
                name="statusprojeto",
                create_type=False,
            ),
            name="status",
            nullable=False,
        ),
        sa.Column("cliente_nome", sa.String(200), nullable=True),
        sa.Column("cliente_contato", sa.String(200), nullable=True),
        sa.Column("data_entrada", sa.Date(), nullable=True),
        sa.Column("data_entrega_prevista", sa.Date(), nullable=True),
        sa.Column("data_entrega_real", sa.Date(), nullable=True),
        sa.Column("prioridade", sa.SmallInteger(), nullable=False),
        sa.Column("observacoes", sa.Text(), nullable=True),
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
        sa.ForeignKeyConstraint(["criado_por_id"], ["usuarios.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["empresa_id"], ["empresas.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["responsavel_id"], ["usuarios.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["unidade_id"], ["unidades.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("empresa_id", "codigo", name="uq_projeto_codigo_empresa"),
    )


def downgrade() -> None:
    op.drop_table("projetos")
    op.drop_table("refresh_tokens")
    op.drop_table("usuarios")
    op.drop_table("unidades")
    op.drop_table("empresas")
    op.execute("DROP TYPE IF EXISTS statusprojeto")
    op.execute("DROP TYPE IF EXISTS roleusuario")
    op.execute("DROP TYPE IF EXISTS tipounidade")
