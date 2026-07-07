import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import forbidden_exception
from app.dependencies import get_current_user, get_db, require_role
from app.models.usuario import RoleUsuario, Usuario
from app.schemas.unidade import UnidadeCreate, UnidadeResponse, UnidadeUpdate
from app.services import unidade_service

router = APIRouter(prefix="/empresas/{empresa_id}/unidades", tags=["unidades"])


@router.post("", response_model=UnidadeResponse, status_code=201)
async def create_unidade(
    empresa_id: uuid.UUID,
    data: UnidadeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(
        require_role(RoleUsuario.ADMIN, RoleUsuario.GERENTE)
    ),
):
    # Não-admin só cria unidades na própria empresa
    if current_user.role != RoleUsuario.ADMIN and current_user.empresa_id != empresa_id:
        raise forbidden_exception
    data.empresa_id = empresa_id
    return await unidade_service.create_unidade(db, data)


@router.get("", response_model=list[UnidadeResponse])
async def list_unidades(
    empresa_id: uuid.UUID,
    tipo: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return await unidade_service.list_unidades(db, empresa_id, current_user, tipo)


@router.get("/{unidade_id}", response_model=UnidadeResponse)
async def get_unidade(
    empresa_id: uuid.UUID,
    unidade_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return await unidade_service.get_unidade(db, unidade_id, current_user)


@router.put("/{unidade_id}", response_model=UnidadeResponse)
async def update_unidade(
    empresa_id: uuid.UUID,
    unidade_id: uuid.UUID,
    data: UnidadeUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(
        require_role(RoleUsuario.ADMIN, RoleUsuario.GERENTE)
    ),
):
    return await unidade_service.update_unidade(db, unidade_id, data, current_user)


@router.delete("/{unidade_id}", status_code=204)
async def deactivate_unidade(
    empresa_id: uuid.UUID,
    unidade_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_role(RoleUsuario.ADMIN)),
):
    await unidade_service.deactivate_unidade(db, unidade_id, current_user)
