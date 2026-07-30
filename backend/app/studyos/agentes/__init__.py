"""Implementações concretas dos agentes especializados.

Nem todo agente precisa de modelo: os que apenas derivam estrutura do que o
usuário informou são determinísticos e vivem aqui. O runner consulta este
registro antes de cair no briefing genérico.
"""

from typing import Any, Callable

from app.studyos.agentes import perfil

#: código do agente -> função que recebe o payload de entradas e devolve o conteúdo
IMPLEMENTACOES: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {
    "01": perfil.analisar,
}

__all__ = ["IMPLEMENTACOES", "perfil"]
