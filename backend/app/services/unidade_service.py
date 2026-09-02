import uuid

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.orm.attributes import set_committed_value

from app.core.exceptions import conflict, forbidden_exception, not_found
from app.models.unidade import Unidade
from app.models.usuario import RoleUsuario, Usuario
from app.schemas.unidade import UnidadeCreate, UnidadeUpdate


async def create_unidade(db: AsyncSession, data: UnidadeCreate) -> Unidade:
    if data.codigo:
        existing = await db.execute(
            select(Unidade).where(
                Unidade.empresa_id == data.empresa_id,
                Unidade.codigo == data.codigo,
                Unidade.is_active.is_(True),
            )
        )
        if existing.scalar_one_or_none():
            raise conflict(f"Código '{data.codigo}' já usado nesta empresa")

    if data.is_sede:
        await db.execute(
            update(Unidade)
            .where(Unidade.empresa_id == data.empresa_id)
            .values(is_sede=False)
        )

    unidade = Unidade(**data.model_dump())
    db.add(unidade)
    await db.commit()
    await db.refresh(unidade)
    # Unidade recem-criada nunca tem a relacao empresa carregada -- sem isso
    # a serializacao do response_model (UnidadeResponse.empresa, opcional)
    # tenta lazy-load fora do greenlet async e quebra com MissingGreenlet.
    set_committed_value(unidade, "empresa", None)
    return unidade


async def get_unidade(
    db: AsyncSession, unidade_id: uuid.UUID, current_user: Usuario
) -> Unidade:
    result = await db.execute(
        select(Unidade)
        .options(selectinload(Unidade.empresa))
        .where(Unidade.id == unidade_id, Unidade.is_active.is_(True))
    )
    unidade = result.scalar_one_or_none()
    if not unidade:
        raise not_found("Unidade")

    if (
        current_user.role != RoleUsuario.ADMIN
        and current_user.empresa_id != unidade.empresa_id
    ):
        raise forbidden_exception

    return unidade


async def list_unidades(
    db: AsyncSession,
    empresa_id: uuid.UUID,
    current_user: Usuario,
    tipo: str | None = None,
) -> list[Unidade]:
    if (
        current_user.role != RoleUsuario.ADMIN
        and current_user.empresa_id != empresa_id
    ):
        raise forbidden_exception

    query = select(Unidade).where(
        Unidade.empresa_id == empresa_id, Unidade.is_active.is_(True)
    )
    if tipo:
        query = query.where(Unidade.tipo == tipo)

    result = await db.execute(query)
    return list(result.scalars().all())


async def update_unidade(
    db: AsyncSession,
    unidade_id: uuid.UUID,
    data: UnidadeUpdate,
    current_user: Usuario,
) -> Unidade:
    unidade = await get_unidade(db, unidade_id, current_user)

    if data.is_sede is True:
        await db.execute(
            update(Unidade)
            .where(Unidade.empresa_id == unidade.empresa_id)
            .values(is_sede=False)
        )

    for field, value in data.model_dump(exclude_none=True).items():
        setattr(unidade, field, value)

    await db.commit()
    await db.refresh(unidade)
    return unidade


async def deactivate_unidade(
    db: AsyncSession, unidade_id: uuid.UUID, current_user: Usuario
) -> None:
    unidade = await get_unidade(db, unidade_id, current_user)
    unidade.is_active = False
    await db.commit()
