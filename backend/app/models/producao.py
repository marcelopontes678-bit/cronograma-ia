"""Dominio de producao (cronograma/Gantt, Kanban, carga por operador) do
gestori -- integra o modulo Producao (antes 100% mock no frontend) ao
Projeto ja existente. Reagendamento em cascata e caminho critico
continuam sendo calculados no frontend (funcoes puras sobre o array de
tarefas ja carregado); aqui so persistimos o estado."""
import enum
import uuid
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, Enum, ForeignKey, Integer, SmallInteger, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.projeto import Projeto
    from app.models.usuario import Usuario


class TipoVinculo(str, enum.Enum):
    FS = "FS"  # Finish-to-Start
    SS = "SS"  # Start-to-Start


class StatusTarefa(str, enum.Enum):
    NAO_INICIADA = "nao_iniciada"
    EM_ANDAMENTO = "em_andamento"
    CONCLUIDA = "concluida"
    BLOQUEADA = "bloqueada"
    ATRASADA = "atrasada"
    EM_RISCO = "em_risco"


class TarefaCronograma(TimestampMixin, Base):
    __tablename__ = "tarefas_cronograma"

    projeto_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projetos.id", ondelete="CASCADE"), nullable=False
    )
    operador_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="SET NULL")
    )
    predecessora_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tarefas_cronograma.id", ondelete="SET NULL")
    )
    nome: Mapped[str] = mapped_column(String(300), nullable=False)
    descricao: Mapped[str | None] = mapped_column(Text)
    tipo_vinculo: Mapped[TipoVinculo] = mapped_column(
        Enum(
            TipoVinculo, name="tipovinculo", values_callable=lambda e: [m.value for m in e]
        ),
        nullable=False,
        default=TipoVinculo.FS,
    )
    lag_dias: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    duracao_dias: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    data_inicio: Mapped[date] = mapped_column(Date, nullable=False)
    data_fim: Mapped[date] = mapped_column(Date, nullable=False)
    baseline_inicio: Mapped[date | None] = mapped_column(Date)
    baseline_fim: Mapped[date | None] = mapped_column(Date)
    percentual_concluido: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    status: Mapped[StatusTarefa] = mapped_column(
        Enum(
            StatusTarefa, name="statustarefa", values_callable=lambda e: [m.value for m in e]
        ),
        nullable=False,
        default=StatusTarefa.NAO_INICIADA,
    )
    folga: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    eh_caminho_critico: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    observacoes: Mapped[str | None] = mapped_column(Text)
    historico: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        doc=(
            "Lista de eventos {id, data, acao, usuario, observacao} -- sempre lida/"
            "escrita como unidade, mesmo padrao ja usado em OrcamentoJob.ambientes."
        ),
    )

    projeto: Mapped["Projeto"] = relationship("Projeto")
    operador: Mapped["Usuario | None"] = relationship("Usuario", foreign_keys=[operador_id])


class AusenciaOperador(TimestampMixin, Base):
    __tablename__ = "ausencias_operador"

    usuario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False
    )
    data_inicio: Mapped[date] = mapped_column(Date, nullable=False)
    data_fim: Mapped[date] = mapped_column(Date, nullable=False)
    motivo: Mapped[str] = mapped_column(String(300), nullable=False)

    usuario: Mapped["Usuario"] = relationship("Usuario")
