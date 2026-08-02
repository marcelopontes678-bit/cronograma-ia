"""Master Orchestrator do StudyOS.

Coordena agentes especializados — nunca ensina, nunca gera conteúdo, nunca
responde ao usuário por conta própria. Faz cinco coisas:

1. interpreta a intenção da solicitação;
2. seleciona os agentes necessários (obrigatórios inclusos);
3. executa em ondas, paralelizando o que não tem dependência;
4. valida o fluxo com o agente 24;
5. consolida e devolve uma única resposta.
"""

from __future__ import annotations

import asyncio
import time
import uuid
from dataclasses import dataclass, field

from app.studyos import acp, validators
from app.studyos.agents import (
    AGENTES_OBRIGATORIOS,
    ORDEM_FASES,
    AgentResult,
    Fase,
    get_agent,
)
from app.studyos.graph import (
    CicloDeDependencia,
    dependencias_efetivas,
    fechar_dependencias,
    ondas_de_execucao,
)
from app.studyos.intents import Classificacao, Intencao, classificar, selecionar_agentes
from app.studyos.runner import AgentRunner, ContextoExecucao, RunnerEstrutural

CODIGO_VALIDATORS = "24"


@dataclass
class ExecucaoAgente:
    """Registro do que aconteceu com um agente no fluxo."""

    codigo: str
    nome: str
    fase: Fase
    tarefa: str
    onda: int
    status: str  # "concluido" | "falhou" | "ignorado"
    depende_de: list[str] = field(default_factory=list)
    duracao_ms: float = 0.0
    detalhe: str | None = None
    #: Confiança do agente na própria saída, derivada do que ele declarou.
    confidence: float = 0.0
    base_da_confidence: str = ""

    def to_dict(self) -> dict:
        return {
            "codigo": self.codigo,
            "nome": self.nome,
            "fase": self.fase.value,
            "tarefa": self.tarefa,
            "onda": self.onda,
            "status": self.status,
            "depende_de": self.depende_de,
            "duracao_ms": round(self.duracao_ms, 2),
            "detalhe": self.detalhe,
            "confidence": round(self.confidence, 2),
            "base_da_confidence": self.base_da_confidence,
        }


@dataclass
class Orquestracao:
    """Resultado final entregue ao usuário."""

    solicitacao: str
    classificacao: Classificacao
    execucoes: list[ExecucaoAgente]
    ondas: list[list[str]]
    saidas: dict[str, AgentResult]
    validacao: validators.Validacao
    duracao_ms: float
    #: Identificador do fluxo — o mesmo em toda mensagem e todo log do ACP.
    workflow_id: str = ""
    #: Trilha completa de mensagens do protocolo, na ordem em que trafegaram.
    mensagens: list[acp.Mensagem] = field(default_factory=list)
    #: Um log por execução, com o que a spec do ACP exige registrar.
    logs: list[acp.Log] = field(default_factory=list)
    #: Entradas do usuário que geraram este fluxo — guardadas para que uma
    #: reexecução parta exatamente do mesmo ponto quando nada mudou.
    dados_usuario: dict = field(default_factory=dict)

    # -- SAÍDA canônica do orquestrador ------------------------------------ #

    @property
    def agentes_executados(self) -> list[dict]:
        return [e.to_dict() for e in self.execucoes if e.status == "concluido"]

    @property
    def ordem_execucao(self) -> list[dict]:
        return [
            {
                "onda": indice,
                "paralelo": len(onda) > 1,
                "agentes": [f"{codigo} {get_agent(codigo).nome}" for codigo in onda],
            }
            for indice, onda in enumerate(self.ondas, start=1)
        ]

    @property
    def tarefas_realizadas(self) -> list[dict]:
        return [
            {
                "agente": f"{e.codigo} {e.nome}",
                "fase": e.fase.value,
                "tarefa": e.tarefa,
                "status": e.status,
            }
            for e in self.execucoes
        ]

    @property
    def resultado_consolidado(self) -> dict:
        por_fase: dict[str, dict] = {}
        for codigo, resultado in sorted(self.saidas.items()):
            if not resultado.ok:
                continue
            fase = por_fase.setdefault(resultado.fase.value, {})
            fase[f"{codigo} {resultado.nome}"] = resultado.conteudo

        lacunas = sorted(
            {
                lacuna
                for resultado in self.saidas.values()
                for lacuna in resultado.lacunas
            }
        )

        return {
            "intencao": self.classificacao.intencao.value,
            "workflow": self.classificacao.workflow.descricao,
            "intencao_por_fallback": self.classificacao.fallback,
            "por_fase": por_fase,
            "validacao": self.validacao.to_dict(),
            "lacunas_de_informacao": lacunas,
            "proximos_passos": self._proximos_passos(lacunas),
            "duracao_ms": round(self.duracao_ms, 2),
        }

    def _proximos_passos(self, lacunas: list[str]) -> list[str]:
        passos: list[str] = []
        if lacunas:
            passos.append(
                "Informar ao StudyOS: " + ", ".join(lacunas)
                + " — os agentes declararam essas lacunas em vez de assumir valores."
            )
        if self.validacao.problemas:
            passos.append(
                "Reexecutar o fluxo após corrigir: "
                + "; ".join(self.validacao.problemas)
            )
        if self.classificacao.fallback:
            passos.append(
                "Solicitação genérica: o ciclo completo foi executado. "
                "Um pedido mais específico reduz o número de agentes."
            )
        return passos

    def to_dict(self) -> dict:
        return {
            "agentes_executados": self.agentes_executados,
            "ordem_execucao": self.ordem_execucao,
            "tarefas_realizadas": self.tarefas_realizadas,
            "resultado_consolidado": self.resultado_consolidado,
        }


