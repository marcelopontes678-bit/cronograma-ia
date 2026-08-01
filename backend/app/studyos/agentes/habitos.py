"""Agente 20 — Habit Builder.

Única responsabilidade: transformar estudo em rotina sustentável. Não ensina,
não cria cronograma, não gera exercício, não altera o plano.

A diferença entre este agente e o 19: o Coach olha para o **desempenho** e diz
o que fazer com ele; o Habit Builder olha para o **comportamento** e ajusta a
meta até ela ser cumprível. Os dois leem o mesmo registro de frequência, pelo
mesmo código (`frequencia.py`), para nunca falarem dois números sobre o mesmo
estudante.

Três decisões estruturais:

* **A meta sai do que foi feito, não do que seria ideal.** Ela é ancorada na
  mediana das sessões reais e limitada pela disponibilidade declarada. Meta
  que o estudante nunca cumpriu não é meta: é a próxima frustração agendada.
* **Evolução gradual é um teto, não um conselho.** O passo máximo entre metas
  é uma constante, e subir só é permitido com adesão alta. Consistência baixa
  faz a meta *descer* — que é exatamente o que o agente 19 pede quando sugere
  "reduzir a meta diária".
* **Nunca punir.** Reforço só existe em variedade positiva, e todo texto passa
  pelo filtro de punição e de manipulação antes de sair. Hábito negativo é
  descrito como obstáculo observado, nunca como falha de caráter.
"""

from __future__ import annotations

import statistics
from datetime import date, timedelta
from typing import Any

from app.studyos.agentes.coach import TERMOS_MANIPULATIVOS
from app.studyos.agentes.comum import (
    como_data,
    como_lista_de_dicts,
    como_numero,
    como_texto,
    preenchido,
)
from app.studyos.agentes.frequencia import (
    consistencia as consistencia_de,
    dias_estudados,
    dias_planejados,
    melhor_sequencia,
    sequencia_ate,
    sessoes_registradas,
)

# --------------------------------------------------------------------------- #
# Constantes declaradas
# --------------------------------------------------------------------------- #

#: Janela de observação do comportamento, em dias. Mais longa que a do agente
#: 19 porque hábito é medido em semanas, não em dias.
JANELA_DE_OBSERVACAO_DIAS = 28

#: Observações mínimas para afirmar qualquer padrão — horário bom, dia ruim,
#: hábito consolidado. Abaixo disso é coincidência com nome de padrão.
MINIMO_DE_OBSERVACOES = 3

#: Adesão a partir da qual um hábito é considerado consolidado, e o mínimo de
#: dias observados para essa afirmação valer.
ADESAO_PARA_CONSOLIDAR = 0.80
DIAS_PARA_CONSOLIDAR = 14

#: Adesão a partir da qual um hábito conta como "em formação".
ADESAO_PARA_EM_FORMACAO = 0.40

#: Passo máximo de aumento da meta entre um plano e o seguinte. Evolução
#: gradual precisa de um número: sem teto, "gradual" vira opinião.
PASSO_MAXIMO_DE_AUMENTO = 0.20

#: Adesão mínima para a meta poder subir. Aumentar meta que ainda não é
#: cumprida é programar a próxima quebra de rotina.
ADESAO_PARA_AUMENTAR = 0.80

#: Adesão abaixo da qual a meta desce, e quanto ela desce.
ADESAO_PARA_REDUZIR = 0.50
PASSO_DE_REDUCAO = 0.25

#: Piso da meta diária. Abaixo disso não sustenta hábito nenhum.
MINUTOS_MINIMOS_DE_META = 10

#: Dias sem estudo que caracterizam risco de quebra de rotina.
DIAS_PARA_RISCO_DE_QUEBRA = 2

#: Marcos de sequência que o agente persegue, em dias.
MARCOS_DE_SEQUENCIA = (3, 7, 14, 21, 30, 60, 90)

#: Reforços disponíveis — todos positivos por construção. Não existe variedade
#: "punitiva" nesta tabela, e é isso que garante a regra "nunca punir".
REFORCOS_POSITIVOS: dict[str, str] = {
    "marco": "registrar o marco alcançado no próprio painel de progresso",
    "constancia": "reconhecer a sequência atual antes de propor o próximo passo",
    "retomada": "tratar a volta como recomeço, sem cobrança pelo intervalo",
    "meta_cumprida": "confirmar a meta cumprida no dia em que ela foi cumprida",
}

