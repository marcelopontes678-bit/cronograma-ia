"""Implementações concretas dos agentes especializados.

Nem todo agente precisa de modelo: os que apenas derivam estrutura do que o
usuário informou são determinísticos e vivem aqui. O runner consulta este
registro antes de cair no briefing genérico.
"""

from typing import Any, Callable

from app.studyos.agentes import conhecimento, curriculo, objetivo, perfil

#: código do agente -> função que recebe o payload de entradas e devolve o conteúdo
IMPLEMENTACOES: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {
    "01": perfil.analisar,
    "02": objetivo.analisar,
    "03": conhecimento.analisar,
    "04": curriculo.construir,
}

__all__ = ["IMPLEMENTACOES", "conhecimento", "curriculo", "objetivo", "perfil"]