class MasterOrchestrator:
    def __init__(self, runner: AgentRunner | None = None):
        self._runner = runner or RunnerEstrutural()

    async def orquestrar(
        self,
        solicitacao: str,
        dados_usuario: dict | None = None,
        intencao: Intencao | None = None,
    ) -> Orquestracao:
        inicio = time.perf_counter()
        workflow_id = f"wf-{uuid.uuid4().hex[:12]}"
        mensagens: list[acp.Mensagem] = []
        logs: list[acp.Log] = []
        memoria = acp.MemoriaCompartilhada(workflow_id)

        classificacao = self._classificar(solicitacao, intencao)
        selecionados = fechar_dependencias(selecionar_agentes(classificacao))
        ondas = ondas_de_execucao(selecionados)

        memoria.publicar(acp.MASTER_ORCHESTRATOR, "intencao", classificacao.intencao.value)
        memoria.publicar(acp.MASTER_ORCHESTRATOR, "agentes_selecionados", sorted(selecionados))

        contexto = ContextoExecucao(
            solicitacao=solicitacao, dados_usuario=dict(dados_usuario or {})
        )
        execucoes: list[ExecucaoAgente] = []

        for indice, onda in enumerate(ondas, start=1):
            executaveis: list[str] = []

            for codigo in onda:
                spec = get_agent(codigo)
                dependencias = dependencias_efetivas(spec, selecionados)
                # Regra: nunca executar um agente cuja entrada ainda não exista.
                faltando = [
                    dep
                    for dep in dependencias
                    if dep not in contexto.saidas or not contexto.saidas[dep].ok
                ]
                if faltando and codigo != CODIGO_VALIDATORS:
                    motivo = "entradas indisponíveis: " + ", ".join(faltando)
                    contexto.saidas[codigo] = AgentResult(
                        codigo=codigo,
                        nome=spec.nome,
                        fase=spec.fase,
                        tarefa=spec.tarefa,
                        conteudo={},
                        erro=motivo,
                    )
                    execucoes.append(
                        ExecucaoAgente(
                            codigo=codigo,
                            nome=spec.nome,
                            fase=spec.fase,
                            tarefa=spec.tarefa,
                            onda=indice,
                            status="ignorado",
                            depende_de=list(dependencias),
                            detalhe=motivo,
                            confidence=acp.CONFIDENCE_DE_FALHA,
                            base_da_confidence="agente não executado",
                        )
                    )
                    mensagens.append(
                        acp.Mensagem(
                            workflow_id=workflow_id,
                            source_agent=acp.MASTER_ORCHESTRATOR,
                            target_agent=codigo,
                            action=acp.Acao.ERROR,
                            status=acp.Status.CANCELLED,
                            priority=acp.Prioridade.HIGH,
                            payload=acp.Erro(
                                agent=codigo,
                                motivo=motivo,
                                impacto=f"a fase {spec.fase.value} fica incompleta",
                                workflow_id=workflow_id,
                            ).to_dict(),
                            metadata={"onda": indice},
                        )
                    )
                    continue
                executaveis.append(codigo)

            if not executaveis:
                continue

            # REQUEST: o orquestrador é quem aciona cada agente. Nenhum agente
            # é chamado por outro — a mensagem registra a origem.
            for codigo in executaveis:
                spec = get_agent(codigo)
                mensagens.append(
                    acp.Mensagem(
                        workflow_id=workflow_id,
                        source_agent=acp.MASTER_ORCHESTRATOR,
                        target_agent=codigo,
                        action=(
                            acp.Acao.VALIDATION
                            if codigo == CODIGO_VALIDATORS
                            else acp.Acao.REQUEST
                        ),
                        status=acp.Status.RUNNING,
                        priority=self._prioridade(spec, selecionados),
                        payload=acp.EntradaPadrao(
                            agent=codigo,
                            input={"solicitacao": solicitacao},
                            context={
                                "dependencias": list(
                                    dependencias_efetivas(spec, selecionados)
                                ),
                                "memoria_compartilhada": memoria.como_dicionario(),
                            },
                            constraints=list(spec.entradas_do_usuario),
                            expected_output=spec.tarefa,
                        ).to_dict(),
                        metadata={"onda": indice, "fase": spec.fase.value},
                    )
                )

            # Regra: agentes sem dependência entre si rodam em paralelo.
            resultados = await asyncio.gather(
                *(self._executar(get_agent(c), contexto, selecionados) for c in executaveis)
            )

            for codigo, (resultado, duracao) in zip(executaveis, resultados):
                spec = get_agent(codigo)
                contexto.saidas[codigo] = resultado
                dependencias = list(dependencias_efetivas(spec, selecionados))
                confidence = acp.confidence_de(resultado.conteudo, resultado.ok)

                execucoes.append(
                    ExecucaoAgente(
                        codigo=codigo,
                        nome=spec.nome,
                        fase=spec.fase,
                        tarefa=spec.tarefa,
                        onda=indice,
                        status="concluido" if resultado.ok else "falhou",
                        depende_de=dependencias,
                        duracao_ms=duracao,
                        detalhe=resultado.erro,
                        confidence=confidence["valor"],
                        base_da_confidence=confidence["base"],
                    )
                )

                log = acp.Log(
                    agent=codigo,
                    workflow_id=workflow_id,
                    horario=acp._agora(),
                    tempo_de_execucao_ms=duracao,
                    entrada_recebida=dependencias,
                    saida_produzida=sorted(resultado.conteudo),
                    erros=[resultado.erro] if resultado.erro else [],
                    agentes_acionados=list(resultado.conteudo.get("consumido_por", [])),
                )
                logs.append(log)

                # RESPONSE ou ERROR: a resposta volta ao orquestrador, nunca ao
                # agente seguinte.
                mensagens.append(
                    acp.Mensagem(
                        workflow_id=workflow_id,
                        source_agent=codigo,
                        target_agent=acp.MASTER_ORCHESTRATOR,
                        action=acp.Acao.RESPONSE if resultado.ok else acp.Acao.ERROR,
                        status=(
                            acp.Status.COMPLETED if resultado.ok else acp.Status.FAILED
                        ),
                        priority=self._prioridade(spec, selecionados),
                        payload=acp.SaidaPadrao(
                            agent=codigo,
                            status=(
                                acp.Status.COMPLETED
                                if resultado.ok
                                else acp.Status.FAILED
                            ),
                            confidence=confidence["valor"],
                            result=resultado.conteudo,
                            recommendations=list(resultado.lacunas),
                            next_agents=list(
                                resultado.conteudo.get("consumido_por", [])
                            ),
                            logs=[log.to_dict()],
                        ).to_dict(),
                        metadata={
                            "onda": indice,
                            "base_da_confidence": confidence["base"],
                        },
                    )
                )
                memoria.publicar(
                    acp.MASTER_ORCHESTRATOR, f"confidence:{codigo}", confidence["valor"]
                )

        validacao = validators.validar(selecionados, contexto.saidas)

        # FINISH: o fluxo termina no orquestrador, que é quem entrega.
        mensagens.append(
            acp.Mensagem(
                workflow_id=workflow_id,
                source_agent=acp.MASTER_ORCHESTRATOR,
                target_agent=acp.MASTER_ORCHESTRATOR,
                action=acp.Acao.FINISH,
                status=(
                    acp.Status.COMPLETED if validacao.aprovado else acp.Status.FAILED
                ),
                priority=(
                    acp.Prioridade.NORMAL if validacao.aprovado else acp.Prioridade.CRITICAL
                ),
                payload={
                    "status_da_validacao": validacao.status,
                    "agentes_executados": len(
                        [e for e in execucoes if e.status == "concluido"]
                    ),
                },
                metadata={"protocolo": f"ACP v{acp.VERSAO}"},
            )
        )

        return Orquestracao(
            solicitacao=solicitacao,
            classificacao=classificacao,
            execucoes=execucoes,
            ondas=ondas,
            saidas=contexto.saidas,
            validacao=validacao,
            duracao_ms=(time.perf_counter() - inicio) * 1000,
            workflow_id=workflow_id,
            mensagens=mensagens,
            logs=logs,
            dados_usuario=dict(dados_usuario or {}),
        )

    def _prioridade(self, spec, selecionados: set[str]) -> acp.Prioridade:
        """Prioridade da mensagem: quanto mais gente espera, mais alta.

        Agente obrigatório é CRITICAL porque sem ele não há resposta; agente do
        qual muitos dependem é HIGH porque a fila inteira para atrás dele.
        """
        if spec.codigo in AGENTES_OBRIGATORIOS:
            return acp.Prioridade.CRITICAL
        dependentes = sum(
            1
            for codigo in selecionados
            if spec.codigo in dependencias_efetivas(get_agent(codigo), selecionados)
        )
        if dependentes >= 3:
            return acp.Prioridade.HIGH
        return acp.Prioridade.NORMAL if dependentes else acp.Prioridade.LOW


    async def reexecutar(
        self,
        orquestracao: Orquestracao,
        agentes: set[str],
        motivo: str,
        dados_usuario: dict | None = None,
    ) -> Orquestracao:
        """Reexecuta agentes — só pelos três motivos que o ACP autoriza.

        Um agente nunca se reexecuta por conta própria e nenhum agente pede
        reexecução de outro: o pedido chega ao orquestrador, que é quem
        autoriza. Motivo fora da lista levanta `ReexecucaoNaoAutorizada`.
        """
        acp.autorizar_reexecucao(motivo)

        if motivo == "reprovado_pelo_validator" and orquestracao.validacao.aprovado:
            raise acp.ReexecucaoNaoAutorizada(
                "o validator aprovou o fluxo: não há reprovação que justifique RETRY"
            )

        pedido = acp.Mensagem(
            workflow_id=orquestracao.workflow_id,
            source_agent=acp.MASTER_ORCHESTRATOR,
            target_agent=acp.MASTER_ORCHESTRATOR,
            action=acp.Acao.RETRY,
            status=acp.Status.PENDING,
            priority=acp.Prioridade.HIGH,
            payload={"agentes": sorted(agentes), "motivo": motivo},
            metadata={"fluxo_anterior": orquestracao.workflow_id},
        )

        nova = await self.orquestrar(
            orquestracao.solicitacao,
            dados_usuario=(
                dados_usuario
                if dados_usuario is not None
                else dict(orquestracao.dados_usuario)
            ),
            intencao=orquestracao.classificacao.intencao,
        )
        nova.mensagens.insert(0, pedido)
        return nova

    # -- internos ----------------------------------------------------------- #

    def _classificar(
        self, solicitacao: str, intencao: Intencao | None
    ) -> Classificacao:
        if intencao is None:
            return classificar(solicitacao)
        from app.studyos.intents import WORKFLOWS

        return Classificacao(
            intencao=intencao,
            workflow=WORKFLOWS[intencao],
            termos_encontrados=(),
            fallback=False,
        )

    async def _executar(
        self, spec, contexto: ContextoExecucao, selecionados: set[str]
    ) -> tuple[AgentResult, float]:
        inicio = time.perf_counter()

        if spec.codigo == CODIGO_VALIDATORS:
            parcial = validators.validar(
                selecionados - {CODIGO_VALIDATORS}, dict(contexto.saidas)
            )
            resultado = AgentResult(
                codigo=spec.codigo,
                nome=spec.nome,
                fase=spec.fase,
                tarefa=spec.tarefa,
                conteudo=parcial.to_dict(),
            )
            return resultado, (time.perf_counter() - inicio) * 1000

        dependencias = dependencias_efetivas(spec, selecionados)
        entradas = contexto.entradas_de(spec, dependencias)
        try:
            resultado = await self._runner.executar(spec, entradas)
        except Exception as exc:  # o fluxo continua; o agente é marcado como falho
            resultado = AgentResult(
                codigo=spec.codigo,
                nome=spec.nome,
                fase=spec.fase,
                tarefa=spec.tarefa,
                conteudo={},
                erro=f"{type(exc).__name__}: {exc}",
            )
        return resultado, (time.perf_counter() - inicio) * 1000