#: Termos de punição: perda, castigo e vergonha. Somados aos manipulativos do
#: agente 19, formam o filtro por onde todo texto deste agente passa.
TERMOS_PUNITIVOS: tuple[str, ...] = (
    "voce perdeu",
    "perdeu o direito",
    "como castigo",
    "penalidade por",
    "so podera",
    "nao merece",
    "zerou tudo",
    "comeca do zero de novo",
)

DIAS_DA_SEMANA = (
    "segunda", "terca", "quarta", "quinta", "sexta", "sabado", "domingo",
)

#: Faixas horárias em que uma sessão pode cair.
FAIXAS_HORARIAS: tuple[tuple[int, int, str], ...] = (
    (5, 12, "manha"),
    (12, 18, "tarde"),
    (18, 23, "noite"),
    (23, 5, "madrugada"),
)


class TextoPunitivo(Exception):
    """Texto que pune, ameaça ou envergonha o estudante."""


def _validar_texto(texto: str) -> None:
    normalizado = como_texto(texto)
    for termo in TERMOS_PUNITIVOS + TERMOS_MANIPULATIVOS:
        if termo in normalizado:
            raise TextoPunitivo(f"texto contém termo punitivo ou manipulativo: '{termo}'")


# --------------------------------------------------------------------------- #
# Rotina observada
# --------------------------------------------------------------------------- #


def _faixa_horaria(hora: Any) -> str | None:
    numero = como_numero(str(hora).split(":")[0]) if preenchido(hora) else None
    if numero is None or not 0 <= numero <= 23:
        return None
    for inicio, fim, nome in FAIXAS_HORARIAS:
        if inicio <= fim and inicio <= numero < fim:
            return nome
        if inicio > fim and (numero >= inicio or numero < fim):
            return nome
    return None


def _rotina(sessoes: list[dict]) -> dict:
    """Quando o estudante estuda de fato, com a amostra que sustenta a leitura."""
    por_faixa: dict[str, dict] = {}
    for sessao in sessoes:
        if not sessao["houve_estudo"]:
            continue
        faixa = _faixa_horaria(sessao["hora"])
        if faixa is None:
            continue
        registro = por_faixa.setdefault(
            faixa,
            {"faixa": faixa, "sessoes": 0, "concluidas": 0, "minutos": [], "datas": []},
        )
        registro["sessoes"] += 1
        registro["concluidas"] += 0 if sessao["interrompida"] else 1
        registro["datas"].append(sessao["data"])
        if sessao["minutos"]:
            registro["minutos"].append(sessao["minutos"])

    faixas = [
        {
            "faixa": r["faixa"],
            "sessoes": r["sessoes"],
            "taxa_de_conclusao": round(r["concluidas"] / r["sessoes"], 4),
            "minutos_medianos": (
                round(statistics.median(r["minutos"]), 1) if r["minutos"] else None
            ),
            # O período observado é o intervalo real entre a primeira e a
            # última sessão da faixa — não a janela de análise. Hábito
            # observado em 8 dias não virou hábito de 28.
            "dias_observados": (max(r["datas"]) - min(r["datas"])).days + 1,
        }
        for r in por_faixa.values()
    ]
    faixas.sort(key=lambda f: (-f["taxa_de_conclusao"], -f["sessoes"]))

    com_amostra = [f for f in faixas if f["sessoes"] >= MINIMO_DE_OBSERVACOES]
    return {
        "faixas_observadas": faixas,
        "melhor_faixa": com_amostra[0] if com_amostra else None,
        "base": (
            f"faixa com mais sessões concluídas entre as que têm ao menos "
            f"{MINIMO_DE_OBSERVACOES} observações"
            if com_amostra
            else (
                f"nenhuma faixa horária atingiu {MINIMO_DE_OBSERVACOES} sessões; "
                "melhor horário não declarado"
            )
        ),
    }


