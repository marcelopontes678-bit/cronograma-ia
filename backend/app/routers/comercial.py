import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.models.usuario import Usuario
from app.schemas.comercial import (
    ClienteCreate,
    ClienteResponse,
    ClienteUpdate,
    FichaTecnicaCreate,
    FichaTecnicaResponse,
    ItemEstoqueCreate,
    ItemEstoqueResponse,
    LancamentoFinanceiroResponse,
    MovimentacaoEstoqueCreate,
    MovimentacaoEstoqueResponse,
    OrcamentoComercialCreate,
    OrcamentoComercialResponse,
    OrcamentoComercialStatusUpdate,
)
from app.services import comercial_service

router = APIRouter(prefix="/comercial", tags=["comercial"])


# --------------------------------------------------------------------------
# CRM / Clientes
# --------------------------------------------------------------------------

@router.get("/clientes", response_model=list[ClienteResponse])
async def listar_clientes(
    db: AsyncSession = Depends(get_db), current_user: Usuario = Depends(get_current_user)
):
    return await comercial_service.listar_clientes(db, current_user)


@router.post("/clientes", status_code=201, response_model=ClienteResponse)
async def criar_cliente(
    data: ClienteCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return await comercial_service.criar_cliente(db, current_user, data)


@router.put("/clientes/{cliente_id}", response_model=ClienteResponse)
async def atualizar_cliente(
    cliente_id: uuid.UUID,
    data: ClienteUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return await comercial_service.atualizar_cliente(db, current_user, cliente_id, data)


# --------------------------------------------------------------------------
# Orcamentos comerciais
# --------------------------------------------------------------------------

@router.get("/orcamentos", response_model=list[OrcamentoComercialResponse])
async def listar_orcamentos_comerciais(
    db: AsyncSession = Depends(get_db), current_user: Usuario = Depends(get_current_user)
):
    return await comercial_service.listar_orcamentos_comerciais(db, current_user)


@router.post("/orcamentos", status_code=201, response_model=OrcamentoComercialResponse)
async def criar_orcamento_comercial(
    data: OrcamentoComercialCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return await comercial_service.criar_orcamento_comercial(db, current_user, data)


@router.patch("/orcamentos/{orcamento_id}/status", response_model=OrcamentoComercialResponse)
async def atualizar_status_orcamento_comercial(
    orcamento_id: uuid.UUID,
    data: OrcamentoComercialStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return await comercial_service.atualizar_status_orcamento_comercial(
        db, current_user, orcamento_id, data.status
    )


# --------------------------------------------------------------------------
# Fichas tecnicas
# --------------------------------------------------------------------------

@router.get("/fichas", response_model=list[FichaTecnicaResponse])
async def listar_fichas(
    db: AsyncSession = Depends(get_db), current_user: Usuario = Depends(get_current_user)
):
    return await comercial_service.listar_fichas(db, current_user)


@router.post("/fichas", status_code=201, response_model=FichaTecnicaResponse)
async def criar_ficha(
    data: FichaTecnicaCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return await comercial_service.criar_ficha(db, current_user, data)


# --------------------------------------------------------------------------
# Estoque
# --------------------------------------------------------------------------

@router.get("/estoque", response_model=list[ItemEstoqueResponse])
async def listar_estoque(
    db: AsyncSession = Depends(get_db), current_user: Usuario = Depends(get_current_user)
):
    return await comercial_service.listar_estoque(db, current_user)


@router.post("/estoque", status_code=201, response_model=ItemEstoqueResponse)
async def criar_item_estoque(
    data: ItemEstoqueCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return await comercial_service.criar_item_estoque(db, current_user, data)


@router.post(
    "/estoque/{item_id}/movimentacoes", status_code=201, response_model=MovimentacaoEstoqueResponse
)
async def registrar_movimentacao(
    item_id: uuid.UUID,
    data: MovimentacaoEstoqueCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return await comercial_service.registrar_movimentacao(db, current_user, item_id, data)


# --------------------------------------------------------------------------
# Financeiro
# --------------------------------------------------------------------------

@router.get("/lancamentos", response_model=list[LancamentoFinanceiroResponse])
async def listar_lancamentos(
    db: AsyncSession = Depends(get_db), current_user: Usuario = Depends(get_current_user)
):
    return await comercial_service.listar_lancamentos(db, current_user)
