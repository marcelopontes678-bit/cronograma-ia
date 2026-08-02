from fastapi import APIRouter, HTTPException, status

from app.schemas.studyos import (
    AgenteCatalogoResponse,
    OrquestracaoRequest,
    OrquestracaoResponse,
    PlanoResponse,
)
from app.studyos.agents import AGENTES, AGENTES_OBRIGATORIOS, ORDEM_FASES
from app.studyos.graph import CicloDeDependencia, descrever_grafo, fechar_dependencias
from app.studyos.intents import WORKFLOWS, Classificacao, classificar, selecionar_agentes
from app.studyos.orchestrator import MasterOrchestrator, renderizar_markdown
from app.studyos.redator import redatores_reais
from app.studyos.runner import RunnerEstrutural

router = APIRouter(prefix="/studyos", tags=["studyos"])

#: Lido direto do ambiente (nunca de ``app.config``) para preservar o
#: isolamento que os testes da API dependem: este router não exige
#: ``DATABASE_URL`` nem qualquer outra configuração da aplicação principal.
#: Sem ``ANTHROPIC_API_KEY``, ``redatores_reais()`` devolve ``{}`` e o
#: comportamento é idêntico ao runner puramente determinístico.
orchestrator = MasterOrchestrator(runner=RunnerEstrutural(redatores=redatores_reais()))


@router.get("/agentes", response_model=list[AgenteCatalogoResponse])
async def listar_agentes():
    """Catálogo dos 24 agentes especializados."""
    ordenados = sorted(
        AGENTES.values(), key=lambda s: (ORDEM_FASES.index(s.fase), s.codigo)
    )
    return [
        AgenteCatalogoResponse(
            codigo=spec.codigo,
            nome=spec.nome,
            fase=spec.fase.value,
            tarefa=spec.tarefa,
            depende_de=list(spec.depende_de),
            obrigatorio=spec.codigo in AGENTES_OBRIGATORIOS,
        )
        for spec in ordenados
    ]


@router.post("/plano", response_model=PlanoResponse)
async def planejar(data: OrquestracaoRequest):
    """Mostra quais agentes rodariam e em que ordem, sem executar nenhum."""
    if data.intencao is None:
        classificacao = classificar(data.solicitacao)
    else:
        classificacao = Classificacao(
            intencao=data.intencao,
            workflow=WORKFLOWS[data.intencao],
            termos_encontrados=(),
            fallback=False,
        )

    selecionados = fechar_dependencias(selecionar_agentes(classificacao))
    try:
        ordem = descrever_grafo(selecionados)
    except CicloDeDependencia as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        ) from exc

    return PlanoResponse(
        intencao=classificacao.intencao.value,
        workflow=classificacao.workflow.descricao,
        intencao_por_fallback=classificacao.fallback,
        agentes_selecionados=sorted(selecionados),
        ordem_execucao=ordem,
    )


@router.post("/orquestrar", response_model=OrquestracaoResponse)
async def orquestrar(data: OrquestracaoRequest):
    """Executa o fluxo completo e devolve a resposta consolidada."""
    try:
        resultado = await orchestrator.orquestrar(
            solicitacao=data.solicitacao,
            dados_usuario=data.dados_usuario,
            intencao=data.intencao,
        )
    except CicloDeDependencia as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        ) from exc

    payload = resultado.to_dict()
    if data.formato == "markdown":
        payload["resposta_markdown"] = renderizar_markdown(resultado)
    return OrquestracaoResponse(**payload)
