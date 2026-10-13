import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import conflict, forbidden_exception, not_found
from app.models.empresa import Empresa
from app.models.unidade import Unidade
from app.models.usuario import Usuario
from app.schemas.empresa import EmpresaCreate, EmpresaUpdate


async def create_empresa(db: AsyncSession, data: EmpresaCreate) -> Empresa:
    existing = await db.execute(
        select(Empresa).where(Empresa.cnpj == data.cnpj)
    )
    if existing.scalar_one_or_none():
        raise conflict(f"CNPJ {data.cnpj} já cadastrado")

    empresa = Empresa(**data.model_dump())
    db.add(empresa)
    await db.commit()
    await db.refresh(empresa)
    return empresa


async def get_empresa(
    db: AsyncSession, empresa_id: uuid.UUID, current_user: Usuario
) -> Empresa:
    result = await db.execute(
        select(Empresa)
        .options(selectinload(Empresa.unidades.and_(Unidade.is_active.is_(True))))
        .where(Empresa.id == empresa_id, Empresa.is_active.is_(True))
    )
    empresa = result.scalar_one_or_none()
    if not empresa:
        raise not_found("Empresa")

    # Isolamento estrito por empresa_id, sem excecao pra ADMIN -- ADMIN e
    # admin da propria empresa, nunca da plataforma (ver routers/usuario.py).
    if current_user.empresa_id != empresa_id:
        raise forbidden_exception

    return empresa


async def list_empresas(
    db: AsyncSession,
    current_user: Usuario,
    skip: int = 0,
    limit: int = 20,
) -> list[Empresa]:
    query = select(Empresa).options(
        selectinload(Empresa.unidades.and_(Unidade.is_active.is_(True)))
    ).where(Empresa.is_active.is_(True), Empresa.id == current_user.empresa_id)

    result = await db.execute(query.offset(skip).limit(limit))
    return list(result.scalars().all())


async def update_empresa(
    db: AsyncSession,
    empresa_id: uuid.UUID,
    data: EmpresaUpdate,
    current_user: Usuario,
) -> Empresa:
    empresa = await get_empresa(db, empresa_id, current_user)

    if data.cnpj and data.cnpj != empresa.cnpj:
        existing = await db.execute(
            select(Empresa).where(Empresa.cnpj == data.cnpj)
        )
        if existing.scalar_one_or_none():
            raise conflict(f"CNPJ {data.cnpj} já cadastrado")

    for field, value in data.model_dump(exclude_none=True).items():
        setattr(empresa, field, value)

    await db.commit()
    await db.refresh(empresa)
    return empresa


async def deactivate_empresa(
    db: AsyncSession, empresa_id: uuid.UUID, current_user: Usuario
) -> None:
    empresa = await get_empresa(db, empresa_id, current_user)
    empresa.is_active = False
    await db.commit()
