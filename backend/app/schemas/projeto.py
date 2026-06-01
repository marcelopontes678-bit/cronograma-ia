import uuid
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator

from app.models.projeto import StatusProjeto
from app.schemas.usuario import UsuarioSummary


class ProjetoBase(BaseModel):
    nome: str
    descricao: Optional[str] = None
    status: StatusProjeto = StatusProjeto.RASCUNHO
    cliente_nome: Optional[str] = None
    cliente_contato: Optional[str] = None
    data_entrada: Optional[date] = None
    data_entrega_prevista: Optional[date] = None
    data_entrega_real: Optional[date] = None
    prioridade: int = 3
    observacoes: Optional[str] = None
    unidade_id: Optional[uuid.UUID] = None
    responsavel_id: Optional[uuid.UUID] = None

    @field_validator("prioridade")
    @classmethod
    def validate_prioridade(cls, v: int) -> int:
        if not 1 <= v <= 5:
            raise ValueError("Prioridade deve ser entre 1 (urgente) e 5 (baixa)")
        return v


class ProjetoCreate(ProjetoBase):
    empresa_id: uuid.UUID
    codigo: str


class ProjetoUpdate(BaseModel):
    nome: Optional[str] = None
    descricao: Optional[str] = None
    status: Optional[StatusProjeto] = None
    cliente_nome: Optional[str] = None
    cliente_contato: Optional[str] = None
    data_entrada: Optional[date] = None
    data_entrega_prevista: Optional[date] = None
    data_entrega_real: Optional[date] = None
    prioridade: Optional[int] = None
    observacoes: Optional[str] = None
    unidade_id: Optional[uuid.UUID] = None
    responsavel_id: Optional[uuid.UUID] = None

    @field_validator("prioridade")
    @classmethod
    def validate_prioridade(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and not 1 <= v <= 5:
            raise ValueError("Prioridade deve ser entre 1 (urgente) e 5 (baixa)")
        return v


class ProjetoListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    codigo: str
    nome: str
    status: StatusProjeto
    cliente_nome: Optional[str] = None
    data_entrega_prevista: Optional[date] = None
    prioridade: int
    created_at: datetime


class ProjetoResponse(ProjetoBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    codigo: str
    empresa_id: uuid.UUID
    criado_por: Optional[UsuarioSummary] = None
    responsavel: Optional[UsuarioSummary] = None
    created_at: datetime
    updated_at: datetime
    is_active: bool
