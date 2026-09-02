import time
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.orm.attributes import set_committed_value

from app.core.exceptions import not_found
from app.models.comercial import (
    Cliente,
    FichaTecnica,
    ItemEstoque,
    LancamentoFinanceiro,
    MovimentacaoEstoque,
    OrcamentoComercial,
)
from app.models.usuario import Usuario
from app.schemas.comercial import (
    ClienteCreate,
    ClienteUpdate,
    FichaTecnicaCreate,
    ItemEstoqueCreate,
    MovimentacaoEstoqueCreate,
    OrcamentoComercialCreate,
)


# --------------------------------------------------------------------------
# Clientes / CRM
# --------------------------------------------------------------------------

async def listar_clientes(db: AsyncSession, current_user: Usuario) -> list[Cliente]:
    result = await db.execute(
        select(Cliente)
        .where(Cliente.empresa_id == current_user.empresa_id)
        .order_by(Cliente.created_at.desc())
    )
    return list(result.scalars().all())


async def criar_cliente(db: AsyncSession, current_user: Usuario, data: ClienteCreate) -> Cliente:
    cliente = Cliente(empresa_id=current_user.empresa_id, **data.model_dump())
    db.add(cliente)
    await db.commit()
    await db.refresh(cliente)
    return cliente


async def atualizar_cliente(
    db: AsyncSession, current_user: Usuario, cliente_id: uuid.UUID, data: ClienteUpdate
) -> Cliente:
    result = await db.execute(select(Cliente).where(Cliente.id == cliente_id))
    cliente = result.scalar_one_or_none()
    if not cliente or cliente.empresa_id != current_user.empresa_id:
        raise not_found("Cliente")
    for campo, valor in data.model_dump(exclude_unset=True).items():
        setattr(cliente, campo, valor)
    await db.commit()
    await db.refresh(cliente)
    return cliente


# --------------------------------------------------------------------------
# Orcamentos comerciais
# --------------------------------------------------------------------------

async def listar_orcamentos_comerciais(db: AsyncSession, current_user: Usuario) -> list[OrcamentoComercial]:
    result = await db.execute(
        select(OrcamentoComercial)
        .where(OrcamentoComercial.empresa_id == current_user.empresa_id)
        .order_by(OrcamentoComercial.created_at.desc())
    )
    return list(result.scalars().all())


def _calcular_total(subtotal: float, desconto: float) -> float:
    return max(0.0, subtotal - desconto)


async def criar_orcamento_comercial(
    db: AsyncSession, current_user: Usuario, data: OrcamentoComercialCreate
) -> OrcamentoComercial:
    numero = f"ORC-{data.data_criacao[:4]}-{str(int(time.time()))[-4:]}"
    orcamento = OrcamentoComercial(
        empresa_id=current_user.empresa_id,
        numero=numero,
        total=_calcular_total(data.subtotal, data.desconto),
        **data.model_dump(),
    )
    db.add(orcamento)
    await db.commit()
    await db.refresh(orcamento)
    return orcamento


async def atualizar_status_orcamento_comercial(
    db: AsyncSession, current_user: Usuario, orcamento_id: uuid.UUID, status: str
) -> OrcamentoComercial:
    result = await db.execute(select(OrcamentoComercial).where(OrcamentoComercial.id == orcamento_id))
    orcamento = result.scalar_one_or_none()
    if not orcamento or orcamento.empresa_id != current_user.empresa_id:
        raise not_found("Orcamento")
    orcamento.status = status
    await db.commit()
    await db.refresh(orcamento)
    return orcamento


# --------------------------------------------------------------------------
# Fichas tecnicas
# --------------------------------------------------------------------------

async def listar_fichas(db: AsyncSession, current_user: Usuario) -> list[FichaTecnica]:
    result = await db.execute(
        select(FichaTecnica)
        .where(FichaTecnica.empresa_id == current_user.empresa_id)
        .order_by(FichaTecnica.nome)
    )
    return list(result.scalars().all())


async def criar_ficha(db: AsyncSession, current_user: Usuario, data: FichaTecnicaCreate) -> FichaTecnica:
    ficha = FichaTecnica(empresa_id=current_user.empresa_id, **data.model_dump())
    db.add(ficha)
    await db.commit()
    await db.refresh(ficha)
    return ficha


# --------------------------------------------------------------------------
# Estoque
# --------------------------------------------------------------------------

async def listar_estoque(db: AsyncSession, current_user: Usuario) -> list[ItemEstoque]:
    result = await db.execute(
        select(ItemEstoque)
        .where(ItemEstoque.empresa_id == current_user.empresa_id)
        .options(selectinload(ItemEstoque.movimentacoes))
        .order_by(ItemEstoque.nome)
    )
    return list(result.scalars().all())


async def criar_item_estoque(db: AsyncSession, current_user: Usuario, data: ItemEstoqueCreate) -> ItemEstoque:
    item = ItemEstoque(empresa_id=current_user.empresa_id, **data.model_dump())
    db.add(item)
    await db.commit()
    await db.refresh(item)
    # Item recem-criado nunca tem movimentacao -- marca a relationship como
    # carregada (vazia) via set_committed_value em vez de deixar o
    # response_model lazy-load na serializacao (dispara IO sincrono fora do
    # greenlet do SQLAlchemy async, MissingGreenlet). Atribuir com `=`
    # normal dispara o mesmo lazy-load internamente (SQLAlchemy busca o
    # valor antigo pra rastrear historico do cascade delete-orphan).
    set_committed_value(item, "movimentacoes", [])
    return item


async def registrar_movimentacao(
    db: AsyncSession, current_user: Usuario, item_id: uuid.UUID, data: MovimentacaoEstoqueCreate
) -> MovimentacaoEstoque:
    result = await db.execute(select(ItemEstoque).where(ItemEstoque.id == item_id))
    item = result.scalar_one_or_none()
    if not item or item.empresa_id != current_user.empresa_id:
        raise not_found("Item de estoque")

    movimentacao = MovimentacaoEstoque(
        empresa_id=current_user.empresa_id,
        item_id=item_id,
        usuario_id=current_user.id,
        **data.model_dump(),
    )
    db.add(movimentacao)

    # Atualiza a quantidade atual do item conforme o tipo -- nunca deixa a
    # quantidade fisica dessincronizada do historico de movimentacoes.
    if data.tipo == "entrada":
        item.quantidade_atual = float(item.quantidade_atual) + data.quantidade
    elif data.tipo == "saida":
        item.quantidade_atual = float(item.quantidade_atual) - data.quantidade
    elif data.tipo == "ajuste":
        item.quantidade_atual = data.quantidade
    elif data.tipo == "reserva":
        item.quantidade_reservada = float(item.quantidade_reservada) + data.quantidade

    await db.commit()
    await db.refresh(movimentacao)
    return movimentacao


# --------------------------------------------------------------------------
# Financeiro
# --------------------------------------------------------------------------

async def listar_lancamentos(db: AsyncSession, current_user: Usuario) -> list[LancamentoFinanceiro]:
    result = await db.execute(
        select(LancamentoFinanceiro)
        .where(LancamentoFinanceiro.empresa_id == current_user.empresa_id)
        .order_by(LancamentoFinanceiro.data.desc())
    )
    return list(result.scalars().all())
