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
from dataclasses import dataclass, field

from app.studyos import validators
from app.studyos.agents import (
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

        classificacao = self._classificar(solicitacao, intencao)
        selecionados = fechar_dependencias(selecionar_agentes(classificacao))
        ondas = ondas_de_execucao(selecionados)

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
                        )
                    )
                    continue
                executaveis.append(codigo)

            if not executaveis:
                continue

            # Regra: agentes sem dependência entre si rodam em paralelo.
            resultados = await asyncio.gather(
                *(self._executar(get_agent(c), contexto, selecionados) for c in executaveis)
            )

            for codigo, (resultado, duracao) in zip(executaveis, resultados):
                spec = get_agent(codigo)
                contexto.saidas[codigo] = resultado
                execucoes.append(
                    ExecucaoAgente(
                        codigo=codigo,
                        nome=spec.nome,
                        fase=spec.fase,
                        tarefa=spec.tarefa,
                        onda=indice,
                        status="concluido" if resultado.ok else "falhou",
                        depende_de=list(dependencias_efetivas(spec, selecionados)),
                        duracao_ms=duracao,
                        detalhe=resultado.erro,
                    )
                )

        validacao = validators.validar(selecionados, contexto.saidas)

        return Orquestracao(
            solicitacao=solicitacao,
            classificacao=classificacao,
            execucoes=execucoes,
            ondas=ondas,
            saidas=contexto.saidas,
            validacao=validacao,
            duracao_ms=(time.perf_counter() - inicio) * 1000,
        )

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
