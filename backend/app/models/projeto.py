import enum
import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.empresa import Empresa
    from app.models.unidade import Unidade
    from app.models.usuario import Usuario


class StatusProjeto(str, enum.Enum):
    RASCUNHO = "rascunho"
    AGUARDANDO_APROVACAO = "aguardando_aprovacao"
    EM_PRODUCAO = "em_producao"
    CONCLUIDO = "concluido"
    CANCELADO = "cancelado"


class Projeto(TimestampMixin, Base):
    __tablename__ = "projetos"

    empresa_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("empresas.id", ondelete="RESTRICT"),
        nullable=False,
    )
    unidade_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("unidades.id", ondelete="SET NULL"),
    )
    criado_por_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("usuarios.id", ondelete="SET NULL"),
    )
    responsavel_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("usuarios.id", ondelete="SET NULL"),
    )
    codigo: Mapped[str] = mapped_column(sa.String(50), nullable=False)
    nome: Mapped[str] = mapped_column(sa.String(300), nullable=False)
    descricao: Mapped[str | None] = mapped_column(sa.Text)
    status: Mapped[StatusProjeto] = mapped_column(
        sa.Enum(
            StatusProjeto,
            name="statusprojeto",
            values_callable=lambda enum_cls: [e.value for e in enum_cls],
        ),
        nullable=False,
        default=StatusProjeto.RASCUNHO,
    )
    cliente_nome: Mapped[str | None] = mapped_column(sa.String(200))
    cliente_contato: Mapped[str | None] = mapped_column(sa.String(200))
    data_entrada: Mapped[date | None] = mapped_column(sa.Date)
    data_entrega_prevista: Mapped[date | None] = mapped_column(sa.Date)
    data_entrega_real: Mapped[date | None] = mapped_column(sa.Date)
    prioridade: Mapped[int] = mapped_column(
        sa.SmallInteger, nullable=False, default=3
    )
    observacoes: Mapped[str | None] = mapped_column(sa.Text)

    __table_args__ = (
        sa.UniqueConstraint("empresa_id", "codigo", name="uq_projeto_codigo_empresa"),
    )

    empresa: Mapped["Empresa"] = relationship("Empresa", back_populates="projetos")
    unidade: Mapped["Unidade | None"] = relationship("Unidade", back_populates="projetos")
    criado_por: Mapped["Usuario | None"] = relationship(
        "Usuario", foreign_keys=[criado_por_id]
    )
    responsavel: Mapped["Usuario | None"] = relationship(
        "Usuario", foreign_keys=[responsavel_id]
    )