def _padroes_por_dia(
    planejados: list[date], estudados: list[date]
) -> dict:
    """Dias da semana que o estudante mais deixa passar."""
    faltas: dict[str, dict] = {}
    estudados_set = set(estudados)
    for dia in planejados:
        nome = DIAS_DA_SEMANA[dia.weekday()]
        registro = faltas.setdefault(nome, {"dia": nome, "planejados": 0, "faltas": 0})
        registro["planejados"] += 1
        registro["faltas"] += 0 if dia in estudados_set else 1

    candidatos = [
        {**r, "taxa_de_falta": round(r["faltas"] / r["planejados"], 4)}
        for r in faltas.values()
        if r["planejados"] >= MINIMO_DE_OBSERVACOES and r["faltas"]
    ]
    candidatos.sort(key=lambda r: -r["taxa_de_falta"])
    return {
        "dias_de_maior_falta": candidatos,
        "base": (
            f"dias da semana com ao menos {MINIMO_DE_OBSERVACOES} ocorrências "
            "planejadas na janela"
        ),
    }


def _interrupcoes(campos: dict, sessoes: list[dict]) -> dict:
    """Motivos que aparecem mais de uma vez viram obstáculo; um só é episódio."""
    motivos: dict[str, int] = {}
    total = 0
    for bruto in como_lista_de_dicts(campos.get("historico_interrupcoes")):
        motivo = bruto.get("motivo") or "não informado"
        motivos[motivo] = motivos.get(motivo, 0) + 1
        total += 1
    for sessao in sessoes:
        if sessao["interrompida"]:
            motivo = sessao["motivo"] or "não informado"
            motivos[motivo] = motivos.get(motivo, 0) + 1
            total += 1

    recorrentes = sorted(
        (
            {"motivo": motivo, "ocorrencias": n}
            for motivo, n in motivos.items()
            if n >= 2
        ),
        key=lambda m: -m["ocorrencias"],
    )
    return {
        "total": total,
        "recorrentes": recorrentes,
        "episodicos": [
            {"motivo": motivo, "ocorrencias": n} for motivo, n in motivos.items() if n < 2
        ],
        "base": "motivo repetido é obstáculo; ocorrência única é episódio",
    }


# --------------------------------------------------------------------------- #
# Hábitos
# --------------------------------------------------------------------------- #


def _habitos(
    campos: dict,
    planejados: list[date],
    estudados: list[date],
    rotina: dict,
    hoje: date,
) -> tuple[list[dict], list[dict]]:
    """Hábitos positivos observados, separados por grau de consolidação."""
    positivos: list[dict] = []
    estudados_set = set(estudados)

    if planejados:
        adesao = len([d for d in planejados if d in estudados_set]) / len(planejados)
        dias_observados = (max(planejados) - min(planejados)).days + 1
        positivos.append(
            {
                "habito": "estudar nos dias planejados",
                "adesao": round(adesao, 4),
                "observacoes": len(planejados),
                "dias_observados": dias_observados,
                "base": (
                    f"{len([d for d in planejados if d in estudados_set])} de "
                    f"{len(planejados)} dias planejados cumpridos"
                ),
            }
        )

    melhor = rotina["melhor_faixa"]
    if melhor:
        positivos.append(
            {
                "habito": f"estudar no período da {melhor['faixa']}",
                "adesao": melhor["taxa_de_conclusao"],
                "observacoes": melhor["sessoes"],
                "dias_observados": melhor["dias_observados"],
                "base": (
                    f"{melhor['sessoes']} sessões nessa faixa, "
                    f"{melhor['taxa_de_conclusao']:.0%} concluídas"
                ),
            }
        )

    for declarado in como_lista_de_dicts(campos.get("historico_habitos")):
        nome = declarado.get("habito") or declarado.get("nome")
        adesao = como_numero(declarado.get("adesao"))
        if preenchido(nome) and adesao is not None:
            positivos.append(
                {
                    "habito": nome,
                    "adesao": round(adesao, 4),
                    "observacoes": int(como_numero(declarado.get("observacoes")) or 0),
                    "dias_observados": int(
                        como_numero(declarado.get("dias_observados")) or 0
                    ),
                    "base": "hábito informado pelo estudante",
                }
            )

    consolidados = [
        {**h, "estado": "consolidado"}
        for h in positivos
        if h["adesao"] >= ADESAO_PARA_CONSOLIDAR
        and h["observacoes"] >= MINIMO_DE_OBSERVACOES
        and h["dias_observados"] >= DIAS_PARA_CONSOLIDAR
    ]
    nomes = {h["habito"] for h in consolidados}
    em_formacao = [
        {
            **h,
            "estado": "em_formacao",
            "falta_para_consolidar": (
                f"adesão de {ADESAO_PARA_CONSOLIDAR:.0%} por "
                f"{DIAS_PARA_CONSOLIDAR} dias"
            ),
        }
        for h in positivos
        if h["habito"] not in nomes and h["adesao"] >= ADESAO_PARA_EM_FORMACAO
    ]
    return consolidados, em_formacao


