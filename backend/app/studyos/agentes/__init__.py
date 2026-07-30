"""Implementações concretas dos agentes especializados.

Nem todo agente precisa de modelo: os que apenas derivam estrutura do que o
usuário informou são determinísticos e vivem aqui. O runner consulta este
registro antes de cair no briefing genérico.
"""

from typing import Any, Callable

from app.studyos.agentes import (
    adaptativo,
    aula,
    conhecimento,
    curriculo,
    dependencias,
    dificuldade,
    exemplos,
    exercicios,
    flashcards,
    memoria,
    objetivo,
    perfil,
    resumos,
    revisao,
    roadmap,
    simulado,
)

#: código do agente -> função que recebe o payload de entradas e devolve o conteúdo
IMPLEMENTACOES: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {
    "01": perfil.analisar,
    "02": objetivo.analisar,
    "03": conhecimento.analisar,
    "04": curriculo.construir,
    "05": dependencias.mapear,
    "06": roadmap.construir,
    "07": aula.gerar,
    "08": exemplos.gerar,
    "09": exercicios.gerar,
    "10": flashcards.gerar,
    "11": resumos.gerar,
    "12": dificuldade.detectar,
    "13": adaptativo.adaptar,
    "14": memoria.agendar,
    "15": revisao.planejar,
    "16": simulado.gerar,
}

__all__ = [
    "IMPLEMENTACOES",
    "adaptativo",
    "aula",
    "conhecimento",
    "curriculo",
    "dependencias",
    "dificuldade",
    "exemplos",
    "exercicios",
    "flashcards",
    "memoria",
    "objetivo",
    "perfil",
    "resumos",
    "revisao",
    "roadmap",
    "simulado",
]
