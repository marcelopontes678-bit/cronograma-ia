"""Agente 14 — Memory Scheduler.

Única responsabilidade: decidir *quando* cada conteúdo volta. Não ensina, não
cria conteúdo, não gera exercícios e **não altera o cronograma principal** — o
plano de revisões é uma camada à parte, que o agente 15 encaixa depois.

Determinístico de ponta a ponta: repetição espaçada é algoritmo, não redação.

Três regras da spec governam o módulo:

* **Nunca revisar o que não foi estudado.** O portão é o mesmo dos agentes 09 e
  10, e conteúdo sem contato registrado não entra no calendário.
* **Nunca remover uma revisão obrigatória.** Quando um dia estoura o limite, as
  revisões excedentes são **remanejadas** para o dia seguinte e o remanejamento
  fica registrado — nenhuma some.
* **Sempre priorizar retenção de longo prazo.** O intervalo da escada de
  repetição é cortado quando a retenção prevista cairia abaixo do alvo antes
  dele: revisar cedo demais custa tempo, revisar tarde demais custa o conteúdo.
"""

from __future__ import annotations

import math
from datetime import date, timedelta
from typing import Any

from app.studyos.agentes.comum import como_data, como_lista, como_numero, como_texto, preenchido

# --------------------------------------------------------------------------- #
# Constantes declaradas
# --------------------------------------------------------------------------- #

#: Meia-vida base da retenção, em dias. É a mesma do agente 03, de propósito:
#: os dois precisam concordar sobre o que "esquecido" significa.
MEIA_VIDA_BASE_DIAS = 30

#: Multiplicadores da meia-vida conforme o domínio medido (agente 03).
FATOR_POR_DOMINIO: dict[str, float] = {
    "avancado": 1.5,
    "intermediario": 1.0,
    "basico": 0.7,
    "nao_conhece": 0.4,
    "indeterminado": 0.7,
}

#: Multiplicadores conforme o nível de dificuldade medido (agente 12).
FATOR_POR_DIFICULDADE: dict[str, float] = {
    "muito_facil": 1.3,
    "facil": 1.1,
    "medio": 1.0,
    "dificil": 0.8,
    "critico": 0.6,
    "indeterminado": 1.0,
}

#: Escada de repetição espaçada, em dias.
INTERVALOS_BASE: tuple[int, ...] = (1, 3, 7, 15, 30, 60)

#: Retenção alvo no momento da revisão — abaixo disso, o conteúdo está se
#: perdendo; muito acima, a revisão é cedo demais.
RETENCAO_ALVO = 0.80

#: Faixas de risco de esquecimento pela retenção estimada.
FAIXAS_DE_RISCO: tuple[tuple[float, str], ...] = (
    (0.80, "baixo"),
    (0.60, "medio"),
    (0.40, "alto"),
    (0.00, "critico"),
)

#: Teto de revisões por dia, para não transformar revisão em sobrecarga.
MAXIMO_REVISOES_POR_DIA = 8

#: Minutos médios por revisão, por método.
MINUTOS_POR_METODO: dict[str, int] = {
    "flashcards": 5,
    "leitura_do_resumo": 8,
    "questoes_comentadas": 12,
    "exercicios": 15,
    "reestudo_da_aula": 25,
}

#: Retenção abaixo da qual o conteúdo precisa ser reestudado, não revisado.
LIMIAR_REESTUDO = 0.30

#: Método indicado por tipo de dificuldade (agente 12).
METODO_POR_DIFICULDADE: dict[str, str] = {
    "memorizacao": "flashcards",
    "procedimental": "exercicios",
    "conceitual": "leitura_do_resumo",
    "interpretacao": "questoes_comentadas",
}

STATUS_ESTUDADO = ("concluido", "em_andamento")


def _classificar_risco(retencao: float) -> str:
    for limite, nome in FAIXAS_DE_RISCO:
        if retencao >= limite:
            return nome
    return "critico"


# --------------------------------------------------------------------------- #
# Histórico de revisões
# --------------------------------------------------------------------------- #


