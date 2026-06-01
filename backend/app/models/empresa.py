from typing import TYPE_CHECKING

from sqlalchemy import ARRAY, String, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.unidade import Unidade
    from app.models.usuario import Usuario
    from app.models.projeto import Projeto


class Empresa(TimestampMixin, Base):
    __tablename__ = "empresas"

    nome: Mapped[str] = mapped_column(String(200), nullable=False)
    nome_fantasia: Mapped[str | None] = mapped_column(String(200))
    cnpj: Mapped[str] = mapped_column(String(18), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(254), nullable=False)
    telefone: Mapped[str | None] = mapped_column(String(20))
    cep: Mapped[str | None] = mapped_column(String(9))
    logradouro: Mapped[str | None] = mapped_column(String(300))
    numero: Mapped[str | None] = mapped_column(String(20))
    complemento: Mapped[str | None] = mapped_column(String(100))
    bairro: Mapped[str | None] = mapped_column(String(100))
    cidade: Mapped[str | None] = mapped_column(String(100))
    estado: Mapped[str | None] = mapped_column(String(2))
    horario_inicio: Mapped[str | None] = mapped_column(Time)
    horario_fim: Mapped[str | None] = mapped_column(Time)
    dias_funcionamento: Mapped[list[str] | None] = mapped_column(ARRAY(String))
    logo_url: Mapped[str | None] = mapped_column(String(500))

    unidades: Mapped[list["Unidade"]] = relationship(
        "Unidade", back_populates="empresa", cascade="all, delete-orphan"
    )
    usuarios: Mapped[list["Usuario"]] = relationship(
        "Usuario", back_populates="empresa"
    )
    projetos: Mapped[list["Projeto"]] = relationship(
        "Projeto", back_populates="empresa"
    )