def _habitos_negativos(
    padroes: dict, interrupcoes: dict, ausencia: int | None, rotina: dict
) -> dict:
    """Obstáculos observados. Descrição de comportamento, nunca de caráter."""
    obstaculos: list[dict] = []
    recorrentes: list[dict] = []
    riscos: list[dict] = []

    for motivo in interrupcoes["recorrentes"]:
        obstaculos.append(
            {
                "obstaculo": motivo["motivo"],
                "ocorrencias": motivo["ocorrencias"],
                "base": "motivo de interrupção registrado mais de uma vez",
            }
        )

    for dia in padroes["dias_de_maior_falta"]:
        recorrentes.append(
            {
                "comportamento": f"{dia['dia']} planejada sem estudo",
                "ocorrencias": dia["faltas"],
                "taxa": dia["taxa_de_falta"],
                "base": f"{dia['faltas']} falta(s) em {dia['planejados']} ocorrências",
            }
        )

    if ausencia is not None and ausencia >= DIAS_PARA_RISCO_DE_QUEBRA:
        riscos.append(
            {
                "situacao": f"{ausencia} dias sem estudo registrado",
                "base": (
                    f"limite de {DIAS_PARA_RISCO_DE_QUEBRA} dias para risco de "
                    "quebra de rotina"
                ),
            }
        )
    for faixa in rotina["faixas_observadas"]:
        if faixa["sessoes"] >= MINIMO_DE_OBSERVACOES and faixa["taxa_de_conclusao"] < 0.5:
            riscos.append(
                {
                    "situacao": f"sessões no período da {faixa['faixa']} raramente terminam",
                    "base": (
                        f"{faixa['taxa_de_conclusao']:.0%} de conclusão em "
                        f"{faixa['sessoes']} sessões"
                    ),
                }
            )

    return {
        "principais_obstaculos": obstaculos,
        "comportamentos_recorrentes": recorrentes,
        "situacoes_de_risco": riscos,
    }


# --------------------------------------------------------------------------- #
# Metas: cumpríveis por construção
# --------------------------------------------------------------------------- #


def _disponibilidade(perfil: dict, campos: dict) -> dict:
    """Minutos por dia que o estudante declarou ter. É o teto de tudo."""
    declarado = como_numero(campos.get("horas_por_dia"))
    do_perfil = (perfil.get("tempo_disponivel") or {}).get("horas_por_dia_declaradas")
    horas = declarado if declarado is not None else como_numero(do_perfil)
    if horas is None:
        return {"minutos": None, "base": "disponibilidade diária não informada"}
    return {
        "minutos": round(horas * 60, 1),
        "base": f"{horas:g}h/dia declaradas pelo estudante",
    }


