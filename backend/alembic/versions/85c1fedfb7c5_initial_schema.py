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
    conn = op.get_bind()

    # Criar ENUMs via SQL puro (idempotente)
    conn.execute(sa.text("CREATE TYPE tipounidade AS ENUM ('fabrica', 'centro_distribuicao', 'escritorio')"))
    conn.execute(sa.text("CREATE TYPE roleusuario AS ENUM ('admin', 'gerente', 'operador', 'visualizador')"))
    conn.execute(sa.text("CREATE TYPE statusprojeto AS ENUM ('rascunho', 'aguardando_aprovacao', 'em_producao', 'concluido', 'cancelado')"))

    conn.execute(sa.text("""
        CREATE TABLE empresas (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            nome VARCHAR(200) NOT NULL,
            nome_fantasia VARCHAR(200),
            cnpj VARCHAR(18) NOT NULL UNIQUE,
            email VARCHAR(254) NOT NULL,
            telefone VARCHAR(20),
            cep VARCHAR(9),
            logradouro VARCHAR(300),
            numero VARCHAR(20),
            complemento VARCHAR(100),
            bairro VARCHAR(100),
            cidade VARCHAR(100),
            estado VARCHAR(2),
            horario_inicio TIME,
            horario_fim TIME,
            dias_funcionamento VARCHAR[],
            logo_url VARCHAR(500),
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            is_active BOOLEAN NOT NULL DEFAULT TRUE
        )
    """))

    conn.execute(sa.text("""
        CREATE TABLE unidades (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            empresa_id UUID NOT NULL REFERENCES empresas(id) ON DELETE CASCADE,
            nome VARCHAR(200) NOT NULL,
            tipo tipounidade NOT NULL,
            codigo VARCHAR(20),
            email VARCHAR(254),
            telefone VARCHAR(20),
            cep VARCHAR(9),
            logradouro VARCHAR(300),
            numero VARCHAR(20),
            complemento VARCHAR(100),
            bairro VARCHAR(100),
            cidade VARCHAR(100),
            estado VARCHAR(2),
            is_sede BOOLEAN NOT NULL DEFAULT FALSE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            is_active BOOLEAN NOT NULL DEFAULT TRUE
        )
    """))

    conn.execute(sa.text("""
        CREATE TABLE usuarios (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            empresa_id UUID NOT NULL REFERENCES empresas(id) ON DELETE RESTRICT,
            unidade_id UUID REFERENCES unidades(id) ON DELETE SET NULL,
            nome VARCHAR(200) NOT NULL,
            email VARCHAR(254) NOT NULL UNIQUE,
            hashed_password VARCHAR(255) NOT NULL,
            role roleusuario NOT NULL,
            telefone VARCHAR(20),
            avatar_url VARCHAR(500),
            last_login_at TIMESTAMPTZ,
            must_change_password BOOLEAN NOT NULL DEFAULT FALSE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            is_active BOOLEAN NOT NULL DEFAULT TRUE
        )
    """))

    conn.execute(sa.text("""
        CREATE TABLE refresh_tokens (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            usuario_id UUID NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
            token_hash VARCHAR(255) NOT NULL UNIQUE,
            expires_at TIMESTAMPTZ NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            revoked_at TIMESTAMPTZ,
            user_agent VARCHAR(500),
            ip_address VARCHAR(45)
        )
    """))

    conn.execute(sa.text("""
        CREATE TABLE projetos (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            empresa_id UUID NOT NULL REFERENCES empresas(id) ON DELETE RESTRICT,
            unidade_id UUID REFERENCES unidades(id) ON DELETE SET NULL,
            criado_por_id UUID REFERENCES usuarios(id) ON DELETE SET NULL,
            responsavel_id UUID REFERENCES usuarios(id) ON DELETE SET NULL,
            codigo VARCHAR(50) NOT NULL,
            nome VARCHAR(300) NOT NULL,
            descricao TEXT,
            status statusprojeto NOT NULL DEFAULT 'rascunho',
            cliente_nome VARCHAR(200),
            cliente_contato VARCHAR(200),
            data_entrada DATE,
            data_entrega_prevista DATE,
            data_entrega_real DATE,
            prioridade SMALLINT NOT NULL DEFAULT 3,
            observacoes TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            UNIQUE(empresa_id, codigo)
        )
    """))

    # Registrar a migração na tabela de controle do Alembic
    # (feito automaticamente pelo alembic)


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("DROP TABLE IF EXISTS projetos"))
    conn.execute(sa.text("DROP TABLE IF EXISTS refresh_tokens"))
    conn.execute(sa.text("DROP TABLE IF EXISTS usuarios"))
    conn.execute(sa.text("DROP TABLE IF EXISTS unidades"))
    conn.execute(sa.text("DROP TABLE IF EXISTS empresas"))
    conn.execute(sa.text("DROP TYPE IF EXISTS statusprojeto"))
    conn.execute(sa.text("DROP TYPE IF EXISTS roleusuario"))
    conn.execute(sa.text("DROP TYPE IF EXISTS tipounidade"))
