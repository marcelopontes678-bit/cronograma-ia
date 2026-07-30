"""Resolução do grafo de dependências entre agentes.

Duas garantias que o Master Orchestrator precisa e que vivem aqui:

* nenhum agente roda antes de suas entradas existirem (ordem topológica);
* agentes sem dependência entre si rodam na mesma onda (execução paralela).
"""

from __future__ import annotations

from app.studyos.agents import AGENTES, ORDEM_FASES, AgentSpec, get_agent


class CicloDeDependencia(Exception):
    """O conjunto de agentes selecionado contém um ciclo — fluxo inexecutável."""

    def __init__(self, pendentes: set[str]):
        self.pendentes = sorted(pendentes)
        super().__init__(
            "Ciclo de dependência entre os agentes: " + ", ".join(self.pendentes)
        )


def fechar_dependencias(codigos: set[str]) -> set[str]:
    """Expande a seleção com todas as dependências transitivas.

    Um agente selecionado sem seus pré-requisitos é um agente que rodaria sem
    entrada; em vez de pular o agente, o orquestrador puxa o que falta.
    """
    resolvidos: set[str] = set()
    pilha = list(codigos)
    while pilha:
        codigo = pilha.pop()
        if codigo in resolvidos:
            continue
        spec = get_agent(codigo)
        resolvidos.add(codigo)
        pilha.extend(spec.depende_de)
    return resolvidos


def dependencias_efetivas(spec: AgentSpec, selecionados: set[str]) -> tuple[str, ...]:
    """Dependências do agente dentro do fluxo selecionado.

    Um agente ``agrega_tudo`` (Validators) depende de todos os demais agentes do
    fluxo, e não de uma lista fixa.
    """
    if spec.agrega_tudo:
        return tuple(sorted(c for c in selecionados if c != spec.codigo))
    return tuple(d for d in spec.depende_de if d in selecionados)


def ondas_de_execucao(codigos: set[str]) -> list[list[str]]:
    """Agrupa os agentes em ondas; cada onda roda em paralelo.

    A onda ``n`` só contém agentes cujas dependências já foram satisfeitas pelas
    ondas ``0..n-1``.
    """
    selecionados = fechar_dependencias(codigos)
    pendentes = dict.fromkeys(sorted(selecionados))
    concluidos: set[str] = set()
    ondas: list[list[str]] = []

    while pendentes:
        onda = [
            codigo
            for codigo in pendentes
            if concluidos.issuperset(
                dependencias_efetivas(get_agent(codigo), selecionados)
            )
        ]
        if not onda:
            raise CicloDeDependencia(set(pendentes))

        onda.sort(key=_chave_de_ordenacao)
        ondas.append(onda)
        concluidos.update(onda)
        for codigo in onda:
            del pendentes[codigo]

    return ondas


def _chave_de_ordenacao(codigo: str) -> tuple[int, str]:
    spec = get_agent(codigo)
    return (ORDEM_FASES.index(spec.fase), spec.codigo)


def descrever_grafo(codigos: set[str]) -> list[dict]:
    """Descrição serializável do plano de execução (usada na resposta da API)."""
    selecionados = fechar_dependencias(codigos)
    descricao: list[dict] = []
    for indice, onda in enumerate(ondas_de_execucao(selecionados), start=1):
        descricao.append(
            {
                "onda": indice,
                "paralelo": len(onda) > 1,
                "agentes": [
                    {
                        "codigo": codigo,
                        "nome": AGENTES[codigo].nome,
                        "fase": AGENTES[codigo].fase.value,
                        "depende_de": list(
                            dependencias_efetivas(AGENTES[codigo], selecionados)
                        ),
                    }
                    for codigo in onda
                ],
            }
        )
    return descricao
