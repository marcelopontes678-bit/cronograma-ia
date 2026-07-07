"""engenharia_manual: materiais, ambientes, modulos, pecas

Revision ID: a1b2c3d4e5f6
Revises: 85c1fedfb7c5
Create Date: 2026-07-07 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "85c1fedfb7c5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()

    conn.execute(sa.text(
        "CREATE TYPE tipomaterial AS ENUM ('chapa', 'fita_borda', 'ferragem', 'outro')"
    ))

    conn.execute(sa.text("""
        CREATE TABLE materiais (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            empresa_id UUID NOT NULL REFERENCES empresas(id) ON DELETE RESTRICT,
            nome VARCHAR(200) NOT NULL,
            codigo VARCHAR(50),
            tipo tipomaterial NOT NULL,
            espessura_mm SMALLINT,
            largura_mm INTEGER,
            comprimento_mm INTEGER,
            cor VARCHAR(100),
            unidade_medida VARCHAR(10) NOT NULL DEFAULT 'un',
            preco_unitario NUMERIC(12, 2),
            observacoes TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            is_active BOOLEAN NOT NULL DEFAULT true,
            CONSTRAINT uq_material_codigo_empresa UNIQUE (empresa_id, codigo)
        )
    """))

    conn.execute(sa.text("""
        CREATE TABLE ambientes (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            projeto_id UUID NOT NULL REFERENCES projetos(id) ON DELETE CASCADE,
            nome VARCHAR(200) NOT NULL,
            descricao TEXT,
            ordem SMALLINT NOT NULL DEFAULT 0,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            is_active BOOLEAN NOT NULL DEFAULT true
        )
    """))

    conn.execute(sa.text("""
        CREATE TABLE modulos (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            ambiente_id UUID NOT NULL REFERENCES ambientes(id) ON DELETE CASCADE,
            nome VARCHAR(200) NOT NULL,
            codigo VARCHAR(50),
            largura_mm INTEGER,
            altura_mm INTEGER,
            profundidade_mm INTEGER,
            quantidade INTEGER NOT NULL DEFAULT 1,
            descricao TEXT,
            ordem SMALLINT NOT NULL DEFAULT 0,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            is_active BOOLEAN NOT NULL DEFAULT true
        )
    """))

    conn.execute(sa.text("""
        CREATE TABLE pecas (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            modulo_id UUID NOT NULL REFERENCES modulos(id) ON DELETE CASCADE,
            material_id UUID REFERENCES materiais(id) ON DELETE SET NULL,
            nome VARCHAR(200) NOT NULL,
            comprimento_mm INTEGER NOT NULL,
            largura_mm INTEGER NOT NULL,
            quantidade INTEGER NOT NULL DEFAULT 1,
            veio BOOLEAN NOT NULL DEFAULT false,
            fita_c1 BOOLEAN NOT NULL DEFAULT false,
            fita_c2 BOOLEAN NOT NULL DEFAULT false,
            fita_l1 BOOLEAN NOT NULL DEFAULT false,
            fita_l2 BOOLEAN NOT NULL DEFAULT false,
            observacoes TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            is_active BOOLEAN NOT NULL DEFAULT true
        )
    """))

    conn.execute(sa.text("CREATE INDEX ix_materiais_empresa ON materiais (empresa_id)"))
    conn.execute(sa.text("CREATE INDEX ix_ambientes_projeto ON ambientes (projeto_id)"))
    conn.execute(sa.text("CREATE INDEX ix_modulos_ambiente ON modulos (ambiente_id)"))
    conn.execute(sa.text("CREATE INDEX ix_pecas_modulo ON pecas (modulo_id)"))


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("DROP TABLE IF EXISTS pecas"))
    conn.execute(sa.text("DROP TABLE IF EXISTS modulos"))
    conn.execute(sa.text("DROP TABLE IF EXISTS ambientes"))
    conn.execute(sa.text("DROP TABLE IF EXISTS materiais"))
    conn.execute(sa.text("DROP TYPE IF EXISTS tipomaterial"))
