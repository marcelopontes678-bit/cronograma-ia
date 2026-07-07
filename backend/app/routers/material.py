import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db, require_role
from app.models.usuario import RoleUsuario, Usuario
from app.schemas.material import MaterialCreate, MaterialResponse, MaterialUpdate
from app.services import material_service

router = APIRouter(prefix="/materiais", tags=["materiais"])

_pode_editar = require_role(RoleUsuario.ADMIN, RoleUsuario.GERENTE)


@router.post("", response_model=MaterialResponse, status_code=201)
async def create_material(
    data: MaterialCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(_pode_editar),
):
    return await material_service.create_material(db, data, current_user)


@router.get("", response_model=list[MaterialResponse])
async def list_materiais(
    tipo: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return await material_service.list_materiais(
        db, current_user, tipo, search, skip, limit
    )


@router.get("/{material_id}", response_model=MaterialResponse)
async def get_material(
    material_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return await material_service.get_material(db, material_id, current_user)


@router.put("/{material_id}", response_model=MaterialResponse)
async def update_material(
    material_id: uuid.UUID,
    data: MaterialUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(_pode_editar),
):
    return await material_service.update_material(db, material_id, data, current_user)


@router.delete("/{material_id}", status_code=204)
async def deactivate_material(
    material_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(_pode_editar),
):
    await material_service.deactivate_material(db, material_id, current_user)