def _meta_diaria(
    sessoes: list[dict],
    adesao: float | None,
    disponibilidade: dict,
    meta_anterior: float | None,
) -> dict:
    """Meta ancorada no que foi feito, limitada pelo que o estudante tem.

    A mediana, e não a média, porque um domingo de seis horas não define a
    rotina de ninguém — e é justamente ele que puxaria a média para uma meta
    que o estudante nunca mais cumpre.
    """
    minutos = [s["minutos"] for s in sessoes if s["houve_estudo"] and s["minutos"]]
    fatores: list[str] = []

    if not minutos and meta_anterior is None:
        return {
            "minutos": None,
            "base": (
                "nenhuma sessão com duração registrada; meta diária não definida "
                "sem base de comparação"
            ),
            "ajuste": None,
            "fatores": [],
        }

    base_atual = (
        round(statistics.median(minutos), 1) if minutos else float(meta_anterior or 0)
    )
    if minutos:
        fatores.append(f"mediana de {len(minutos)} sessões registradas")

    referencia = float(meta_anterior) if meta_anterior else base_atual
    ajuste = "mantida"
    proposta = referencia

    if adesao is None:
        ajuste = "ancorada no observado"
        proposta = base_atual
        fatores.append("sem adesão medida: meta espelha o que já é feito")
    elif adesao < ADESAO_PARA_REDUZIR:
        ajuste = "reduzida"
        proposta = referencia * (1 - PASSO_DE_REDUCAO)
        fatores.append(
            f"adesão de {adesao:.0%}, abaixo de {ADESAO_PARA_REDUZIR:.0%}: "
            "meta reduzida para voltar a ser cumprida"
        )
    elif adesao >= ADESAO_PARA_AUMENTAR:
        ajuste = "aumentada"
        proposta = referencia * (1 + PASSO_MAXIMO_DE_AUMENTO)
        fatores.append(
            f"adesão de {adesao:.0%}: aumento de no máximo "
            f"{PASSO_MAXIMO_DE_AUMENTO:.0%} sobre a meta anterior"
        )
    else:
        fatores.append(
            f"adesão de {adesao:.0%}: meta mantida até estabilizar em "
            f"{ADESAO_PARA_AUMENTAR:.0%}"
        )

    limite = disponibilidade["minutos"]
    if limite is not None and proposta > limite:
        proposta = limite
        ajuste = "limitada pela disponibilidade"
        fatores.append(f"teto de {limite:g} min/dia ({disponibilidade['base']})")

    proposta = max(MINUTOS_MINIMOS_DE_META, round(proposta, 1))
    return {
        "minutos": proposta,
        "base": (
            f"meta anterior de {meta_anterior:g} min ajustada pela adesão"
            if meta_anterior
            else f"mediana das sessões registradas ({base_atual:g} min)"
        ),
        "ajuste": ajuste,
        "fatores": fatores,
    }


def _meta_semanal(meta_diaria: dict, plano: dict, perfil: dict, campos: dict) -> dict:
    """Meta semanal = meta diária × dias que o estudante realmente reservou."""
    if meta_diaria["minutos"] is None:
        return {"minutos": None, "dias": None, "base": "sem meta diária definida"}

    dias = como_numero(campos.get("dias_por_semana")) or como_numero(
        (perfil.get("tempo_disponivel") or {}).get("dias_por_semana_declarados")
    )
    if dias is None:
        semana = (plano.get("resumo_geral") or {}).get("dias_de_estudo_por_semana")
        dias = len(semana) if semana else None
    if dias is None:
        return {
            "minutos": None,
            "dias": None,
            "base": "dias de estudo por semana não informados",
        }
    return {
        "minutos": round(meta_diaria["minutos"] * dias, 1),
        "dias": int(dias),
        "base": f"meta diária × {int(dias)} dias de estudo por semana",
    }


def _proximo_marco(sequencia: dict, melhor: dict) -> dict | None:
    atual = sequencia["dias"]
    for marco in MARCOS_DE_SEQUENCIA:
        if marco > atual:
            return {
                "marco": f"{marco} dias seguidos",
                "faltam": marco - atual,
                "sequencia_atual": atual,
                "melhor_ja_alcancada": melhor["dias"],
                "reforco": REFORCOS_POSITIVOS["marco"],
            }
    return None


def _habito_prioritario(
    negativos: dict, em_formacao: list[dict], consolidados: list[dict]
) -> dict | None:
    """Um alvo por vez: hábito construído em paralelo não é hábito, é lista."""
    if negativos["comportamentos_recorrentes"]:
        alvo = negativos["comportamentos_recorrentes"][0]
        return {
            "habito": f"cumprir o estudo na {alvo['comportamento'].split(' planejada')[0]}",
            "motivo": alvo["base"],
            "origem": "comportamento recorrente observado",
        }
    if em_formacao:
        alvo = max(em_formacao, key=lambda h: h["adesao"])
        return {
            "habito": alvo["habito"],
            "motivo": f"adesão de {alvo['adesao']:.0%}; {alvo['falta_para_consolidar']}",
            "origem": "hábito em formação mais próximo de consolidar",
        }
    if consolidados:
        return {
            "habito": consolidados[0]["habito"],
            "motivo": "manter o que já está consolidado",
            "origem": "hábito consolidado",
        }
    return None


