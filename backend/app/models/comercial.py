"""Dominio comercial do ERP Gestori (CRM, orcamentos comerciais, fichas
tecnicas, estoque, financeiro) -- distinto do dominio de orcamento via
Vision (`OrcamentoJob`/MARC) em `orcamento.py`. "Orcamento" aqui significa
proposta comercial pro cliente (numero, itens, subtotal, parcelas), nao
extracao de PDF -- por isso as tabelas ficam com prefixo proprio
(`orcamentos_comerciais`) para nunca colidir nome com `orcamento_jobs`."""
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.empresa import Empresa


class Cliente(TimestampMixin, Base):
    """Lead/cliente do CRM -- um por empresa, nao compartilhado entre
    tenants."""

    __tablename__ = "clientes"

    empresa_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False
    )
    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    empresa_cliente: Mapped[str | None] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    telefone: Mapped[str] = mapped_column(String(50), nullable=False)
    origem: Mapped[str] = mapped_column(String(30), nullable=False, default="outro")
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="lead")
    valor_estimado: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    data_entrada: Mapped[str] = mapped_column(String(10), nullable=False)
    data_ultima_atualizacao: Mapped[str] = mapped_column(String(10), nullable=False)
    observacoes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    responsavel_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="SET NULL")
    )

    empresa: Mapped["Empresa"] = relationship("Empresa")


class OrcamentoComercial(TimestampMixin, Base):
    """Proposta comercial enviada ao cliente -- nao confundir com
    `OrcamentoJob` (extracao via Vision). `itens` e `parcelas` ficam em
    JSONB pelo mesmo racional de `OrcamentoJob.ambientes`: sempre lidos/
    escritos como arvore inteira, nunca item a item."""

    __tablename__ = "orcamentos_comerciais"

    empresa_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False
    )
    numero: Mapped[str] = mapped_column(String(50), nullable=False)
    cliente_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clientes.id", ondelete="SET NULL")
    )
    cliente_nome: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="rascunho")
    data_criacao: Mapped[str] = mapped_column(String(10), nullable=False)
    data_validade: Mapped[str] = mapped_column(String(10), nullable=False)
    itens: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    subtotal: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    desconto: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    total: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    margem_media: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False, default=0)
    parcelas: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    observacoes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    fichas_tecnicas_ids: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)

    empresa: Mapped["Empresa"] = relationship("Empresa")
    cliente: Mapped["Cliente | None"] = relationship("Cliente")


class FichaTecnica(TimestampMixin, Base):
    __tablename__ = "fichas_tecnicas"

    empresa_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False
    )
    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    categoria: Mapped[str] = mapped_column(String(100), nullable=False)
    descricao: Mapped[str] = mapped_column(Text, nullable=False, default="")
    tempo_producao_horas: Mapped[float] = mapped_column(Numeric(8, 2), nullable=False, default=0)
    custo_materiais: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    custo_mao_obra: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    insumos: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    imagem_url: Mapped[str | None] = mapped_column(String(1000))
    versao: Mapped[int] = mapped_column(default=1, nullable=False)

    empresa: Mapped["Empresa"] = relationship("Empresa")

    @property
    def custo_total(self) -> float:
        """Nunca persistido -- sempre derivado de custo_materiais +
        custo_mao_obra, pra nao ter dois valores que podem divergir."""
        return float(self.custo_materiais) + float(self.custo_mao_obra)


class ItemEstoque(TimestampMixin, Base):
    __tablename__ = "itens_estoque"

    empresa_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False
    )
    codigo: Mapped[str] = mapped_column(String(50), nullable=False)
    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    categoria: Mapped[str] = mapped_column(String(30), nullable=False)
    unidade: Mapped[str] = mapped_column(String(20), nullable=False)
    quantidade_atual: Mapped[float] = mapped_column(Numeric(12, 3), nullable=False, default=0)
    quantidade_minima: Mapped[float] = mapped_column(Numeric(12, 3), nullable=False, default=0)
    quantidade_reservada: Mapped[float] = mapped_column(Numeric(12, 3), nullable=False, default=0)
    custo_unitario: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    fornecedor: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    localizacao: Mapped[str] = mapped_column(String(255), nullable=False, default="")

    empresa: Mapped["Empresa"] = relationship("Empresa")
    movimentacoes: Mapped[list["MovimentacaoEstoque"]] = relationship(
        "MovimentacaoEstoque", back_populates="item", cascade="all, delete-orphan"
    )


class MovimentacaoEstoque(TimestampMixin, Base):
    __tablename__ = "movimentacoes_estoque"

    empresa_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False
    )
    item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("itens_estoque.id", ondelete="CASCADE"), nullable=False
    )
    tipo: Mapped[str] = mapped_column(String(20), nullable=False)
    quantidade: Mapped[float] = mapped_column(Numeric(12, 3), nullable=False)
    referencia: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    usuario_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="SET NULL")
    )

    empresa: Mapped["Empresa"] = relationship("Empresa")
    item: Mapped["ItemEstoque"] = relationship("ItemEstoque", back_populates="movimentacoes")


class LancamentoFinanceiro(TimestampMixin, Base):
    __tablename__ = "lancamentos_financeiros"

    empresa_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False
    )
    tipo: Mapped[str] = mapped_column(String(20), nullable=False)
    categoria: Mapped[str] = mapped_column(String(100), nullable=False)
    descricao: Mapped[str] = mapped_column(String(500), nullable=False)
    valor: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    data: Mapped[str] = mapped_column(String(10), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="previsto")
    orcamento_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orcamentos_comerciais.id", ondelete="SET NULL")
    )

    empresa: Mapped["Empresa"] = relationship("Empresa")
