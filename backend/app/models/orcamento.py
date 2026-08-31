import enum
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.empresa import Empresa
    from app.models.projeto import Projeto
    from app.models.usuario import Usuario


class StatusOrcamentoJob(str, enum.Enum):
    PROCESSANDO = "processando"
    AGUARDANDO_REVISAO = "aguardando_revisao"
    CONFIRMADO = "confirmado"
    ERRO = "erro"


class PreferenciasGlobais(TimestampMixin, Base):
    """Diretrizes padrao da fabrica usadas pelo agente extrator MARC para
    inferir especificacoes que o desenho nao deixa explicitas -- uma por
    empresa (nao por usuario como no protótipo standalone original: sao
    diretrizes de producao da fabrica, nao preferencia pessoal)."""

    __tablename__ = "preferencias_globais"

    empresa_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("empresas.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    configuracao: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        doc=(
            "Espelha api/schemas/preferencias.py::PreferenciasGlobais (sem empresa_id): "
            "espessuras, ferragens, metodo_uniao, fixacao_fundo, acabamento_interno_padrao, "
            "regra_fundo_exposto_forca_cor_caixaria, regra_apoio_por_ambiente, "
            "faixas_dobradicas_por_altura, profundidade_padrao_por_tipo_mm."
        ),
    )

    empresa: Mapped["Empresa"] = relationship("Empresa")


class RegraAprendida(TimestampMixin, Base):
    """Correcao em linguagem natural do marceneiro, normalizada e injetada
    no system prompt do MARC nas proximas extracoes -- nunca apaga do
    historico, so desativa (soft delete via is_active do TimestampMixin)."""

    __tablename__ = "regras_aprendidas"

    empresa_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False
    )
    usuario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True
    )
    instrucao_original: Mapped[str] = mapped_column(Text, nullable=False)
    regra_normalizada: Mapped[str] = mapped_column(Text, nullable=False)
    origem_job_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orcamento_jobs.id", ondelete="SET NULL")
    )
    origem_modulo_id: Mapped[str | None] = mapped_column(String(50))

    empresa: Mapped["Empresa"] = relationship("Empresa")
    usuario: Mapped["Usuario | None"] = relationship("Usuario")


class OrcamentoJob(TimestampMixin, Base):
    """Um job de extracao via Claude Vision (persona MARC). A arvore
    ambientes->modulos inteira fica em `ambientes` (JSONB) -- e sempre lida/
    escrita como unidade pelo vision_extractor.py/pricing_service.py, e o
    patch parcial de modulo (correcao humana) ja faz merge raso em JSON, sem
    ganho em normalizar em tabelas separadas agora (ver plano de integracao,
    Fase 1)."""

    __tablename__ = "orcamento_jobs"

    empresa_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False
    )
    usuario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True
    )
    projeto_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projetos.id", ondelete="SET NULL")
    )
    arquivo_origem: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[StatusOrcamentoJob] = mapped_column(
        Enum(
            StatusOrcamentoJob,
            name="statusorcamentojob",
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,
        default=StatusOrcamentoJob.PROCESSANDO,
    )
    ambientes: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    avisos: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)

    empresa: Mapped["Empresa"] = relationship("Empresa")
    usuario: Mapped["Usuario | None"] = relationship("Usuario")
    projeto: Mapped["Projeto | None"] = relationship("Projeto")
