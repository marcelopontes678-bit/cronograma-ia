import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import conflict, forbidden_exception, not_found
from app.core.security import hash_password, verify_password
from app.models.usuario import RoleUsuario, Usuario
from app.schemas.usuario import PasswordChange, UsuarioCreate, UsuarioUpdate
from fastapi import HTTPException, status


async def create_usuario(db: AsyncSession, data: UsuarioCreate) -> Usuario:
    existing = await db.execute(
        select(Usuario).where(Usuario.email == data.email)
    )
    if existing.scalar_one_or_none():
        raise conflict(f"E-mail '{data.email}' já cadastrado")

    payload = data.model_dump(exclude={"password"})
    payload["hashed_password"] = hash_password(data.password)

    usuario = Usuario(**payload)
    db.add(usuario)
    await db.commit()
    await db.refresh(usuario)
    return usuario


async def get_usuario(
    db: AsyncSession, usuario_id: uuid.UUID, current_user: Usuario
) -> Usuario:
    result = await db.execute(
        select(Usuario).where(Usuario.id == usuario_id, Usuario.is_active.is_(True))
    )
    usuario = result.scalar_one_or_none()
    if not usuario:
        raise not_found("Usuário")

    if (
        current_user.role != RoleUsuario.ADMIN
        and str(current_user.id) != str(usuario_id)
        and current_user.empresa_id != usuario.empresa_id
    ):
        raise forbidden_exception

    return usuario


async def list_usuarios(
    db: AsyncSession,
    current_user: Usuario,
    skip: int = 0,
    limit: int = 20,
) -> list[Usuario]:
    query = select(Usuario).where(
        Usuario.empresa_id == current_user.empresa_id,
        Usuario.is_active.is_(True),
    )
    result = await db.execute(query.offset(skip).limit(limit))
    return list(result.scalars().all())


async def update_usuario(
    db: AsyncSession,
    usuario_id: uuid.UUID,
    data: UsuarioUpdate,
    current_user: Usuario,
) -> Usuario:
    usuario = await get_usuario(db, usuario_id, current_user)

    # Somente ADMIN pode mudar role
    update_data = data.model_dump(exclude_none=True)
    if "role" in update_data and current_user.role != RoleUsuario.ADMIN:
        raise forbidden_exception

    if "email" in update_data and update_data["email"] != usuario.email:
        existing = await db.execute(
            select(Usuario).where(Usuario.email == update_data["email"])
        )
        if existing.scalar_one_or_none():
            raise conflict(f"E-mail '{update_data['email']}' já cadastrado")

    for field, value in update_data.items():
        setattr(usuario, field, value)

    await db.commit()
    await db.refresh(usuario)
    return usuario


async def change_password(
    db: AsyncSession,
    usuario_id: uuid.UUID,
    data: PasswordChange,
    current_user: Usuario,
) -> None:
    if str(current_user.id) != str(usuario_id):
        raise forbidden_exception

    if not verify_password(data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Senha atual incorreta",
        )

    current_user.hashed_password = hash_password(data.new_password)
    current_user.must_change_password = False
    await db.commit()


async def deactivate_usuario(
    db: AsyncSession, usuario_id: uuid.UUID, current_user: Usuario
) -> None:
    if current_user.role != RoleUsuario.ADMIN:
        raise forbidden_exception
    usuario = await get_usuario(db, usuario_id, current_user)
    usuario.is_active = False
    await db.commit()
