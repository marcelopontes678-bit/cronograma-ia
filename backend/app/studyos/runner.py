"""Execução dos agentes especializados.

O orquestrador não sabe *como* um agente produz sua saída — só sabe pedir.
Trocar o runner troca o motor (stub determinístico, LLM, serviço externo) sem
tocar no grafo nem na consolidação.
"""

from __future__ import annotations

import asyncio
import inspect
from dataclasses import dataclass, field
from typing import Awaitable, Callable, Protocol

from app.studyos.agentes import IMPLEMENTACOES
from app.studyos.agents import AgentResult, AgentSpec


@dataclass
class ContextoExecucao:
    """Tudo que um agente pode ler no momento em que roda."""

    solicitacao: str
    #: Dados fornecidos pelo usuário (perfil, objetivo, prazo, nível...).
    dados_usuario: dict = field(default_factory=dict)
    #: Saídas já produzidas por outros agentes, indexadas por código.
    saidas: dict[str, AgentResult] = field(default_factory=dict)

    def entradas_de(self, spec: AgentSpec, dependencias: tuple[str, ...]) -> dict:
        """Monta o payload de entrada do agente a partir das dependências."""
        return {
            "solicitacao": self.solicitacao,
            "dados_usuario": dict(self.dados_usuario),
            #: Campos que a spec do agente declara consumir — usado para relatar
            #: lacunas sem impedir o agente de ler o contexto completo.
            "campos_declarados": list(spec.entradas_do_usuario),
            "saidas_anteriores": {
                codigo: self.saidas[codigo].conteudo
                for codigo in dependencias
                if codigo in self.saidas
            },
        }


def _aceita_redator(implementacao: Callable) -> bool:
    try:
        return "redator" in inspect.signature(implementacao).parameters
    except (TypeError, ValueError):  # pragma: no cover - builtins/callables exóticos
        return False


class AgentRunner(Protocol):
    """Contrato de execução de um agente."""

    async def executar(
        self, spec: AgentSpec, entradas: dict
    ) -> AgentResult:  # pragma: no cover - protocolo
        ...


class RunnerEstrutural:
    """Runner padrão, determinístico e offline.

    Agentes com implementação concreta (registro ``studyos.agentes``) rodam de
    verdade. Os demais devolvem o *briefing* estruturado — tarefa, entradas
    efetivamente recebidas e o que faltou — sem inventar conteúdo de estudo.
    A regra "nunca invente informações" vale também para o motor de execução.
    """

    #: Campos que cada agente ainda sem implementação precisa do usuário.
    CAMPOS_ESPERADOS: dict[str, tuple[str, ...]] = {
        "16": ("historico",),
        "17": ("historico",),
        "21": ("historico",),
    }

    def __init__(self, redatores: dict[str, Callable[[dict], dict]] | None = None):
        """``redatores`` conecta um modelo aos agentes que produzem conteúdo.

        A chave é o código do agente (por exemplo ``"07"``); o valor recebe o
        briefing montado pelo agente e devolve as seções redigidas. O agente
        continua dono das regras — o redator só escreve.
        """
        self._redatores = dict(redatores or {})

    async def executar(self, spec: AgentSpec, entradas: dict) -> AgentResult:
        implementacao = IMPLEMENTACOES.get(spec.codigo)
        if implementacao is not None:
            redator = self._redatores.get(spec.codigo)
            if redator is not None and _aceita_redator(implementacao):
                #: O redator real faz chamadas de rede bloqueantes (httpx
                #: síncrono). Rodar direto travaria o event loop inteiro —
                #: inclusive outros agentes da mesma onda e, num servidor
                #: vivo, qualquer outra requisição em andamento.
                conteudo = await asyncio.to_thread(
                    implementacao, entradas, redator=redator
                )
            else:
                conteudo = implementacao(entradas)
            return AgentResult(
                codigo=spec.codigo,
                nome=spec.nome,
                fase=spec.fase,
                tarefa=spec.tarefa,
                conteudo=conteudo,
                lacunas=list(conteudo.get("lacunas", [])),
            )

        dados = entradas.get("dados_usuario", {})
        disponiveis = {k: v for k, v in dados.items() if v not in (None, "", [], {})}

        lacunas = [
            campo
            for campo in self.CAMPOS_ESPERADOS.get(spec.codigo, ())
            if campo not in disponiveis
        ]

        conteudo = {
            "tarefa": spec.tarefa,
            "entradas_recebidas": {
                "do_usuario": sorted(disponiveis),
                "de_agentes": sorted(entradas.get("saidas_anteriores", {})),
            },
            "status": "pendente_de_geracao",
            "observacao": (
                "Briefing montado pelo orquestrador. A geração de conteúdo exige "
                "um runner com modelo conectado."
            ),
        }
        return AgentResult(
            codigo=spec.codigo,
            nome=spec.nome,
            fase=spec.fase,
            tarefa=spec.tarefa,
            conteudo=conteudo,
            lacunas=lacunas,
        )


class RunnerDelegado:
    """Adapta uma função assíncrona qualquer ao contrato de runner.

    A função recebe ``(spec, entradas)`` e devolve o conteúdo do agente — é o
    ponto de conexão com um modelo, um serviço interno ou um mock de teste.
    """

    def __init__(self, funcao: Callable[[AgentSpec, dict], Awaitable[dict]]):
        self._funcao = funcao

    async def executar(self, spec: AgentSpec, entradas: dict) -> AgentResult:
        conteudo = await self._funcao(spec, entradas)
        if not isinstance(conteudo, dict):
            conteudo = {"resultado": conteudo}
        return AgentResult(
            codigo=spec.codigo,
            nome=spec.nome,
            fase=spec.fase,
            tarefa=spec.tarefa,
            conteudo=conteudo,
            lacunas=list(conteudo.get("lacunas", [])),
        )
