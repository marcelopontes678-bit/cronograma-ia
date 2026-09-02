import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db, require_role
from app.models.usuario import RoleUsuario, Usuario
from app.schemas.usuario import (
    PasswordChange,
    UsuarioCreate,
    UsuarioResponse,
    UsuarioUpdate,
)
from app.services import usuario_service

router = APIRouter(prefix="/usuarios", tags=["usuarios"])


@router.post("/", response_model=UsuarioResponse, status_code=201)
async def create_usuario(
    data: UsuarioCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_role(RoleUsuario.ADMIN)),
):
    # Sem isso, um ADMIN de uma empresa poderia criar um usuario em
    # QUALQUER empresa passando um empresa_id arbitrario no corpo -- o
    # require_role acima so checa o cargo, nunca o tenant (bug real
    # encontrado ao expor esta rota no frontend gestori).
    data.empresa_id = current_user.empresa_id
    return await usuario_service.create_usuario(db, data)


@router.get("/", response_model=list[UsuarioResponse])
async def list_usuarios(
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(
        require_role(RoleUsuario.ADMIN, RoleUsuario.GERENTE)
    ),
):
    return await usuario_service.list_usuarios(db, current_user, skip, limit)


@router.get("/{usuario_id}", response_model=UsuarioResponse)
async def get_usuario(
    usuario_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return await usuario_service.get_usuario(db, usuario_id, current_user)


@router.put("/{usuario_id}", response_model=UsuarioResponse)
async def update_usuario(
    usuario_id: uuid.UUID,
    data: UsuarioUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return await usuario_service.update_usuario(db, usuario_id, data, current_user)


@router.post("/{usuario_id}/change-password", status_code=204)
async def change_password(
    usuario_id: uuid.UUID,
    data: PasswordChange,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    await usuario_service.change_password(db, usuario_id, data, current_user)


@router.delete("/{usuario_id}", status_code=204)
async def deactivate_usuario(
    usuario_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_role(RoleUsuario.ADMIN)),
):
    await usuario_service.deactivate_usuario(db, usuario_id, current_user)