def _historico(campos: dict) -> dict[str, list[dict]]:
    """`conteúdo -> revisões registradas`, em ordem cronológica."""
    registros: list[dict] = []
    for chave in ("historico_revisoes", "revisoes"):
        bruto = campos.get(chave)
        if isinstance(bruto, dict):
            registros.append(bruto)
        elif isinstance(bruto, (list, tuple)):
            registros.extend(item for item in bruto if isinstance(item, dict))

    por_conteudo: dict[str, list[dict]] = {}
    for registro in registros:
        nome = registro.get("conteudo") or registro.get("topico")
        data = como_data(registro.get("data"))
        if not preenchido(nome) or data is None:
            continue
        por_conteudo.setdefault(como_texto(nome), []).append(
            {
                "data": data,
                "resultado": como_texto(registro.get("resultado") or "acerto"),
                "conteudo": nome,
            }
        )
    for revisoes in por_conteudo.values():
        revisoes.sort(key=lambda r: r["data"])
    return por_conteudo


def _indice_da_escada(revisoes: list[dict]) -> tuple[int, int]:
    """Posição na escada de intervalos e número de revisões bem-sucedidas.

    Acerto avança um degrau; erro volta ao começo — o conteúdo que falhou
    precisa reconstruir o espaçamento, não continuar de onde parou.
    """
    indice = 0
    acertos = 0
    for revisao in revisoes:
        if revisao["resultado"] in ("acerto", "sucesso", "ok"):
            indice = min(indice + 1, len(INTERVALOS_BASE) - 1)
            acertos += 1
        else:
            indice = 0
    return indice, acertos


# --------------------------------------------------------------------------- #
# Retenção e intervalo
# --------------------------------------------------------------------------- #


def _meia_vida(dominio: str, dificuldade: str, erros: int) -> dict:
    fator_dominio = FATOR_POR_DOMINIO.get(dominio, 0.7)
    fator_dificuldade = FATOR_POR_DIFICULDADE.get(dificuldade, 1.0)
    fator_erros = 0.8 if erros >= 2 else 1.0

    dias = MEIA_VIDA_BASE_DIAS * fator_dominio * fator_dificuldade * fator_erros
    return {
        "dias": round(dias, 1),
        "fatores": {
            "dominio": fator_dominio,
            "dificuldade": fator_dificuldade,
            "erros": fator_erros,
        },
        "base": (
            f"{MEIA_VIDA_BASE_DIAS}d × {fator_dominio} (domínio {dominio}) × "
            f"{fator_dificuldade} (dificuldade {dificuldade})"
            + (f" × {fator_erros} ({erros} erros)" if fator_erros != 1.0 else "")
        ),
    }


def _retencao(dias_desde_contato: int | None, meia_vida: float) -> float | None:
    if dias_desde_contato is None or meia_vida <= 0:
        return None
    return round(0.5 ** (max(dias_desde_contato, 0) / meia_vida), 4)


def _dias_ate_o_alvo(meia_vida: float) -> int:
    """Dias até a retenção cair ao alvo, a partir de 100%."""
    return max(1, int(meia_vida * math.log(RETENCAO_ALVO) / math.log(0.5)))


def _intervalo(indice_escada: int, meia_vida: float) -> dict:
    """Escada de repetição, cortada pela previsão de esquecimento."""
    da_escada = INTERVALOS_BASE[indice_escada]
    pelo_esquecimento = _dias_ate_o_alvo(meia_vida)
    escolhido = min(da_escada, pelo_esquecimento)

    return {
        "dias": escolhido,
        "da_escada": da_escada,
        "pelo_esquecimento": pelo_esquecimento,
        "degrau": indice_escada + 1,
        "base": (
            f"degrau {indice_escada + 1} da escada ({da_escada}d)"
            + (
                f", cortado para {escolhido}d porque a retenção cairia abaixo de "
                f"{RETENCAO_ALVO:.0%} antes disso"
                if escolhido < da_escada
                else ""
            )
        ),
    }