def _estrategia_de_manutencao(
    adesao: float | None, sequencia: dict, riscos: list[dict], rotina: dict
) -> dict:
    reforcos: list[str] = []
    if sequencia["dias"] >= MINIMO_DE_OBSERVACOES:
        reforcos.append(REFORCOS_POSITIVOS["constancia"])
    if sequencia["dias"] == 0:
        reforcos.append(REFORCOS_POSITIVOS["retomada"])
    reforcos.append(REFORCOS_POSITIVOS["meta_cumprida"])

    if riscos:
        acao = "encurtar a sessão até ela voltar a ser concluída todo dia"
        base = riscos[0]["base"]
    elif rotina["melhor_faixa"]:
        acao = f"ancorar a sessão no período da {rotina['melhor_faixa']['faixa']}"
        base = rotina["base"]
    elif adesao is not None and adesao >= ADESAO_PARA_AUMENTAR:
        acao = "manter o mesmo horário até o hábito consolidar"
        base = f"adesão de {adesao:.0%} na janela observada"
    else:
        acao = "registrar o horário de cada sessão para achar a melhor janela"
        base = "sem horário registrado não há como identificar o melhor momento"

    return {"acao": acao, "base": base, "reforcos": reforcos}


# --------------------------------------------------------------------------- #
# Indicadores
# --------------------------------------------------------------------------- #


def _frequencia_periodica(estudados: list[date], hoje: date) -> dict:
    semana = [d for d in estudados if (hoje - d).days < 7]
    mes = [d for d in estudados if (hoje - d).days < 30]
    return {
        "semanal": {"dias": len(semana), "base": "últimos 7 dias"},
        "mensal": {"dias": len(mes), "base": "últimos 30 dias"},
    }


def _evolucao_da_consistencia(
    estudados: list[date], plano: dict, hoje: date
) -> dict:
    """Adesão da janela atual contra a anterior, em dias planejados."""
    metade = JANELA_DE_OBSERVACAO_DIAS // 2
    atual = consistencia_de(
        estudados,
        dias_planejados(plano, hoje - timedelta(days=metade - 1), hoje),
        metade,
    )
    anterior = consistencia_de(
        estudados,
        dias_planejados(
            plano,
            hoje - timedelta(days=JANELA_DE_OBSERVACAO_DIAS - 1),
            hoje - timedelta(days=metade),
        ),
        metade,
    )
    if atual["indice"] is None or anterior["indice"] is None:
        return {
            "disponivel": False,
            "tendencia": "indeterminada",
            "base": "não há duas janelas planejadas para comparar",
        }
    variacao = atual["indice"] - anterior["indice"]
    return {
        "disponivel": True,
        "tendencia": (
            "melhora" if variacao >= 0.1
            else "piora" if variacao <= -0.1
            else "estavel"
        ),
        "adesao_atual": atual["indice"],
        "adesao_anterior": anterior["indice"],
        "variacao": round(variacao, 4),
        "base": f"{metade} dias contra os {metade} anteriores",
    }


def _probabilidade_de_manutencao(
    adesao: float | None, sequencia: dict, evolucao: dict, riscos: list[dict]
) -> dict:
    """Estimativa declarada, com a conta à mostra — nunca um número solto."""
    if adesao is None:
        return {
            "probabilidade": None,
            "confianca": "baixa",
            "base": "sem adesão medida não há como estimar manutenção",
            "fatores": [],
        }

    fatores = [f"adesão de {adesao:.0%} na janela"]
    valor = adesao
    if sequencia["dias"] >= MINIMO_DE_OBSERVACOES:
        valor = min(1.0, valor + 0.05)
        fatores.append(f"sequência de {sequencia['dias']} dias")
    if evolucao["disponivel"] and evolucao["tendencia"] == "piora":
        valor = max(0.0, valor - 0.1)
        fatores.append("adesão em queda entre as duas janelas")
    if riscos:
        valor = max(0.0, valor - 0.1)
        fatores.append(f"{len(riscos)} situação(ões) de risco em aberto")

    return {
        "probabilidade": round(valor, 4),
        "confianca": "media" if evolucao["disponivel"] else "baixa",
        "base": (
            "adesão observada ajustada por sequência, tendência e situações de "
            "risco; é projeção comportamental, não previsão de desempenho"
        ),
        "fatores": fatores,
    }


