"""Leitura do registro de frequência, compartilhada pelos agentes 19 e 20.

Os dois olham para os mesmos dias: o Coach para dizer se o estudante está
consistente, o Habit Builder para construir hábito em cima disso. Duas
implementações do mesmo cálculo acabariam divergindo num arredondamento e o
sistema falaria dois números sobre o mesmo comportamento — então o cálculo
mora aqui, uma vez só.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from app.studyos.agentes.comum import como_data, como_lista_de_dicts, como_numero

#: Chaves em que o registro de frequência pode chegar.
CHAVES_DE_FREQUENCIA = ("historico_frequencia", "historico_sessoes", "historico_estudo")


def sessoes_registradas(campos: dict[str, Any]) -> list[dict]:
    """Sessões com data válida, na ordem em que aconteceram.

    Um registro com ``estudou: false`` ou zero minutos é uma ausência
    declarada — ele conta como dia planejado que não virou estudo, e não como
    estudo de duração desconhecida.
    """
    sessoes: list[dict] = []
    for chave in CHAVES_DE_FREQUENCIA:
        for bruto in como_lista_de_dicts(campos.get(chave)):
            data = como_data(bruto.get("data"))
            if data is None:
                continue
            minutos = como_numero(bruto.get("minutos") or bruto.get("tempo_min"))
            houve_estudo = bruto.get("estudou") is not False and (
                minutos is None or minutos > 0
            )
            sessoes.append(
                {
                    "data": data,
                    "minutos": minutos,
                    "hora": bruto.get("hora") or bruto.get("inicio"),
                    "houve_estudo": houve_estudo,
                    "interrompida": bool(bruto.get("interrompida")),
                    "motivo": bruto.get("motivo"),
                    "origem": chave,
                }
            )
    return sorted(sessoes, key=lambda s: s["data"])


def dias_estudados(campos: dict[str, Any]) -> list[date]:
    """Datas em que houve estudo registrado, sem duplicatas."""
    return sorted({s["data"] for s in sessoes_registradas(campos) if s["houve_estudo"]})


def dias_planejados(plano: dict, inicio: date, fim: date) -> list[date]:
    """Dias que o agente 06 reservou para estudo dentro da janela."""
    dias: list[date] = []
    for dia in plano.get("cronograma", []):
        data = como_data(dia.get("data"))
        if data and inicio <= data <= fim:
            dias.append(data)
    return sorted(dias)


def sequencia_ate(estudados: list[date], hoje: date) -> dict:
    """Dias seguidos de estudo terminando hoje ou ontem."""
    if not estudados:
        return {"dias": 0, "base": "nenhum dia de estudo registrado"}

    ultimo = estudados[-1]
    if (hoje - ultimo).days > 1:
        return {
            "dias": 0,
            "base": f"último estudo em {ultimo.isoformat()}, há {(hoje - ultimo).days} dias",
        }

    sequencia = 1
    for anterior, seguinte in zip(reversed(estudados[:-1]), reversed(estudados[1:])):
        if (seguinte - anterior).days != 1:
            break
        sequencia += 1
    return {"dias": sequencia, "base": f"dias consecutivos até {ultimo.isoformat()}"}


def melhor_sequencia(estudados: list[date]) -> dict:
    """A maior sequência já registrada, com o período em que aconteceu."""
    if not estudados:
        return {"dias": 0, "inicio": None, "fim": None, "base": "nenhum dia registrado"}

    melhor = atual = 1
    inicio = fim = inicio_atual = estudados[0]
    for anterior, seguinte in zip(estudados, estudados[1:]):
        if (seguinte - anterior).days == 1:
            atual += 1
        else:
            atual = 1
            inicio_atual = seguinte
        if atual > melhor:
            melhor, inicio, fim = atual, inicio_atual, seguinte

    return {
        "dias": melhor,
        "inicio": inicio.isoformat(),
        "fim": fim.isoformat(),
        "base": f"maior sequência entre {estudados[0]} e {estudados[-1]}",
    }


def consistencia(
    estudados: list[date], planejados: list[date], janela_dias: int
) -> dict:
    """Dias estudados sobre dias planejados — sem plano, sem índice.

    Frequência sozinha não é consistência: estudar 3 dias é ótimo contra uma
    meta de 3 e ruim contra uma meta de 10. Sem denominador devolve ``None`` e
    declara o que falta.
    """
    if not planejados:
        return {
            "indice": None,
            "dias_estudados": len(estudados),
            "dias_planejados": 0,
            "base": (
                "nenhum dia planejado na janela; sem denominador não há índice "
                "de consistência"
            ),
        }

    cumpridos = [d for d in planejados if d in set(estudados)]
    return {
        "indice": round(len(cumpridos) / len(planejados), 4),
        "dias_estudados": len(cumpridos),
        "dias_planejados": len(planejados),
        "base": (
            f"{len(cumpridos)} de {len(planejados)} dias planejados na janela de "
            f"{janela_dias} dias"
        ),
    }


__all__ = [
    "CHAVES_DE_FREQUENCIA",
    "consistencia",
    "dias_estudados",
    "dias_planejados",
    "melhor_sequencia",
    "sequencia_ate",
    "sessoes_registradas",
]