def _metodo(
    retencao: float | None,
    tipo_de_dificuldade: str | None,
    disponiveis: dict[str, bool],
) -> dict:
    """Escolhe o método — e só recomenda o que existe de verdade."""
    if retencao is not None and retencao < LIMIAR_REESTUDO:
        preferidos = ["reestudo_da_aula", "leitura_do_resumo", "flashcards"]
        base = f"retenção em {retencao:.0%}, abaixo do limiar de reestudo"
    elif tipo_de_dificuldade in METODO_POR_DIFICULDADE:
        preferidos = [
            METODO_POR_DIFICULDADE[tipo_de_dificuldade],
            "flashcards",
            "leitura_do_resumo",
        ]
        base = f"dificuldade {tipo_de_dificuldade} medida pelo agente 12"
    else:
        preferidos = ["flashcards", "leitura_do_resumo", "questoes_comentadas"]
        base = "manutenção por recuperação ativa"

    for metodo in preferidos:
        if disponiveis.get(metodo, True):
            return {
                "metodo": metodo,
                "base": base,
                "minutos": MINUTOS_POR_METODO[metodo],
                "alternativas": [
                    m for m in preferidos if m != metodo and disponiveis.get(m, True)
                ],
            }

    return {
        "metodo": "reestudo_da_aula",
        "base": base + "; nenhum material específico disponível",
        "minutos": MINUTOS_POR_METODO["reestudo_da_aula"],
        "alternativas": [],
    }


# --------------------------------------------------------------------------- #
# Montagem do calendário
# --------------------------------------------------------------------------- #


def _distribuir(agendamentos: list[dict], teto_diario: int) -> list[dict]:
    """Empurra o excedente para o dia seguinte — nenhuma revisão é removida."""
    por_data: dict[str, list[dict]] = {}
    for item in sorted(
        agendamentos, key=lambda a: (a["proxima_revisao"], -a["score_de_prioridade"])
    ):
        data = date.fromisoformat(item["proxima_revisao"])
        while len(por_data.get(data.isoformat(), [])) >= teto_diario:
            data += timedelta(days=1)
            item["remanejada"] = True
        if item.get("remanejada"):
            item["remanejamento"] = {
                "de": item["proxima_revisao"],
                "para": data.isoformat(),
                "motivo": f"limite de {teto_diario} revisões por dia",
            }
            item["proxima_revisao"] = data.isoformat()
        por_data.setdefault(data.isoformat(), []).append(item)
    return agendamentos


def _calendario(agendamentos: list[dict]) -> list[dict]:
    """Agrupa por dia e por disciplina — trocar de assunto custa atenção."""
    por_data: dict[str, list[dict]] = {}
    for item in agendamentos:
        por_data.setdefault(item["proxima_revisao"], []).append(item)

    calendario: list[dict] = []
    for data in sorted(por_data):
        do_dia = por_data[data]
        grupos: dict[str, list[dict]] = {}
        for item in do_dia:
            grupos.setdefault(item["disciplina"] or "sem disciplina", []).append(item)
        calendario.append(
            {
                "data": data,
                "total_de_revisoes": len(do_dia),
                "minutos_estimados": sum(i["minutos_estimados"] for i in do_dia),
                "grupos": [
                    {
                        "disciplina": disciplina,
                        "conteudos": [i["topico"] for i in itens],
                        "metodos": sorted({i["metodo_recomendado"] for i in itens}),
                        "minutos": sum(i["minutos_estimados"] for i in itens),
                    }
                    for disciplina, itens in grupos.items()
                ],
            }
        )
    return calendario


# --------------------------------------------------------------------------- #
# Entrada principal
# --------------------------------------------------------------------------- #


