import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


# ── Peça ─────────────────────────────────────────────────────────────────────

class PecaBase(BaseModel):
    nome: str = Field(min_length=1, max_length=200)
    material_id: Optional[uuid.UUID] = None
    comprimento_mm: int = Field(ge=1, le=20_000)
    largura_mm: int = Field(ge=1, le=10_000)
    quantidade: int = Field(1, ge=1, le=1_000)
    veio: bool = False
    fita_c1: bool = False
    fita_c2: bool = False
    fita_l1: bool = False
    fita_l2: bool = False
    observacoes: Optional[str] = None


class PecaCreate(PecaBase):
    pass


class PecaUpdate(BaseModel):
    nome: Optional[str] = Field(None, min_length=1, max_length=200)
    material_id: Optional[uuid.UUID] = None
    comprimento_mm: Optional[int] = Field(None, ge=1, le=20_000)
    largura_mm: Optional[int] = Field(None, ge=1, le=10_000)
    quantidade: Optional[int] = Field(None, ge=1, le=1_000)
    veio: Optional[bool] = None
    fita_c1: Optional[bool] = None
    fita_c2: Optional[bool] = None
    fita_l1: Optional[bool] = None
    fita_l2: Optional[bool] = None
    observacoes: Optional[str] = None


class PecaResponse(PecaBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    modulo_id: uuid.UUID
    created_at: datetime
    is_active: bool


# ── Módulo ───────────────────────────────────────────────────────────────────

class ModuloBase(BaseModel):
    nome: str = Field(min_length=1, max_length=200)
    codigo: Optional[str] = Field(None, max_length=50)
    largura_mm: Optional[int] = Field(None, ge=1, le=20_000)
    altura_mm: Optional[int] = Field(None, ge=1, le=20_000)
    profundidade_mm: Optional[int] = Field(None, ge=1, le=20_000)
    quantidade: int = Field(1, ge=1, le=1_000)
    descricao: Optional[str] = None
    ordem: int = Field(0, ge=0)


class ModuloCreate(ModuloBase):
    pass


class ModuloUpdate(BaseModel):
    nome: Optional[str] = Field(None, min_length=1, max_length=200)
    codigo: Optional[str] = Field(None, max_length=50)
    largura_mm: Optional[int] = Field(None, ge=1, le=20_000)
    altura_mm: Optional[int] = Field(None, ge=1, le=20_000)
    profundidade_mm: Optional[int] = Field(None, ge=1, le=20_000)
    quantidade: Optional[int] = Field(None, ge=1, le=1_000)
    descricao: Optional[str] = None
    ordem: Optional[int] = Field(None, ge=0)


class ModuloResponse(ModuloBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    ambiente_id: uuid.UUID
    created_at: datetime
    is_active: bool
    pecas: list[PecaResponse] = []


# ── Ambiente ─────────────────────────────────────────────────────────────────

class AmbienteBase(BaseModel):
    nome: str = Field(min_length=1, max_length=200)
    descricao: Optional[str] = None
    ordem: int = Field(0, ge=0)


class AmbienteCreate(AmbienteBase):
    pass


class AmbienteUpdate(BaseModel):
    nome: Optional[str] = Field(None, min_length=1, max_length=200)
    descricao: Optional[str] = None
    ordem: Optional[int] = Field(None, ge=0)


class AmbienteResponse(AmbienteBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    projeto_id: uuid.UUID
    created_at: datetime
    is_active: bool
    modulos: list[ModuloResponse] = []


# ── Resumo de engenharia (lista de corte) ────────────────────────────────────

class ResumoMaterial(BaseModel):
    material_id: Optional[uuid.UUID] = None
    material_nome: str
    total_pecas: int
    area_m2: float
    fita_borda_m: float


class EngenhariaResumo(BaseModel):
    projeto_id: uuid.UUID
    total_ambientes: int
    total_modulos: int
    total_pecas: int
    materiais: list[ResumoMaterial]
    ambientes: list[AmbienteResponse]
