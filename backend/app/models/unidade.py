import enum
import uuid
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.empresa import Empresa
    from app.models.usuario import Usuario
    from app.models.projeto import Projeto


class TipoUnidade(str, enum.Enum):
    FABRICA = "fabrica"
    CENTRO_DISTRIBUICAO = "centro_distribuicao"
    ESCRITORIO = "escritorio"


class Unidade(TimestampMixin, Base):
    __tablename__ = "unidades"

    empresa_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("empresas.id", ondelete="CASCADE"),
        nullable=False,
    )
    nome: Mapped[str] = mapped_column(sa.String(200), nullable=False)
    tipo: Mapped[TipoUnidade] = mapped_column(
        sa.Enum(TipoUnidade, name="tipounidade"), nullable=False
    )
    codigo: Mapped[str | None] = mapped_column(sa.String(20))
    email: Mapped[str | None] = mapped_column(sa.String(254))
    telefone: Mapped[str | None] = mapped_column(sa.String(20))
    cep: Mapped[str | None] = mapped_column(sa.String(9))
    logradouro: Mapped[str | None] = mapped_column(sa.String(300))
    numero: Mapped[str | None] = mapped_column(sa.String(20))
    complemento: Mapped[str | None] = mapped_column(sa.String(100))
    bairro: Mapped[str | None] = mapped_column(sa.String(100))
    cidade: Mapped[str | None] = mapped_column(sa.String(100))
    estado: Mapped[str | None] = mapped_column(sa.String(2))
    is_sede: Mapped[bool] = mapped_column(sa.Boolean, default=False, nullable=False)

    empresa: Mapped["Empresa"] = relationship("Empresa", back_populates="unidades")
    usuarios: Mapped[list["Usuario"]] = relationship(
        "Usuario", back_populates="unidade"
    )
    projetos: Mapped[list["Projeto"]] = relationship(
        "Projeto", back_populates="unidade"
    )