# --------------------------------------------------------------------------- #
# Entrada principal
# --------------------------------------------------------------------------- #

CONSUMIDORES = ["21", "22", "23", "24"]


def _observacoes(
    sessoes: list[dict],
    adesao: float | None,
    rotina: dict,
    meta: dict,
    recusados: list[dict],
) -> list[str]:
    observacoes: list[str] = []

    if not sessoes:
        observacoes.append(
            "Nenhuma sessão registrada: sem histórico de frequência não há hábito "
            "a medir, e o agente não estima comportamento a partir do plano."
        )
        return observacoes
    if adesao is None:
        observacoes.append(
            "Adesão não calculada: nenhum dia planejado na janela observada."
        )
    if rotina["melhor_faixa"] is None:
        observacoes.append(f"Melhor horário não declarado: {rotina['base']}.")
    if meta["minutos"] is None:
        observacoes.append(f"Meta diária não definida: {meta['base']}.")
    elif meta["ajuste"] == "limitada pela disponibilidade":
        observacoes.append(
            "Meta limitada pela disponibilidade declarada: a evolução gradual "
            "para no teto do estudante, nunca acima dele."
        )
    if recusados:
        observacoes.append(
            f"{len(recusados)} texto(s) recusado(s) por conterem punição ou "
            "manipulação. O agente não pune: reforço só existe em variedade positiva."
        )
    return observacoes