def agendar(entradas: dict[str, Any], hoje: date | None = None) -> dict[str, Any]:
    """Constrói o Plano Inteligente de Revisões."""
    hoje = hoje or date.today()
    dados = entradas.get("dados_usuario", {}) or {}
    campos = {k: v for k, v in dados.items() if k != "perfil"}
    if isinstance(dados.get("perfil"), dict):
        campos = {**campos, **dados["perfil"]}

    anteriores = entradas.get("saidas_anteriores", {})
    mapa_estrategico = anteriores.get("02", {}) or {}
    mapa_conhecimento = anteriores.get("03", {}) or {}
    grafo = anteriores.get("05", {}) or {}
    plano = anteriores.get("06", {}) or {}
    flashcards = anteriores.get("10", {}) or {}
    resumos = anteriores.get("11", {}) or {}
    relatorio = anteriores.get("12", {}) or {}
    adaptacao = anteriores.get("13", {}) or {}

    historico = _historico(campos)
    status_por_topico = {
        como_texto(no["nome"]): no.get("status_curricular")
        for no in grafo.get("nos", [])
    }
    dificuldade_por_topico = {
        como_texto(t["topico"]): t for t in relatorio.get("topicos", [])
    }
    prioridades = {
        como_texto(p["disciplina"]): p["prioridade"]
        for p in mapa_estrategico.get("prioridade_disciplinas", [])
    }

    disponiveis = {
        "flashcards": bool(flashcards.get("flashcards")),
        "leitura_do_resumo": bool(resumos.get("resumo_5min") or resumos.get("resumo_1min")),
        "exercicios": True,
        "questoes_comentadas": True,
        "reestudo_da_aula": True,
    }

    pedidos_de_encurtamento = {
        como_texto(s.get("pedido", "").split(" de ")[-1])
        for s in adaptacao.get("solicitacoes", [])
        if s.get("agente", "").startswith("14")
    }

    data_prova = como_data(campos.get("data_prova")) or como_data(
        (mapa_estrategico.get("prazo_final") or {}).get("data")
    )

    agendamentos: list[dict] = []
    nao_elegiveis: list[dict] = []

    for disciplina in mapa_conhecimento.get("disciplinas", []):
        for medicao in disciplina.get("topicos", []):
            chave = como_texto(medicao["topico"])
            revisoes = historico.get(chave, [])
            estudado = (
                status_por_topico.get(chave) in STATUS_ESTUDADO
                or medicao.get("classificacao") != "indeterminado"
                or bool(revisoes)
            )
            if not estudado:
                nao_elegiveis.append(
                    {
                        "topico": medicao["topico"],
                        "disciplina": disciplina["disciplina"],
                        "motivo": "conteúdo ainda não estudado",
                    }
                )
                continue

            agendamentos.append(
                _agendar_conteudo(
                    medicao,
                    disciplina["disciplina"],
                    revisoes,
                    dificuldade_por_topico.get(chave, {}),
                    prioridades.get(como_texto(disciplina["disciplina"]), "media"),
                    disponiveis,
                    chave in pedidos_de_encurtamento,
                    data_prova,
                    hoje,
                )
            )

    teto = _teto_diario(campos, plano)
    _distribuir(agendamentos, teto)
    calendario = _calendario(agendamentos)

    retencoes = [
        a["nivel_de_retencao"] for a in agendamentos if a["nivel_de_retencao"] is not None
    ]
    return {
        "recalculado_em": hoje.isoformat(),
        "resumo_geral": {
            "total_de_conteudos_monitorados": len(agendamentos),
            "total_de_revisoes_programadas": len(agendamentos),
            "indice_medio_de_retencao": (
                round(sum(retencoes) / len(retencoes), 4) if retencoes else None
            ),
            "risco_medio_de_esquecimento": (
                round(1 - sum(retencoes) / len(retencoes), 4) if retencoes else None
            ),
            "teto_de_revisoes_por_dia": teto,
            "conteudos_nao_elegiveis": len(nao_elegiveis),
        },
        "conteudos": agendamentos,
        "calendario": calendario,
        "nao_elegiveis": nao_elegiveis,
        "remanejadas": [
            {"topico": a["topico"], **a["remanejamento"]}
            for a in agendamentos
            if a.get("remanejamento")
        ],
        "indicadores": _indicadores(agendamentos, campos.get("plano_anterior")),
        "consumido_por": ["15", "16", "17", "18", "19", "21", "22", "23", "24"],
        "observacoes": _observacoes(
            agendamentos, nao_elegiveis, historico, disponiveis, pedidos_de_encurtamento
        ),
        "lacunas": _lacunas(mapa_conhecimento, historico),
        "confiabilidade": (
            "alta" if agendamentos and historico
            else "media" if agendamentos
            else "baixa"
        ),
        "constantes_aplicadas": {
            "meia_vida_base_dias": MEIA_VIDA_BASE_DIAS,
            "intervalos_base": list(INTERVALOS_BASE),
            "retencao_alvo": RETENCAO_ALVO,
            "maximo_revisoes_por_dia": MAXIMO_REVISOES_POR_DIA,
            "limiar_reestudo": LIMIAR_REESTUDO,
            "minutos_por_metodo": MINUTOS_POR_METODO,
        },
    }


