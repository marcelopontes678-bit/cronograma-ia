"""Agente 24 — Validators.

A validação é estrutural, não generativa: ela confere se o fluxo executado
respeitou as regras do orquestrador. Por isso roda sempre no motor, mesmo
quando os demais agentes estão plugados a um modelo.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.studyos.agents import (
    AGENTES_OBRIGATORIOS,
    AgentResult,
    get_agent,
)
from app.studyos.graph import dependencias_efetivas


@dataclass
class Validacao:
    aprovado: bool
    verificacoes: list[str] = field(default_factory=list)
    problemas: list[str] = field(default_factory=list)
    alertas: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "aprovado": self.aprovado,
            "verificacoes": self.verificacoes,
            "problemas": self.problemas,
            "alertas": self.alertas,
        }


def validar(
    selecionados: set[str], saidas: dict[str, AgentResult]
) -> Validacao:
    """Confere o fluxo executado contra as regras do Master Orchestrator."""
    verificacoes: list[str] = []
    problemas: list[str] = []
    alertas: list[str] = []

    executados = {codigo for codigo, r in saidas.items() if r.ok}

    # Regra: nunca pular agentes obrigatórios.
    faltando = [c for c in AGENTES_OBRIGATORIOS if c != "24" and c not in executados]
    if faltando:
        problemas.append(
            "Agentes obrigatórios ausentes: "
            + ", ".join(f"{c} {get_agent(c).nome}" for c in faltando)
        )
    else:
        verificacoes.append("Agentes obrigatórios executados")

    # Regra: nunca executar agente cuja entrada não exista.
    for codigo in sorted(executados):
        spec = get_agent(codigo)
        pendentes = [
            dep
            for dep in dependencias_efetivas(spec, selecionados)
            if dep not in executados
        ]
        if pendentes:
            problemas.append(
                f"{codigo} {spec.nome} rodou sem as entradas de: "
                + ", ".join(pendentes)
            )
    if not problemas:
        verificacoes.append("Toda dependência foi satisfeita antes da execução")

    # Falhas de execução.
    for codigo, resultado in sorted(saidas.items()):
        if not resultado.ok:
            problemas.append(f"{codigo} {resultado.nome} falhou: {resultado.erro}")
        elif not resultado.conteudo:
            problemas.append(f"{codigo} {resultado.nome} devolveu saída vazia")

    # Lacunas de informação: não invalidam o fluxo, mas precisam ser declaradas
    # em vez de preenchidas por invenção.
    for codigo, resultado in sorted(saidas.items()):
        for lacuna in resultado.lacunas:
            alertas.append(
                f"{codigo} {resultado.nome}: informação ausente do usuário — '{lacuna}'"
            )
    if not alertas:
        verificacoes.append("Nenhuma lacuna de informação declarada pelos agentes")

    pendentes_de_geracao = sorted(
        codigo
        for codigo, r in saidas.items()
        if r.conteudo.get("status") == "pendente_de_geracao"
    )
    if pendentes_de_geracao:
        alertas.append(
            "Conteúdo não gerado (runner sem modelo conectado) em: "
            + ", ".join(pendentes_de_geracao)
        )

    return Validacao(
        aprovado=not problemas,
        verificacoes=verificacoes,
        problemas=problemas,
        alertas=alertas,
    )
