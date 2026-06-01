import re
import uuid
from datetime import datetime, time
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator


def _validate_cnpj(v: str) -> str:
    if not re.match(r"^\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}$", v):
        raise ValueError("CNPJ deve estar no formato XX.XXX.XXX/XXXX-XX")
    return v


class EmpresaBase(BaseModel):
    nome: str
    nome_fantasia: Optional[str] = None
    cnpj: str
    email: EmailStr
    telefone: Optional[str] = None
    cep: Optional[str] = None
    logradouro: Optional[str] = None
    numero: Optional[str] = None
    complemento: Optional[str] = None
    bairro: Optional[str] = None
    cidade: Optional[str] = None
    estado: Optional[str] = None
    horario_inicio: Optional[time] = None
    horario_fim: Optional[time] = None
    dias_funcionamento: Optional[list[str]] = None
    logo_url: Optional[str] = None

    @field_validator("cnpj")
    @classmethod
    def validate_cnpj(cls, v: str) -> str:
        return _validate_cnpj(v)


class EmpresaCreate(EmpresaBase):
    pass


class EmpresaUpdate(BaseModel):
    nome: Optional[str] = None
    nome_fantasia: Optional[str] = None
    cnpj: Optional[str] = None
    email: Optional[EmailStr] = None
    telefone: Optional[str] = None
    cep: Optional[str] = None
    logradouro: Optional[str] = None
    numero: Optional[str] = None
    complemento: Optional[str] = None
    bairro: Optional[str] = None
    cidade: Optional[str] = None
    estado: Optional[str] = None
    horario_inicio: Optional[time] = None
    horario_fim: Optional[time] = None
    dias_funcionamento: Optional[list[str]] = None
    logo_url: Optional[str] = None

    @field_validator("cnpj")
    @classmethod
    def validate_cnpj(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            return _validate_cnpj(v)
        return v


class UnidadeSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    nome: str
    tipo: str
    codigo: Optional[str] = None
    is_sede: bool


class EmpresaResponse(EmpresaBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    is_active: bool
    unidades: list[UnidadeSummary] = []
