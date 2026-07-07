import enum
import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.empresa import Empresa


class TipoMaterial(str, enum.Enum):
    CHAPA = "chapa"
    FITA_BORDA = "fita_borda"
    FERRAGEM = "ferragem"
    OUTRO = "outro"


class Material(TimestampMixin, Base):
    """Biblioteca de materiais da empresa (chapas MDF, fitas, ferragens)."""

    __tablename__ = "materiais"

    empresa_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("empresas.id", ondelete="RESTRICT"),
        nullable=False,
    )
    nome: Mapped[str] = mapped_column(sa.String(200), nullable=False)
    codigo: Mapped[str | None] = mapped_column(sa.String(50))
    tipo: Mapped[TipoMaterial] = mapped_column(
        sa.Enum(
            TipoMaterial,
            name="tipomaterial",
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
    )
    # Dimensões da chapa/fita em milímetros
    espessura_mm: Mapped[int | None] = mapped_column(sa.SmallInteger)
    largura_mm: Mapped[int | None] = mapped_column(sa.Integer)
    comprimento_mm: Mapped[int | None] = mapped_column(sa.Integer)
    cor: Mapped[str | None] = mapped_column(sa.String(100))
    # un = unidade, m2 = metro quadrado, m = metro linear
    unidade_medida: Mapped[str] = mapped_column(
        sa.String(10), nullable=False, default="un"
    )
    preco_unitario: Mapped[Decimal | None] = mapped_column(sa.Numeric(12, 2))
    observacoes: Mapped[str | None] = mapped_column(sa.Text)

    __table_args__ = (
        sa.UniqueConstraint("empresa_id", "codigo", name="uq_material_codigo_empresa"),
    )

    empresa: Mapped["Empresa"] = relationship("Empresa")
