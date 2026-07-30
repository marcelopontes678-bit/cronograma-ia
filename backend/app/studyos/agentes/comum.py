"""Coerção de entradas compartilhada pelos agentes.

O usuário informa o que quiser no formato que quiser: número como texto, lista
como string separada por vírgula, data em três formatos. Estas funções aceitam
tudo isso — e devolvem ``None``/``[]`` quando o dado não existe, em vez de
inventar um valor.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from app.studyos.intents import normalizar

VAZIOS: tuple = (None, "", [], {}, ())


def como_texto(valor: Any) -> str:
    """Texto normalizado (minúsculo, sem acento) para comparação de termos."""
    if valor is None:
        return ""
    if isinstance(valor, (list, tuple, set)):
        return normalizar(" ".join(str(v) for v in valor))
    return normalizar(str(valor))


def como_lista(valor: Any) -> list[str]:
    """Lista de strings a partir de lista, tupla ou texto separado por vírgula."""
    if valor in VAZIOS:
        return []
    if isinstance(valor, dict):
        return [str(chave).strip() for chave in valor if str(chave).strip()]
    if isinstance(valor, (list, tuple, set)):
        return [str(v).strip() for v in valor if str(v).strip()]
    return [parte.strip() for parte in str(valor).split(",") if parte.strip()]


def como_numero(valor: Any) -> float | None:
    if valor in VAZIOS:
        return None
    if isinstance(valor, bool):
        return None
    try:
        return float(str(valor).replace(",", "."))
    except (ValueError, TypeError):
        return None


def como_data(valor: Any) -> date | None:
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, date):
        return valor
    if not valor:
        return None
    for formato in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(str(valor).strip(), formato).date()
        except ValueError:
            continue
    return None


def como_lista_de_dicts(valor: Any) -> list[dict]:
    """Registros do usuário: um dicionário solto vale como lista de um."""
    if not preenchido(valor):
        return []
    if isinstance(valor, dict):
        return [valor]
    return [item for item in valor if isinstance(item, dict)]


def preenchido(valor: Any) -> bool:
    return valor not in VAZIOS


#: Chaves que descrevem a estrutura de um edital/matriz e não são nomes de conteúdo.
CHAVES_ESTRUTURAIS: tuple[str, ...] = (
    "modulos", "topicos", "conteudos", "subtopicos", "microtopicos",
    "peso", "questoes", "importancia", "obrigatorio", "opcional", "nome",
    "disciplina", "materia",
    # Metadados do nó, não conteúdo dentro dele: sem isso, um tópico que
    # declara pré-requisito vira um "conteúdo" chamado pre_requisitos.
    "pre_requisitos", "pre_requisito", "requisitos", "depende_de",
)


def filhos_estruturais(bruto: Any) -> list[tuple[str, Any]]:
    """Pares ``(nome, filhos)`` de um nível de edital, matriz ou lista.

    Aceita dicionário aninhado, lista de nomes, lista de dicionários com `nome`
    e texto separado por vírgula — os quatro formatos em que um edital costuma
    chegar. Não inventa nível nenhum: o que não estiver escrito sai vazio.
    """
    if not preenchido(bruto):
        return []

    if isinstance(bruto, dict):
        conteudo = {k: v for k, v in bruto.items() if k not in CHAVES_ESTRUTURAIS}
        if conteudo:
            return [(str(nome), filhos) for nome, filhos in conteudo.items()]
        for chave in ("modulos", "topicos", "conteudos", "subtopicos", "microtopicos"):
            if preenchido(bruto.get(chave)):
                return filhos_estruturais(bruto[chave])
        return []

    if isinstance(bruto, (list, tuple)):
        pares: list[tuple[str, Any]] = []
        for item in bruto:
            if isinstance(item, dict):
                nome = item.get("nome") or item.get("disciplina") or item.get("materia")
                if nome:
                    pares.append((str(nome), item))
                else:
                    pares.extend(filhos_estruturais(item))
            elif str(item).strip():
                pares.append((str(item).strip(), None))
        return pares

    return [(nome, None) for nome in como_lista(bruto)]


__all__ = [
    "CHAVES_ESTRUTURAIS",
    "como_data",
    "como_lista",
    "como_numero",
    "como_texto",
    "filhos_estruturais",
    "preenchido",
]
