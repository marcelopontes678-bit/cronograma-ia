import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import conflict, forbidden_exception, not_found
from app.models.material import Material
from app.models.usuario import RoleUsuario, Usuario
from app.schemas.material import MaterialCreate, MaterialUpdate


async def create_material(
    db: AsyncSession, data: MaterialCreate, current_user: Usuario
) -> Material:
    if data.codigo:
        existing = await db.execute(
            select(Material).where(
                Material.empresa_id == current_user.empresa_id,
                Material.codigo == data.codigo,
                Material.is_active.is_(True),
            )
        )
        if existing.scalar_one_or_none():
            raise conflict(f"Código '{data.codigo}' já usado nesta empresa")

    material = Material(**data.model_dump(), empresa_id=current_user.empresa_id)
    db.add(material)
    await db.commit()
    await db.refresh(material)
    return material


async def get_material(
    db: AsyncSession, material_id: uuid.UUID, current_user: Usuario
) -> Material:
    result = await db.execute(
        select(Material).where(
            Material.id == material_id, Material.is_active.is_(True)
        )
    )
    material = result.scalar_one_or_none()
    if not material:
        raise not_found("Material")

    if (
        current_user.role != RoleUsuario.ADMIN
        and current_user.empresa_id != material.empresa_id
    ):
        raise forbidden_exception

    return material


async def list_materiais(
    db: AsyncSession,
    current_user: Usuario,
    tipo: Optional[str] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
) -> list[Material]:
    query = select(Material).where(
        Material.empresa_id == current_user.empresa_id,
        Material.is_active.is_(True),
    )
    if tipo:
        query = query.where(Material.tipo == tipo)
    if search:
        term = f"%{search}%"
        query = query.where(Material.nome.ilike(term) | Material.codigo.ilike(term))

    result = await db.execute(
        query.order_by(Material.nome).offset(skip).limit(limit)
    )
    return list(result.scalars().all())


async def update_material(
    db: AsyncSession,
    material_id: uuid.UUID,
    data: MaterialUpdate,
    current_user: Usuario,
) -> Material:
    material = await get_material(db, material_id, current_user)

    for field, value in data.model_dump(exclude_none=True).items():
        setattr(material, field, value)

    await db.commit()
    await db.refresh(material)
    return material


async def deactivate_material(
    db: AsyncSession, material_id: uuid.UUID, current_user: Usuario
) -> None:
    material = await get_material(db, material_id, current_user)
    material.is_active = False
    await db.commit()
