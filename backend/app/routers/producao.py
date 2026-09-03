import uuid

from fastapi import APIRouter, Depends

from app.dependencies import get_current_user, get_db
from app.models.usuario import Usuario
from app.schemas.producao import (
    AusenciaOperadorCreate,
    AusenciaOperadorResponse,
    OperadorResponse,
    OperadorUpdate,
    ProjetoProducaoCreate,
    ProjetoProducaoResponse,
    TarefaCronogramaCreate,
    TarefaCronogramaResponse,
    TarefaCronogramaUpdate,
)
from app.services import producao_service
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/producao", tags=["producao"])


def _to_projeto_producao_response(projeto, tarefas) -> ProjetoProducaoResponse:
    return ProjetoProducaoResponse(
        id=projeto.id,
        nome=projeto.nome,
        cliente_nome=projeto.cliente_nome,
        status_producao=projeto.status_producao,
        prioridade=projeto.prioridade,
        data_entrada=projeto.data_entrada,
        data_entrega_prevista=projeto.data_entrega_prevista,
        cor=projeto.cor,
        responsavel_id=projeto.responsavel_id,
        observacoes=projeto.observacoes,
        tarefas=tarefas,
    )


@router.get("/projetos", response_model=list[ProjetoProducaoResponse])
async def listar_projetos_producao(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    pares = await producao_service.listar_projetos_producao(db, current_user)
    return [_to_projeto_producao_response(p, t) for p, t in pares]


@router.post("/projetos", status_code=201, response_model=ProjetoProducaoResponse)
async def criar_projeto_producao(
    data: ProjetoProducaoCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    projeto = await producao_service.criar_projeto_producao(db, data, current_user)
    return _to_projeto_producao_response(projeto, [])


@router.get("/projetos/{projeto_id}/tarefas", response_model=list[TarefaCronogramaResponse])
async def listar_tarefas(
    projeto_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return await producao_service.listar_tarefas_do_projeto(db, projeto_id, current_user)


@router.post(
    "/projetos/{projeto_id}/tarefas", status_code=201, response_model=TarefaCronogramaResponse
)
async def criar_tarefa(
    projeto_id: uuid.UUID,
    data: TarefaCronogramaCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return await producao_service.criar_tarefa(db, projeto_id, data, current_user)


@router.put("/tarefas/{tarefa_id}", response_model=TarefaCronogramaResponse)
async def atualizar_tarefa(
    tarefa_id: uuid.UUID,
    data: TarefaCronogramaUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return await producao_service.atualizar_tarefa(db, tarefa_id, data, current_user)


@router.delete("/tarefas/{tarefa_id}", status_code=204)
async def deletar_tarefa(
    tarefa_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    await producao_service.deletar_tarefa(db, tarefa_id, current_user)


@router.get("/operadores", response_model=list[OperadorResponse])
async def listar_operadores(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return await producao_service.listar_operadores(db, current_user)


@router.put("/operadores/{usuario_id}", response_model=OperadorResponse)
async def atualizar_perfil_operador(
    usuario_id: uuid.UUID,
    data: OperadorUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return await producao_service.atualizar_perfil_operador(db, usuario_id, data, current_user)


@router.get("/ausencias", response_model=list[AusenciaOperadorResponse])
async def listar_ausencias(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return await producao_service.listar_ausencias(db, current_user)


@router.post("/ausencias", status_code=201, response_model=AusenciaOperadorResponse)
async def criar_ausencia(
    data: AusenciaOperadorCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return await producao_service.criar_ausencia(db, data, current_user)


@router.delete("/ausencias/{ausencia_id}", status_code=204)
async def deletar_ausencia(
    ausencia_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    await producao_service.deletar_ausencia(db, ausencia_id, current_user)
