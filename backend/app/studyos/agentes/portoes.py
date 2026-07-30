"""Portões compartilhados entre os agentes de produção.

Regras que mais de um agente precisa aplicar do mesmo jeito. Ficam aqui para
que "conteúdo não estudado" signifique exatamente a mesma coisa no agente 09 e
no 10 — e para que corrigir a regra corrija os dois.
"""

from __future__ import annotations

from typing import Any

from app.studyos.agentes.comum import como_texto, preenchido

#: Status do currículo que contam como "já estudado".
STATUS_ESTUDADO = ("concluido", "em_andamento")


def localizar_no(grafo: dict, aula: dict, solicitado: Any) -> dict | None:
    """Encontra o nó do Grafo de Aprendizagem por id, por nome ou pela aula."""
    nos = grafo.get("nos", [])
    alvo = como_texto(solicitado) if preenchido(solicitado) else None
    if alvo is None and aula.get("conteudo"):
        alvo = como_texto(aula["conteudo"]["nome"])
    if alvo is None:
        return None
    for no in nos:
        if no["id"] == solicitado or como_texto(no["nome"]) == alvo:
            return no
    return None


def conteudo_estudado(
    aula: dict, no: dict | None, grafo: dict | None = None
) -> dict | None:
    """Devolve o bloqueio quando o conteúdo ainda não foi estudado.

    "Estudado" é uma de duas coisas: a aula do agente 07 foi redigida, ou o
    conteúdo já consta como concluído/em andamento no currículo — que é o caso
    de quem estudou antes de entrar no StudyOS.
    """
    if aula.get("status") == "gerada":
        return None
    if no is not None and no.get("status_curricular") in STATUS_ESTUDADO:
        return None

    if no is not None and no.get("status") == "bloqueado":
        por_id = {n["id"]: n["nome"] for n in (grafo or {}).get("nos", [])}
        pendentes = [por_id.get(pre, pre) for pre in no.get("bloqueado_por", [])]
        return {
            "motivo": "conteudo_bloqueado",
            "detalhe": (
                "O conteúdo depende de pré-requisitos não concluídos: "
                + ", ".join(pendentes)
            ),
            "acao": "Estudar os pré-requisitos antes.",
        }

    if not aula and no is None:
        return {
            "motivo": "conteudo_ausente",
            "detalhe": "Nenhuma aula do agente 07 nem conteúdo identificado no grafo.",
            "acao": "Indicar o conteúdo ou gerar a aula.",
        }

    return {
        "motivo": "conteudo_nao_estudado",
        "detalhe": (
            "A aula existe em estrutura, mas não foi redigida, e o conteúdo não "
            "consta como estudado."
            if aula
            else "O conteúdo ainda não foi estudado."
        ),
        "acao": "Estudar o conteúdo antes.",
    }


__all__ = ["STATUS_ESTUDADO", "conteudo_estudado", "localizar_no"]