def _agendar_conteudo(
    medicao: dict,
    disciplina: str,
    revisoes: list[dict],
    dificuldade: dict,
    prioridade_disciplina: str,
    disponiveis: dict[str, bool],
    encurtar: bool,
    data_prova: date | None,
    hoje: date,
) -> dict:
    dominio = medicao.get("classificacao", "indeterminado")
    nivel_dificuldade = (dificuldade.get("dificuldade") or {}).get("nivel", "indeterminado")
    erros = dificuldade.get("frequencia_de_erros", 0)

    meia_vida = _meia_vida(dominio, nivel_dificuldade, erros)
    indice_escada, acertos = _indice_da_escada(revisoes)

    ultima = revisoes[-1]["data"] if revisoes else None
    if ultima is None and medicao.get("dias_sem_contato") is not None:
        ultima = hoje - timedelta(days=int(medicao["dias_sem_contato"]))

    dias_desde = (hoje - ultima).days if ultima else None
    retencao = _retencao(dias_desde, meia_vida["dias"])
    intervalo = _intervalo(indice_escada, meia_vida["dias"])

    dias = intervalo["dias"]
    ajuste = None
    if encurtar:
        # Pedido do agente 13: dificuldade persistente detectada na tutoria.
        dias = max(1, dias // 2)
        ajuste = "intervalo reduzido pela metade a pedido do agente 13"

    proxima = (ultima or hoje) + timedelta(days=dias)
    if proxima <= hoje:
        proxima = hoje
        ajuste = (ajuste + "; " if ajuste else "") + "revisão já vencida, agendada para hoje"

    risco = _classificar_risco(retencao) if retencao is not None else "indeterminado"
    metodo = _metodo(retencao, (dificuldade.get("tipos_de_dificuldade") or {}).get("predominante"), disponiveis)
    prioridade = _prioridade(
        risco, nivel_dificuldade, prioridade_disciplina, data_prova, proxima
    )

    return {
        "id": f"rev-{como_texto(medicao['topico']).replace(' ', '-')}",
        "disciplina": disciplina,
        "topico": medicao["topico"],
        "ultima_revisao": ultima.isoformat() if ultima else None,
        "proxima_revisao": proxima.isoformat(),
        "intervalo_atual_dias": dias,
        "intervalo": {**intervalo, "ajuste": ajuste},
        "meia_vida": meia_vida,
        "nivel_de_retencao": retencao,
        "risco_de_esquecimento": risco,
        "prioridade": prioridade["nivel"],
        "score_de_prioridade": prioridade["score"],
        "base_da_prioridade": prioridade["base"],
        "metodo_recomendado": metodo["metodo"],
        "base_do_metodo": metodo["base"],
        "metodos_alternativos": metodo["alternativas"],
        "minutos_estimados": metodo["minutos"],
        "revisoes_realizadas": len(revisoes),
        "acertos_consecutivos": acertos,
        "dominio_medido": dominio,
        "nivel_de_dificuldade": nivel_dificuldade,
    }


def _prioridade(
    risco: str,
    dificuldade: str,
    prioridade_disciplina: str,
    data_prova: date | None,
    proxima: date,
) -> dict:
    peso_risco = {"critico": 3.0, "alto": 2.0, "medio": 1.0, "baixo": 0.5, "indeterminado": 1.0}
    peso_dificuldade = {"critico": 1.5, "dificil": 1.2, "medio": 1.0, "facil": 0.8, "muito_facil": 0.6}
    peso_disciplina = {"alta": 1.3, "media": 1.0, "baixa": 0.7}

    score = (
        peso_risco.get(risco, 1.0)
        * peso_dificuldade.get(dificuldade, 1.0)
        * peso_disciplina.get(prioridade_disciplina, 1.0)
    )
    fatores = [
        f"risco {risco}",
        f"dificuldade {dificuldade}",
        f"disciplina {prioridade_disciplina}",
    ]
    if data_prova and proxima <= data_prova:
        dias_ate_prova = (data_prova - proxima).days
        if dias_ate_prova <= 30:
            score *= 1.3
            fatores.append(f"{dias_ate_prova} dias da prova")

    nivel = "alta" if score >= 2.5 else "media" if score >= 1.2 else "baixa"
    return {"nivel": nivel, "score": round(score, 2), "base": "; ".join(fatores)}


def _teto_diario(campos: dict, plano: dict) -> int:
    explicito = como_numero(campos.get("maximo_revisoes_por_dia"))
    if explicito:
        return int(explicito)

    for dia in plano.get("cronograma", []):
        for sessao in dia.get("sessoes", []):
            if sessao.get("tipo") == "revisao":
                minutos = float(sessao["tempo_estimado_h"]) * 60
                # O bloco de revisão do agente 06 é o orçamento real do dia.
                cabem = int(minutos // MINUTOS_POR_METODO["flashcards"])
                return max(1, min(MAXIMO_REVISOES_POR_DIA, cabem))
    return MAXIMO_REVISOES_POR_DIA


def _indicadores(agendamentos: list[dict], plano_anterior: Any) -> dict:
    dominados = [a["topico"] for a in agendamentos if a["risco_de_esquecimento"] == "baixo"]
    consolidacao = [
        a["topico"] for a in agendamentos if a["risco_de_esquecimento"] == "medio"
    ]
    criticos = [
        a["topico"]
        for a in agendamentos
        if a["risco_de_esquecimento"] in ("alto", "critico")
    ]

    tendencia = "indeterminada"
    variacao = None
    if isinstance(plano_anterior, dict):
        antes = (plano_anterior.get("resumo_geral") or {}).get("indice_medio_de_retencao")
        atuais = [a["nivel_de_retencao"] for a in agendamentos if a["nivel_de_retencao"]]
        agora = sum(atuais) / len(atuais) if atuais else None
        if antes is not None and agora is not None:
            variacao = round(agora - antes, 4)
            tendencia = (
                "melhorando" if variacao > 0.02
                else "piorando" if variacao < -0.02
                else "estavel"
            )

    return {
        "conteudos_dominados": dominados,
        "conteudos_em_consolidacao": consolidacao,
        "conteudos_criticos": criticos,
        "tendencia_de_retencao": tendencia,
        "evolucao_da_memoria": {
            "variacao_do_indice": variacao,
            "base": (
                "comparação com o plano anterior informado"
                if variacao is not None
                else "nenhum plano anterior informado"
            ),
        },
    }


def _observacoes(
    agendamentos: list[dict],
    nao_elegiveis: list[dict],
    historico: dict,
    disponiveis: dict[str, bool],
    encurtamentos: set[str],
) -> list[str]:
    observacoes: list[str] = []
    if nao_elegiveis:
        observacoes.append(
            f"{len(nao_elegiveis)} conteúdo(s) fora do plano por ainda não terem "
            "sido estudados — revisão de conteúdo novo não existe."
        )
    if not historico:
        observacoes.append(
            "Nenhum histórico de revisões informado: todos os conteúdos começam "
            "no primeiro degrau da escada de repetição."
        )
    sem_data = [a["topico"] for a in agendamentos if a["nivel_de_retencao"] is None]
    if sem_data:
        observacoes.append(
            f"{len(sem_data)} conteúdo(s) sem data de contato registrada: a "
            "retenção não foi estimada e a revisão foi agendada pelo primeiro "
            "degrau da escada — "
            + ", ".join(sem_data)
        )
    if not disponiveis["flashcards"]:
        observacoes.append(
            "Sem flashcards do agente 10: o método de recuperação ativa por "
            "cartões não foi recomendado."
        )
    if not disponiveis["leitura_do_resumo"]:
        observacoes.append(
            "Sem resumos do agente 11: leitura do resumo não foi recomendada."
        )
    if encurtamentos:
        observacoes.append(
            f"{len(encurtamentos)} intervalo(s) encurtado(s) a pedido do agente 13."
        )
    remanejadas = [a for a in agendamentos if a.get("remanejamento")]
    if remanejadas:
        observacoes.append(
            f"{len(remanejadas)} revisão(ões) remanejada(s) por excesso no dia — "
            "nenhuma foi removida."
        )
    observacoes.append(
        "Este plano não altera o cronograma principal: o encaixe é do agente 15."
    )
    return observacoes


def _lacunas(mapa_conhecimento: dict, historico: dict) -> list[str]:
    lacunas: list[str] = []
    if not mapa_conhecimento:
        lacunas.append("mapa_de_conhecimento_do_agente_03")
    if not historico:
        lacunas.append("historico_revisoes")
    return lacunas


__all__ = [
    "INTERVALOS_BASE",
    "MEIA_VIDA_BASE_DIAS",
    "MINUTOS_POR_METODO",
    "RETENCAO_ALVO",
    "agendar",
]
