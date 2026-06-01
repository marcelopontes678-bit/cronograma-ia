import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator

from app.models.usuario import RoleUsuario


class UsuarioBase(BaseModel):
    nome: str
    email: EmailStr
    role: RoleUsuario
    telefone: Optional[str] = None
    avatar_url: Optional[str] = None


class UsuarioCreate(UsuarioBase):
    empresa_id: uuid.UUID
    unidade_id: Optional[uuid.UUID] = None
    password: str
    must_change_password: bool = False

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Senha deve ter pelo menos 8 caracteres")
        return v


class UsuarioUpdate(BaseModel):
    nome: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[RoleUsuario] = None
    telefone: Optional[str] = None
    avatar_url: Optional[str] = None
    unidade_id: Optional[uuid.UUID] = None


class PasswordChange(BaseModel):
    current_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Senha deve ter pelo menos 8 caracteres")
        return v


class UsuarioSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    nome: str
    email: str
    role: RoleUsuario


class UsuarioResponse(UsuarioBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    empresa_id: uuid.UUID
    unidade_id: Optional[uuid.UUID] = None
    must_change_password: bool
    last_login_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    is_active: bool
