import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr

from app.models.unidade import TipoUnidade


class UnidadeBase(BaseModel):
    nome: str
    tipo: TipoUnidade
    codigo: Optional[str] = None
    email: Optional[EmailStr] = None
    telefone: Optional[str] = None
    cep: Optional[str] = None
    logradouro: Optional[str] = None
    numero: Optional[str] = None
    complemento: Optional[str] = None
    bairro: Optional[str] = None
    cidade: Optional[str] = None
    estado: Optional[str] = None
    is_sede: bool = False


class UnidadeCreate(UnidadeBase):
    empresa_id: uuid.UUID


class UnidadeUpdate(BaseModel):
    nome: Optional[str] = None
    tipo: Optional[TipoUnidade] = None
    codigo: Optional[str] = None
    email: Optional[EmailStr] = None
    telefone: Optional[str] = None
    cep: Optional[str] = None
    logradouro: Optional[str] = None
    numero: Optional[str] = None
    complemento: Optional[str] = None
    bairro: Optional[str] = None
    cidade: Optional[str] = None
    estado: Optional[str] = None
    is_sede: Optional[bool] = None


class EmpresaSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    nome: str
    cnpj: str


class UnidadeResponse(UnidadeBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    empresa_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    is_active: bool
    empresa: Optional[EmpresaSummary] = None
