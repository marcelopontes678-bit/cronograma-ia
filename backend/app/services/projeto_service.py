import uuid
from typing import Optional

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import conflict, forbidden_exception, not_found
from app.models.projeto import Projeto, StatusProjeto
from app.models.usuario import RoleUsuario, Usuario
from app.schemas.projeto import ProjetoCreate, ProjetoUpdate
from fastapi import HTTPException, status


async def create_projeto(
    db: AsyncSession, data: ProjetoCreate, current_user: Usuario
) -> Projeto:
    # Não-admin só cria projetos na própria empresa
    if (
        current_user.role != RoleUsuario.ADMIN
        and data.empresa_id != current_user.empresa_id
    ):
        raise forbidden_exception

    existing = await db.execute(
        select(Projeto).where(
            Projeto.empresa_id == data.empresa_id,
            Projeto.codigo == data.codigo,
            Projeto.is_active.is_(True),
        )
    )
    if existing.scalar_one_or_none():
        raise conflict(f"Código '{data.codigo}' já existe nesta empresa")

    payload = data.model_dump()
    payload["criado_por_id"] = current_user.id

    projeto = Projeto(**payload)
    db.add(projeto)
    await db.commit()
    await db.refresh(projeto)
    return projeto


async def get_projeto(
    db: AsyncSession, projeto_id: uuid.UUID, current_user: Usuario
) -> Projeto:
    result = await db.execute(
        select(Projeto)
        .options(
            selectinload(Projeto.criado_por),
            selectinload(Projeto.responsavel),
        )
        .where(Projeto.id == projeto_id, Projeto.is_active.is_(True))
    )
    projeto = result.scalar_one_or_none()
    if not projeto:
        raise not_found("Projeto")

    if (
        current_user.role != RoleUsuario.ADMIN
        and current_user.empresa_id != projeto.empresa_id
    ):
        raise forbidden_exception

    return projeto


async def list_projetos(
    db: AsyncSession,
    current_user: Usuario,
    empresa_id: Optional[uuid.UUID] = None,
    status: Optional[StatusProjeto] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
) -> list[Projeto]:
    query = select(Projeto).where(Projeto.is_active.is_(True))

    if current_user.role != RoleUsuario.ADMIN:
        query = query.where(Projeto.empresa_id == current_user.empresa_id)
    elif empresa_id:
        query = query.where(Projeto.empresa_id == empresa_id)

    if status:
        query = query.where(Projeto.status == status)

    if search:
        term = f"%{search}%"
        query = query.where(
            or_(
                Projeto.nome.ilike(term),
                Projeto.codigo.ilike(term),
                Projeto.cliente_nome.ilike(term),
            )
        )

    result = await db.execute(
        query.order_by(Projeto.prioridade, Projeto.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())


async def update_projeto(
    db: AsyncSession,
    projeto_id: uuid.UUID,
    data: ProjetoUpdate,
    current_user: Usuario,
) -> Projeto:
    projeto = await get_projeto(db, projeto_id, current_user)

    update_data = data.model_dump(exclude_none=True)

    # OPERADOR só pode mudar status
    if current_user.role == RoleUsuario.OPERADOR:
        allowed = {"status"}
        blocked = set(update_data.keys()) - allowed
        if blocked:
            raise forbidden_exception

    for field, value in update_data.items():
        setattr(projeto, field, value)

    await db.commit()
    await db.refresh(projeto)
    return projeto


async def deactivate_projeto(
    db: AsyncSession, projeto_id: uuid.UUID, current_user: Usuario
) -> None:
    if current_user.role != RoleUsuario.ADMIN:
        raise forbidden_exception
    projeto = await get_projeto(db, projeto_id, current_user)

    if projeto.status not in (StatusProjeto.RASCUNHO, StatusProjeto.CANCELADO):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Só é possível excluir projetos em rascunho ou cancelados",
        )

    projeto.is_active = False
    await db.commit()
