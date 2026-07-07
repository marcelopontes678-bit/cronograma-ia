import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.material import TipoMaterial


class MaterialBase(BaseModel):
    nome: str = Field(min_length=1, max_length=200)
    codigo: Optional[str] = Field(None, max_length=50)
    tipo: TipoMaterial
    espessura_mm: Optional[int] = Field(None, ge=1, le=200)
    largura_mm: Optional[int] = Field(None, ge=1, le=10_000)
    comprimento_mm: Optional[int] = Field(None, ge=1, le=20_000)
    cor: Optional[str] = Field(None, max_length=100)
    unidade_medida: str = Field("un", max_length=10)
    preco_unitario: Optional[Decimal] = Field(None, ge=0)
    observacoes: Optional[str] = None


class MaterialCreate(MaterialBase):
    pass


class MaterialUpdate(BaseModel):
    nome: Optional[str] = Field(None, min_length=1, max_length=200)
    codigo: Optional[str] = Field(None, max_length=50)
    tipo: Optional[TipoMaterial] = None
    espessura_mm: Optional[int] = Field(None, ge=1, le=200)
    largura_mm: Optional[int] = Field(None, ge=1, le=10_000)
    comprimento_mm: Optional[int] = Field(None, ge=1, le=20_000)
    cor: Optional[str] = Field(None, max_length=100)
    unidade_medida: Optional[str] = Field(None, max_length=10)
    preco_unitario: Optional[Decimal] = Field(None, ge=0)
    observacoes: Optional[str] = None


class MaterialResponse(MaterialBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    empresa_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    is_active: bool