def renderizar_markdown(orquestracao: Orquestracao) -> str:
    """Resposta final em texto — o único formato que chega ao usuário."""
    linhas: list[str] = ["# StudyOS — Orquestração", ""]

    linhas.append("## Agentes executados")
    concluidos = [e for e in orquestracao.execucoes if e.status == "concluido"]
    for execucao in concluidos:
        linhas.append(f"- {execucao.codigo} {execucao.nome} ({execucao.fase.value})")
    ignorados = [e for e in orquestracao.execucoes if e.status != "concluido"]
    if ignorados:
        linhas.append("")
        linhas.append("Não executados:")
        for execucao in ignorados:
            linhas.append(
                f"- {execucao.codigo} {execucao.nome} — {execucao.status}: {execucao.detalhe}"
            )

    linhas += ["", "## Ordem de execução"]
    for onda in orquestracao.ordem_execucao:
        marca = " (paralelo)" if onda["paralelo"] else ""
        linhas.append(f"{onda['onda']}.{marca} " + ", ".join(onda["agentes"]))

    linhas += ["", "## Tarefas realizadas"]
    for fase in ORDEM_FASES:
        tarefas = [
            t for t in orquestracao.tarefas_realizadas if t["fase"] == fase.value
        ]
        if not tarefas:
            continue
        linhas.append(f"**{fase.value}**")
        for tarefa in tarefas:
            linhas.append(f"- {tarefa['agente']}: {tarefa['tarefa']}")

    consolidado = orquestracao.resultado_consolidado
    linhas += ["", "## Resultado consolidado"]
    linhas.append(f"- Intenção: {consolidado['intencao']} — {consolidado['workflow']}")
    validacao = consolidado["validacao"]
    linhas.append(
        f"- Validação: {'aprovada' if validacao['aprovado'] else 'reprovada'}"
    )
    for problema in validacao["problemas"]:
        linhas.append(f"  - problema: {problema}")
    for alerta in validacao["alertas"]:
        linhas.append(f"  - alerta: {alerta}")
    for passo in consolidado["proximos_passos"]:
        linhas.append(f"- Próximo passo: {passo}")

    return "\n".join(linhas)


__all__ = [
    "CicloDeDependencia",
    "MasterOrchestrator",
    "Orquestracao",
    "renderizar_markdown",
]
