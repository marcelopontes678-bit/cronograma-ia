import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db, require_role
from app.models.usuario import RoleUsuario, Usuario
from app.schemas.empresa import EmpresaCreate, EmpresaResponse, EmpresaUpdate
from app.services import empresa_service

router = APIRouter(prefix="/empresas", tags=["empresas"])


@router.post("", response_model=EmpresaResponse, status_code=201)
async def create_empresa(
    data: EmpresaCreate,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(require_role(RoleUsuario.ADMIN)),
):
    return await empresa_service.create_empresa(db, data)


@router.get("", response_model=list[EmpresaResponse])
async def list_empresas(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return await empresa_service.list_empresas(db, current_user, skip, limit)


@router.get("/{empresa_id}", response_model=EmpresaResponse)
async def get_empresa(
    empresa_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return await empresa_service.get_empresa(db, empresa_id, current_user)


@router.put("/{empresa_id}", response_model=EmpresaResponse)
async def update_empresa(
    empresa_id: uuid.UUID,
    data: EmpresaUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(
        require_role(RoleUsuario.ADMIN, RoleUsuario.GERENTE)
    ),
):
    return await empresa_service.update_empresa(db, empresa_id, data, current_user)


@router.delete("/{empresa_id}", status_code=204)
async def deactivate_empresa(
    empresa_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_role(RoleUsuario.ADMIN)),
):
    await empresa_service.deactivate_empresa(db, empresa_id, current_user)
