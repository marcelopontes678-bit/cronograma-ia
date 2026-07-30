"""Classificação de intenção e seleção do conjunto de agentes.

Regra do orquestrador: a intenção decide *quais* agentes participam; o grafo de
dependências decide *quando* cada um roda.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from enum import Enum

from app.studyos.agents import AGENTES_OBRIGATORIOS


class Intencao(str, Enum):
    DIAGNOSTICO = "diagnostico"
    CRIAR_PLANO = "criar_plano"
    ESTUDAR_TOPICO = "estudar_topico"
    GERAR_EXERCICIOS = "gerar_exercicios"
    REVISAR = "revisar"
    SIMULADO = "simulado"
    ANALISE_DESEMPENHO = "analise_desempenho"
    MOTIVACAO = "motivacao"
    COMPLETO = "completo"


@dataclass(frozen=True)
class Workflow:
    intencao: Intencao
    descricao: str
    #: Agentes pedidos explicitamente pela intenção. As dependências são
    #: acrescentadas depois, pelo módulo ``graph``.
    agentes: tuple[str, ...]


WORKFLOWS: dict[Intencao, Workflow] = {
    Intencao.DIAGNOSTICO: Workflow(
        Intencao.DIAGNOSTICO,
        "Diagnóstico de perfil, objetivo e nível atual",
        ("01", "02", "03"),
    ),
    Intencao.CRIAR_PLANO: Workflow(
        Intencao.CRIAR_PLANO,
        "Cronograma completo do objetivo até o prazo",
        ("01", "02", "03", "04", "05", "06", "14", "15", "19", "20"),
    ),
    Intencao.ESTUDAR_TOPICO: Workflow(
        Intencao.ESTUDAR_TOPICO,
        "Produção de aula, exemplos e resumo de um tópico",
        ("04", "07", "08", "11", "12", "13"),
    ),
    Intencao.GERAR_EXERCICIOS: Workflow(
        Intencao.GERAR_EXERCICIOS,
        "Bateria de exercícios calibrada por nível",
        ("04", "09", "12"),
    ),
    Intencao.REVISAR: Workflow(
        Intencao.REVISAR,
        "Flashcards, repetição espaçada e plano de revisão",
        ("10", "11", "14", "15"),
    ),
    Intencao.SIMULADO: Workflow(
        Intencao.SIMULADO,
        "Simulado com correção, análise de erros e pontos fracos",
        ("09", "16", "17", "18"),
    ),
    Intencao.ANALISE_DESEMPENHO: Workflow(
        Intencao.ANALISE_DESEMPENHO,
        "Desempenho, projeção de chegada e otimização do plano",
        ("16", "17", "18", "21", "22", "23"),
    ),
    Intencao.MOTIVACAO: Workflow(
        Intencao.MOTIVACAO,
        "Rotina, hábitos e acompanhamento de ritmo",
        ("06", "19", "20"),
    ),
    Intencao.COMPLETO: Workflow(
        Intencao.COMPLETO,
        "Ciclo completo: diagnóstico, plano, conteúdo, avaliação e otimização",
        tuple(f"{n:02d}" for n in range(1, 24)),
    ),
}


#: Palavras-chave por intenção (texto já normalizado, sem acento e em minúsculas).
PALAVRAS_CHAVE: dict[Intencao, tuple[str, ...]] = {
    Intencao.CRIAR_PLANO: (
        "cronograma", "plano de estudo", "planejar", "planejamento", "roadmap",
        "organizar meus estudos", "quero passar", "me prepare", "trilha",
    ),
    Intencao.ESTUDAR_TOPICO: (
        "aula", "explique", "explica", "me ensine", "entender", "conteudo sobre",
        "estudar sobre", "material de",
    ),
    Intencao.GERAR_EXERCICIOS: (
        "exercicio", "exercicios", "questoes", "questao", "praticar", "lista de",
        "resolver",
    ),
    Intencao.REVISAR: (
        "revisao", "revisar", "flashcard", "flashcards", "memorizar", "decorar",
        "repeticao espacada", "anki",
    ),
    Intencao.SIMULADO: (
        "simulado", "prova", "mock", "teste cronometrado", "simular a prova",
    ),
    Intencao.ANALISE_DESEMPENHO: (
        "desempenho", "resultado", "acertei", "errei", "estatistica", "evolucao",
        "vou conseguir", "projecao", "otimizar", "meu rendimento",
    ),
    Intencao.MOTIVACAO: (
        "motivacao", "desanimado", "procrastin", "habito", "rotina", "disciplina",
        "constancia", "travado",
    ),
    Intencao.DIAGNOSTICO: (
        "diagnostico", "meu nivel", "avaliar meu conhecimento", "por onde comeco",
        "onde estou",
    ),
}


def normalizar(texto: str) -> str:
    sem_acento = "".join(
        c
        for c in unicodedata.normalize("NFD", texto)
        if unicodedata.category(c) != "Mn"
    )
    return re.sub(r"\s+", " ", sem_acento.lower()).strip()


@dataclass(frozen=True)
class Classificacao:
    intencao: Intencao
    workflow: Workflow
    termos_encontrados: tuple[str, ...]
    #: ``True`` quando nenhuma palavra-chave bateu e o fluxo completo foi usado.
    fallback: bool


def classificar(solicitacao: str) -> Classificacao:
    """Escolhe o workflow a partir do texto da solicitação.

    Sem correspondência, cai no ciclo completo — o orquestrador prefere rodar
    mais agentes a adivinhar o que o usuário quis dizer.
    """
    texto = normalizar(solicitacao)

    pontuacao: dict[Intencao, list[str]] = {}
    for intencao, termos in PALAVRAS_CHAVE.items():
        encontrados = [termo for termo in termos if termo in texto]
        if encontrados:
            pontuacao[intencao] = encontrados

    if not pontuacao:
        return Classificacao(
            Intencao.COMPLETO, WORKFLOWS[Intencao.COMPLETO], (), fallback=True
        )

    # Mais termos batidos vence; empate resolve pelo termo mais específico (longo).
    intencao = max(
        pontuacao,
        key=lambda i: (len(pontuacao[i]), max(len(t) for t in pontuacao[i])),
    )
    return Classificacao(
        intencao, WORKFLOWS[intencao], tuple(pontuacao[intencao]), fallback=False
    )


def selecionar_agentes(classificacao: Classificacao) -> set[str]:
    """Agentes do workflow mais os obrigatórios, que nunca são pulados."""
    return set(classificacao.workflow.agentes) | set(AGENTES_OBRIGATORIOS)