def construir(entradas: dict[str, Any], hoje: date | None = None) -> dict[str, Any]:
    """Constrói o Plano de Formação de Hábitos."""
    hoje = hoje or date.today()
    dados = entradas.get("dados_usuario", {}) or {}
    campos = {k: v for k, v in dados.items() if k != "perfil"}
    if isinstance(dados.get("perfil"), dict):
        campos = {**campos, **dados["perfil"]}

    anteriores = entradas.get("saidas_anteriores", {})
    perfil = anteriores.get("01", {}) or {}
    plano = anteriores.get("06", {}) or {}
    revisoes = anteriores.get("15", {}) or {}
    acompanhamento = anteriores.get("19", {}) or {}

    inicio = hoje - timedelta(days=JANELA_DE_OBSERVACAO_DIAS - 1)
    sessoes = [s for s in sessoes_registradas(campos) if inicio <= s["data"] <= hoje]
    estudados = dias_estudados(campos)
    planejados = dias_planejados(plano, inicio, hoje)

    adesao_medida = consistencia_de(estudados, planejados, JANELA_DE_OBSERVACAO_DIAS)
    adesao = adesao_medida["indice"]
    sequencia = sequencia_ate(estudados, hoje)
    melhor = melhor_sequencia(estudados)
    ausencia = (hoje - estudados[-1]).days if estudados else None

    rotina = _rotina(sessoes)
    padroes = _padroes_por_dia(planejados, estudados)
    interrupcoes = _interrupcoes(campos, sessoes)
    consolidados, em_formacao = _habitos(campos, planejados, estudados, rotina, hoje)
    negativos = _habitos_negativos(padroes, interrupcoes, ausencia, rotina)

    disponibilidade = _disponibilidade(perfil, campos)
    meta_anterior = como_numero(
        (campos.get("plano_de_habitos_anterior") or {})
        .get("plano_de_acao", {})
        .get("meta_diaria", {})
        .get("minutos")
    )
    meta_diaria = _meta_diaria(sessoes, adesao, disponibilidade, meta_anterior)
    meta_semanal = _meta_semanal(meta_diaria, plano, perfil, campos)
    evolucao = _evolucao_da_consistencia(estudados, plano, hoje)
    estrategia = _estrategia_de_manutencao(
        adesao, sequencia, negativos["situacoes_de_risco"], rotina
    )

    #: Todo texto endereçado ao estudante passa pelo filtro antes de sair.
    recusados: list[dict] = []
    for rotulo, texto in (
        ("estrategia", estrategia["acao"]),
        *((f"reforco:{i}", r) for i, r in enumerate(estrategia["reforcos"])),
    ):
        try:
            _validar_texto(texto)
        except TextoPunitivo as recusa:
            recusados.append({"onde": rotulo, "texto": texto, "motivo": str(recusa)})
    estrategia["reforcos"] = [
        r for r in estrategia["reforcos"]
        if not any(rec["texto"] == r for rec in recusados)
    ]

    return {
        "atualizado_em": hoje.isoformat(),
        "resumo_geral": {
            "indice_de_consistencia": adesao,
            "base_da_consistencia": adesao_medida["base"],
            "sequencia_atual": sequencia,
            "melhor_sequencia_historica": melhor,
            "frequencia": _frequencia_periodica(estudados, hoje),
            "janela_de_observacao_dias": JANELA_DE_OBSERVACAO_DIAS,
            "engajamento_do_agente_19": (
                acompanhamento.get("resumo_geral") or {}
            ).get("nivel_de_engajamento"),
        },
        "habitos_positivos": {
            "consolidados": consolidados,
            "em_formacao": em_formacao,
            "criterio": (
                f"consolidado: adesão ≥ {ADESAO_PARA_CONSOLIDAR:.0%} com ao menos "
                f"{MINIMO_DE_OBSERVACOES} observações em {DIAS_PARA_CONSOLIDAR} dias"
            ),
        },
        "habitos_negativos": negativos,
        "plano_de_acao": {
            "habito_prioritario": _habito_prioritario(
                negativos, em_formacao, consolidados
            ),
            "meta_diaria": {**meta_diaria, "disponibilidade": disponibilidade},
            "meta_semanal": meta_semanal,
            "proximo_marco": _proximo_marco(sequencia, melhor),
            "estrategia_de_manutencao": estrategia,
        },
        "indicadores": {
            "taxa_de_adesao": adesao,
            "evolucao_da_consistencia": evolucao,
            "tendencia_comportamental": evolucao["tendencia"],
            "probabilidade_de_manutencao": _probabilidade_de_manutencao(
                adesao, sequencia, evolucao, negativos["situacoes_de_risco"]
            ),
            "interrupcoes": interrupcoes,
            "padroes_por_dia": padroes,
            "revisoes_agendadas": len(revisoes.get("sessoes", [])),
        },
        "textos_recusados": recusados,
        "consumido_por": CONSUMIDORES,
        "observacoes": _observacoes(sessoes, adesao, rotina, meta_diaria, recusados),
        "lacunas": [] if sessoes else ["historico_frequencia"],
        "confiabilidade": (
            "alta" if sessoes and adesao is not None and evolucao["disponivel"]
            else "media" if sessoes
            else "baixa"
        ),
        "constantes_aplicadas": {
            "janela_de_observacao_dias": JANELA_DE_OBSERVACAO_DIAS,
            "minimo_de_observacoes": MINIMO_DE_OBSERVACOES,
            "adesao_para_consolidar": ADESAO_PARA_CONSOLIDAR,
            "dias_para_consolidar": DIAS_PARA_CONSOLIDAR,
            "passo_maximo_de_aumento": PASSO_MAXIMO_DE_AUMENTO,
            "adesao_para_aumentar": ADESAO_PARA_AUMENTAR,
            "adesao_para_reduzir": ADESAO_PARA_REDUZIR,
            "passo_de_reducao": PASSO_DE_REDUCAO,
            "minutos_minimos_de_meta": MINUTOS_MINIMOS_DE_META,
            "marcos_de_sequencia": MARCOS_DE_SEQUENCIA,
            "reforcos_positivos": REFORCOS_POSITIVOS,
            "termos_punitivos": TERMOS_PUNITIVOS,
        },
    }


__all__ = [
    "ADESAO_PARA_AUMENTAR",
    "ADESAO_PARA_CONSOLIDAR",
    "ADESAO_PARA_REDUZIR",
    "DIAS_PARA_CONSOLIDAR",
    "DIAS_PARA_RISCO_DE_QUEBRA",
    "JANELA_DE_OBSERVACAO_DIAS",
    "MARCOS_DE_SEQUENCIA",
    "MINIMO_DE_OBSERVACOES",
    "MINUTOS_MINIMOS_DE_META",
    "PASSO_DE_REDUCAO",
    "PASSO_MAXIMO_DE_AUMENTO",
    "REFORCOS_POSITIVOS",
    "TERMOS_PUNITIVOS",
    "TextoPunitivo",
    "construir",
]
