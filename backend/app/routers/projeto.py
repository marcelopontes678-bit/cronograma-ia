import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db, require_role
from app.models.projeto import StatusProjeto
from app.models.usuario import RoleUsuario, Usuario
from app.schemas.projeto import (
    ProjetoCreate,
    ProjetoListItem,
    ProjetoResponse,
    ProjetoUpdate,
)
from app.services import projeto_service

router = APIRouter(prefix="/projetos", tags=["projetos"])


@router.post("/", response_model=ProjetoResponse, status_code=201)
async def create_projeto(
    data: ProjetoCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(
        require_role(RoleUsuario.ADMIN, RoleUsuario.GERENTE)
    ),
):
    # Nunca confia no empresa_id do corpo -- ver comentario no schema.
    data.empresa_id = current_user.empresa_id
    return await projeto_service.create_projeto(db, data, current_user)


@router.get("/", response_model=list[ProjetoListItem])
async def list_projetos(
    empresa_id: Optional[uuid.UUID] = Query(None),
    status: Optional[StatusProjeto] = Query(None),
    search: Optional[str] = Query(None),
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return await projeto_service.list_projetos(
        db, current_user, empresa_id, status, search, skip, limit
    )


@router.get("/{projeto_id}", response_model=ProjetoResponse)
async def get_projeto(
    projeto_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return await projeto_service.get_projeto(db, projeto_id, current_user)


@router.put("/{projeto_id}", response_model=ProjetoResponse)
async def update_projeto(
    projeto_id: uuid.UUID,
    data: ProjetoUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return await projeto_service.update_projeto(db, projeto_id, data, current_user)


@router.delete("/{projeto_id}", status_code=204)
async def deactivate_projeto(
    projeto_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_role(RoleUsuario.ADMIN)),
):
    await projeto_service.deactivate_projeto(db, projeto_id, current_user)
