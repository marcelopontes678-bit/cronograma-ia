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


def preenchido(valor: Any) -> bool:
    return valor not in VAZIOS


__all__ = ["como_data", "como_lista", "como_numero", "como_texto", "preenchido"]
