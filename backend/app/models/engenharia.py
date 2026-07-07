"""Estrutura de produto (engenharia manual): Projeto → Ambiente → Módulo → Peça."""
import uuid
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.material import Material
    from app.models.projeto import Projeto


class Ambiente(TimestampMixin, Base):
    """Ambiente do projeto (ex.: Cozinha, Dormitório casal)."""

    __tablename__ = "ambientes"

    projeto_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("projetos.id", ondelete="CASCADE"),
        nullable=False,
    )
    nome: Mapped[str] = mapped_column(sa.String(200), nullable=False)
    descricao: Mapped[str | None] = mapped_column(sa.Text)
    ordem: Mapped[int] = mapped_column(sa.SmallInteger, nullable=False, default=0)

    projeto: Mapped["Projeto"] = relationship("Projeto", back_populates="ambientes")
    modulos: Mapped[list["Modulo"]] = relationship(
        "Modulo",
        back_populates="ambiente",
        cascade="all, delete-orphan",
        order_by="Modulo.ordem",
    )


class Modulo(TimestampMixin, Base):
    """Módulo do ambiente (ex.: Armário superior 800mm, Bancada)."""

    __tablename__ = "modulos"

    ambiente_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("ambientes.id", ondelete="CASCADE"),
        nullable=False,
    )
    nome: Mapped[str] = mapped_column(sa.String(200), nullable=False)
    codigo: Mapped[str | None] = mapped_column(sa.String(50))
    largura_mm: Mapped[int | None] = mapped_column(sa.Integer)
    altura_mm: Mapped[int | None] = mapped_column(sa.Integer)
    profundidade_mm: Mapped[int | None] = mapped_column(sa.Integer)
    quantidade: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=1)
    descricao: Mapped[str | None] = mapped_column(sa.Text)
    ordem: Mapped[int] = mapped_column(sa.SmallInteger, nullable=False, default=0)

    ambiente: Mapped["Ambiente"] = relationship("Ambiente", back_populates="modulos")
    pecas: Mapped[list["Peca"]] = relationship(
        "Peca", back_populates="modulo", cascade="all, delete-orphan"
    )


class Peca(TimestampMixin, Base):
    """Peça de um módulo (ex.: lateral, porta, prateleira) — base da lista de corte."""

    __tablename__ = "pecas"

    modulo_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("modulos.id", ondelete="CASCADE"),
        nullable=False,
    )
    material_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("materiais.id", ondelete="SET NULL"),
    )
    nome: Mapped[str] = mapped_column(sa.String(200), nullable=False)
    comprimento_mm: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    largura_mm: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    quantidade: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=1)
    # Respeitar o sentido do veio da madeira no plano de corte
    veio: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, default=False)
    # Fita de borda em cada lado: comprimento 1/2, largura 1/2
    fita_c1: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, default=False)
    fita_c2: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, default=False)
    fita_l1: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, default=False)
    fita_l2: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, default=False)
    observacoes: Mapped[str | None] = mapped_column(sa.Text)

    modulo: Mapped["Modulo"] = relationship("Modulo", back_populates="pecas")
    material: Mapped["Material | None"] = relationship("Material")
