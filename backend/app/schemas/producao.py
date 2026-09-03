import uuid
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator

from app.models.producao import StatusTarefa, TipoVinculo
from app.models.projeto import StatusProducao


class HistoricoTarefaEntry(BaseModel):
    id: str
    data: str
    acao: str
    usuario: str
    observacao: Optional[str] = None


class TarefaCronogramaBase(BaseModel):
    nome: str
    descricao: Optional[str] = None
    operador_id: Optional[uuid.UUID] = None
    predecessora_id: Optional[uuid.UUID] = None
    tipo_vinculo: TipoVinculo = TipoVinculo.FS
    lag_dias: int = 0
    duracao_dias: int = 1
    data_inicio: date
    data_fim: date
    baseline_inicio: Optional[date] = None
    baseline_fim: Optional[date] = None
    percentual_concluido: int = 0
    status: StatusTarefa = StatusTarefa.NAO_INICIADA
    observacoes: Optional[str] = None

    @field_validator("percentual_concluido")
    @classmethod
    def validate_percentual(cls, v: int) -> int:
        if not 0 <= v <= 100:
            raise ValueError("percentual_concluido deve ser entre 0 e 100")
        return v


class TarefaCronogramaCreate(TarefaCronogramaBase):
    pass


class TarefaCronogramaUpdate(BaseModel):
    nome: Optional[str] = None
    descricao: Optional[str] = None
    operador_id: Optional[uuid.UUID] = None
    predecessora_id: Optional[uuid.UUID] = None
    tipo_vinculo: Optional[TipoVinculo] = None
    lag_dias: Optional[int] = None
    duracao_dias: Optional[int] = None
    data_inicio: Optional[date] = None
    data_fim: Optional[date] = None
    baseline_inicio: Optional[date] = None
    baseline_fim: Optional[date] = None
    percentual_concluido: Optional[int] = None
    status: Optional[StatusTarefa] = None
    folga: Optional[int] = None
    eh_caminho_critico: Optional[bool] = None
    observacoes: Optional[str] = None
    # Anexa um evento ao historico, em vez de substituir a lista inteira
    # -- o service concatena, nunca sobrescreve.
    novo_evento_historico: Optional[HistoricoTarefaEntry] = None

    @field_validator("percentual_concluido")
    @classmethod
    def validate_percentual(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and not 0 <= v <= 100:
            raise ValueError("percentual_concluido deve ser entre 0 e 100")
        return v


class TarefaCronogramaResponse(TarefaCronogramaBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    projeto_id: uuid.UUID
    folga: int
    eh_caminho_critico: bool
    historico: list[HistoricoTarefaEntry]
    created_at: datetime
    updated_at: datetime


class AusenciaOperadorCreate(BaseModel):
    usuario_id: uuid.UUID
    data_inicio: date
    data_fim: date
    motivo: str


class AusenciaOperadorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    usuario_id: uuid.UUID
    data_inicio: date
    data_fim: date
    motivo: str


class OperadorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    nome: str
    especialidades: list[str] = []
    cor: Optional[str] = None
    capacidade_diaria: float = 8.0
    dias_trabalho: list[int] = [1, 2, 3, 4, 5]
    avatar_url: Optional[str] = None

    @field_validator("especialidades", mode="before")
    @classmethod
    def default_especialidades(cls, v):
        return v if v is not None else []

    @field_validator("capacidade_diaria", mode="before")
    @classmethod
    def default_capacidade(cls, v):
        return v if v is not None else 8.0

    @field_validator("dias_trabalho", mode="before")
    @classmethod
    def default_dias_trabalho(cls, v):
        return v if v is not None else [1, 2, 3, 4, 5]


class OperadorUpdate(BaseModel):
    especialidades: Optional[list[str]] = None
    cor: Optional[str] = None
    capacidade_diaria: Optional[float] = None
    dias_trabalho: Optional[list[int]] = None


class ProjetoStatusProducaoUpdate(BaseModel):
    status_producao: StatusProducao


class ProjetoProducaoResponse(BaseModel):
    """Espelha ProjetoProducao do frontend (types/producao.ts) num unico
    payload -- projeto + tarefas embutidas -- pra evitar N+1 fetches ao
    montar o Gantt/Kanban inteiro de uma vez."""

    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    nome: str
    cliente_nome: Optional[str] = None
    status_producao: Optional[StatusProducao] = None
    prioridade: int
    data_entrada: Optional[date] = None
    data_entrega_prevista: Optional[date] = None
    cor: Optional[str] = None
    responsavel_id: Optional[uuid.UUID] = None
    observacoes: Optional[str] = None
    tarefas: list[TarefaCronogramaResponse] = []


class ProjetoProducaoCreate(BaseModel):
    nome: str
    cliente_nome: Optional[str] = None
    prioridade: int = 3
    data_entrada: Optional[date] = None
    data_entrega_prevista: Optional[date] = None
    cor: Optional[str] = None
    observacoes: Optional[str] = None
