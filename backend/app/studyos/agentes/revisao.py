"""Agente 15 — Revision Planner.

Única responsabilidade: transformar o calendário do agente 14 em sessões
executáveis. Não ensina, não cria conteúdo, não gera exercícios e **não
modifica o Plano de Estudos principal**.

Determinístico. A diferença entre este agente e o 14 é a pergunta que cada um
responde: o 14 decide *quando* cada conteúdo volta; o 15 decide *como aquele
dia vira sessão* — quantas, de que tipo, em que ordem e com qual critério de
conclusão.

Duas regras moldam o módulo:

* **A prioridade do Memory Scheduler é soberana.** O 15 nunca reordena por
  conveniência: quando o tempo não dá para tudo, sai o de menor prioridade — e
  sai declarado, nunca em silêncio.
* **Sessão longa demais não é sessão, é fadiga.** Todo bloco tem teto; o que
  não cabe vira outra sessão, e conteúdo crítico tem limite por sessão porque
  três reestudos seguidos não cabem na mesma cabeça.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from app.studyos.agentes.comum import como_numero, como_texto, preenchido

# --------------------------------------------------------------------------- #
# Constantes declaradas
# --------------------------------------------------------------------------- #

#: Teto de uma sessão de revisão. Acima disso, a atenção cai mais do que rende.
MAXIMO_MINUTOS_POR_SESSAO = 45
#: Abaixo disso não vale abrir sessão — vira anexo da anterior.
MINIMO_MINUTOS_POR_SESSAO = 10

#: Dias extras percorridos para reencaixar uma revisão que não coube.
HORIZONTE_DE_ADIAMENTO_DIAS = 14

#: Conteúdos críticos por sessão. Três reestudos seguidos não cabem na mesma
#: cabeça, por mais que o calendário permita.
MAXIMO_CRITICOS_POR_SESSAO = 2

TIPOS_DE_SESSAO = ("rapida", "aprofundada", "critica")

#: Tipo de sessão conforme o risco de esquecimento medido pelo agente 14.
TIPO_POR_RISCO: dict[str, str] = {
    "baixo": "rapida",
    "medio": "aprofundada",
    "alto": "critica",
    "critico": "critica",
    "indeterminado": "aprofundada",
}

#: Métodos que só existem em sessão — o agente 14 não os agenda, o 15 os aplica.
METODOS_ATIVOS = ("explicacao_ativa", "autoexplicacao")

#: Método complementar por tipo de sessão.
COMPLEMENTO_POR_TIPO: dict[str, str | None] = {
    "rapida": None,
    "aprofundada": "autoexplicacao",
    "critica": "explicacao_ativa",
}

#: Critério de conclusão por método — o que fecha a revisão de verdade.
CRITERIO_POR_METODO: dict[str, str] = {
    "flashcards": "acertar 90% dos cartões sem consultar o material",
    "leitura_do_resumo": "reproduzir os pontos-chave de memória depois da leitura",
    "questoes_comentadas": "justificar a resposta de cada questão, certa ou errada",
    "exercicios": "resolver a bateria sem consultar e conferir o gabarito",
    "reestudo_da_aula": "explicar o conceito em voz alta sem olhar o material",
    "explicacao_ativa": "explicar o conteúdo como se estivesse ensinando outra pessoa",
    "autoexplicacao": "escrever com as próprias palavras por que cada passo funciona",
}

#: Material necessário por método.
MATERIAL_POR_METODO: dict[str, str] = {
    "flashcards": "baralho do agente 10",
    "leitura_do_resumo": "resumo do agente 11",
    "questoes_comentadas": "gabarito comentado do agente 09",
    "exercicios": "bateria do agente 09",
    "reestudo_da_aula": "aula do agente 07",
    "explicacao_ativa": "nenhum — a explicação é oral",
    "autoexplicacao": "papel ou editor de texto",
}

#: Minutos extras do método complementar, por conteúdo.
MINUTOS_DO_COMPLEMENTO = 3

ORDEM_DE_PRIORIDADE = {"alta": 0, "media": 1, "baixa": 2}


# --------------------------------------------------------------------------- #
# Tempo disponível
# --------------------------------------------------------------------------- #


def _tempo_por_dia(campos: dict, plano_de_estudos: dict) -> tuple[dict[str, float], str]:
    """Minutos de revisão disponíveis em cada dia, na ordem de precedência."""
    explicito = como_numero(campos.get("tempo_revisao_min"))
    if explicito:
        return {}, f"informado pelo usuário ({explicito:.0f} min/dia)"

    por_data: dict[str, float] = {}
    for dia in plano_de_estudos.get("cronograma", []):
        minutos = sum(
            float(s["tempo_estimado_h"]) * 60
            for s in dia.get("sessoes", [])
            if s.get("tipo") == "revisao"
        )
        if minutos:
            por_data[dia["data"]] = minutos
    if por_data:
        return por_data, "bloco de revisão do Plano de Estudos (agente 06)"
    return {}, "sem limite declarado: o tempo do agente 14 foi mantido"


def _limite_do_dia(
    data: str, por_data: dict[str, float], campos: dict
) -> float | None:
    explicito = como_numero(campos.get("tempo_revisao_min"))
    if explicito:
        return float(explicito)
    return por_data.get(data)


# --------------------------------------------------------------------------- #
# Montagem das sessões
# --------------------------------------------------------------------------- #


def _intercalar(conteudos: list[dict]) -> list[dict]:
    """Alterna difícil e fácil dentro da sessão, sem quebrar a prioridade.

    A ordem por prioridade decide *quem entra*; a intercalação decide *em que
    ordem se estuda* — empilhar os três críticos no começo esgota o estudante
    antes do resto.
    """
    pesados = [c for c in conteudos if c["risco_de_esquecimento"] in ("alto", "critico")]
    leves = [c for c in conteudos if c not in pesados]

    intercalados: list[dict] = []
    while pesados or leves:
        if pesados:
            intercalados.append(pesados.pop(0))
        if leves:
            intercalados.append(leves.pop(0))
    return intercalados


def _minutos_do_conteudo(conteudo: dict, complemento: str | None) -> float:
    base = float(conteudo.get("minutos_estimados") or 0)
    return base + (MINUTOS_DO_COMPLEMENTO if complemento else 0)


def _sessoes_do_dia(
    data: str,
    conteudos: list[dict],
    limite_minutos: float | None,
    numero_inicial: int,
) -> tuple[list[dict], list[dict]]:
    """Divide o dia em sessões por tipo, respeitando tetos e prioridade."""
    ordenados = sorted(
        conteudos,
        key=lambda c: (
            ORDEM_DE_PRIORIDADE.get(c.get("prioridade"), 1),
            -(c.get("score_de_prioridade") or 0),
        ),
    )

    # Regra: adaptar ao tempo disponível. O corte começa pelo fim da fila de
    # prioridade — nunca pelo começo.
    cabem: list[dict] = []
    fora: list[dict] = []
    acumulado = 0.0
    for conteudo in ordenados:
        tipo = TIPO_POR_RISCO.get(conteudo["risco_de_esquecimento"], "aprofundada")
        minutos = _minutos_do_conteudo(conteudo, COMPLEMENTO_POR_TIPO[tipo])
        if limite_minutos is not None and acumulado + minutos > limite_minutos:
            fora.append(
                {
                    **conteudo,
                    "motivo": (
                        f"tempo de revisão do dia esgotado "
                        f"({limite_minutos:.0f} min disponíveis)"
                    ),
                }
            )
            continue
        acumulado += minutos
        cabem.append(conteudo)

    # Um conteúdo cujo método custa mais que o bloco inteiro do dia nunca
    # caberia — e adiá-lo para sempre é honesto e inútil. Ele entra assim
    # mesmo, sozinho, com o estouro declarado: não revisar é pior que passar
    # alguns minutos do bloco.
    if not cabem and fora:
        forcado = fora.pop(0)
        tipo = TIPO_POR_RISCO.get(forcado["risco_de_esquecimento"], "aprofundada")
        minutos = _minutos_do_conteudo(forcado, COMPLEMENTO_POR_TIPO[tipo])
        cabem.append(
            {
                **{k: v for k, v in forcado.items() if k != "motivo"},
                "excede_o_bloco_do_dia": {
                    "minutos_necessarios": minutos,
                    "minutos_disponiveis": limite_minutos,
                    "motivo": (
                        "o método exigido custa mais que o bloco de revisão do "
                        "dia; adiar indefinidamente seria pior"
                    ),
                },
            }
        )

    por_tipo: dict[str, list[dict]] = {}
    for conteudo in cabem:
        tipo = TIPO_POR_RISCO.get(conteudo["risco_de_esquecimento"], "aprofundada")
        por_tipo.setdefault(tipo, []).append(conteudo)

    sessoes: list[dict] = []
    numero = numero_inicial
    for tipo in TIPOS_DE_SESSAO:
        do_tipo = por_tipo.get(tipo)
        if not do_tipo:
            continue
        for bloco in _dividir_em_blocos(_intercalar(do_tipo), tipo):
            sessoes.append(_montar_sessao(numero, data, tipo, bloco))
            numero += 1
    return sessoes, fora


def _montar_agenda(
    conteudos: list[dict], por_data: dict[str, float], campos: dict
) -> tuple[list[dict], list[dict], list[dict]]:
    """Percorre os dias carregando para frente o que não coube.

    A revisão que não cabe hoje **não é descartada**: ela é adiada para o
    próximo dia com bloco de revisão, do mesmo jeito que o agente 14 remaneja o
    excesso. Só depois do horizonte é que ela vira conteúdo não alocado — e
    ainda assim declarado.
    """
    if not conteudos:
        return [], [], []

    agrupados: dict[str, list[dict]] = {}
    for conteudo in conteudos:
        agrupados.setdefault(conteudo["proxima_revisao"], []).append(conteudo)

    dias = _dias_utilizaveis(sorted(agrupados), por_data, campos)

    sessoes: list[dict] = []
    adiados: list[dict] = []
    pendentes: list[tuple[dict, str]] = []
    numero = 1

    for data in dias:
        do_dia = [(c, data) for c in agrupados.get(data, [])]
        fila = pendentes + do_dia
        pendentes = []
        if not fila:
            continue

        montadas, sobra = _sessoes_do_dia(
            data,
            [c for c, _ in fila],
            _limite_do_dia(data, por_data, campos),
            numero,
        )
        sessoes.extend(montadas)
        numero += len(montadas)

        origem = {c["topico"]: origem_data for c, origem_data in fila}
        for conteudo in sobra:
            original = origem.get(conteudo["topico"], data)
            adiados.append(
                {
                    "topico": conteudo["topico"],
                    "de": data,
                    "prevista_em": original,
                    "motivo": conteudo["motivo"],
                }
            )
            pendentes.append(
                (next(c for c, _ in fila if c["topico"] == conteudo["topico"]), original)
            )

    nao_alocados = [
        {
            "topico": conteudo["topico"],
            "disciplina": conteudo["disciplina"],
            "data_prevista": original,
            "prioridade": conteudo.get("prioridade"),
            "minutos": conteudo.get("minutos_estimados"),
            "motivo": (
                "sem espaço no horizonte de revisão: nenhum dia disponível "
                "comportou este conteúdo"
            ),
        }
        for conteudo, original in pendentes
    ]
    # Adiamentos que terminaram em não alocação não contam como adiamento.
    nomes_nao_alocados = {n["topico"] for n in nao_alocados}
    adiados = [a for a in adiados if a["topico"] not in nomes_nao_alocados]
    return sessoes, nao_alocados, adiados


def _dias_utilizaveis(
    datas_previstas: list[str], por_data: dict[str, float], campos: dict
) -> list[str]:
    """Dias em que revisão pode acontecer, a partir da primeira data prevista."""
    if por_data:
        # Só os dias que o agente 06 reservou para revisão são utilizáveis.
        return sorted(d for d in por_data if d >= datas_previstas[0])

    inicio = date.fromisoformat(datas_previstas[0])
    fim = date.fromisoformat(datas_previstas[-1])
    return [
        (inicio + timedelta(days=n)).isoformat()
        for n in range((fim - inicio).days + HORIZONTE_DE_ADIAMENTO_DIAS + 1)
    ]


def _dividir_em_blocos(conteudos: list[dict], tipo: str) -> list[list[dict]]:
    """Quebra por teto de minutos e por teto de conteúdos críticos."""
    complemento = COMPLEMENTO_POR_TIPO[tipo]
    blocos: list[list[dict]] = []
    atual: list[dict] = []
    minutos = 0.0
    criticos = 0

    for conteudo in conteudos:
        custo = _minutos_do_conteudo(conteudo, complemento)
        e_critico = conteudo["risco_de_esquecimento"] in ("alto", "critico")
        estoura_tempo = atual and minutos + custo > MAXIMO_MINUTOS_POR_SESSAO
        estoura_criticos = (
            e_critico and criticos >= MAXIMO_CRITICOS_POR_SESSAO and atual
        )
        if estoura_tempo or estoura_criticos:
            blocos.append(atual)
            atual, minutos, criticos = [], 0.0, 0

        atual.append(conteudo)
        minutos += custo
        criticos += 1 if e_critico else 0

    if atual:
        blocos.append(atual)

    # Sessão curta demais é anexada à anterior, em vez de virar um bloco solto.
    if len(blocos) > 1:
        ultimo = blocos[-1]
        minutos_do_ultimo = sum(
            _minutos_do_conteudo(c, complemento) for c in ultimo
        )
        if minutos_do_ultimo < MINIMO_MINUTOS_POR_SESSAO:
            blocos[-2].extend(ultimo)
            blocos.pop()
    return blocos


def _montar_sessao(numero: int, data: str, tipo: str, conteudos: list[dict]) -> dict:
    complemento = COMPLEMENTO_POR_TIPO[tipo]
    metodos = sorted({c["metodo_recomendado"] for c in conteudos})
    if complemento:
        metodos.append(complemento)

    duracao = sum(_minutos_do_conteudo(c, complemento) for c in conteudos)
    disciplinas = sorted({c["disciplina"] for c in conteudos if c["disciplina"]})

    return {
        "id": f"sessao-{data}-{numero:02d}",
        "numero": numero,
        "data": data,
        "tipo": tipo,
        "duracao_min": round(duracao, 1),
        "objetivo": _objetivo(tipo, conteudos),
        "conteudos": [
            {
                "topico": c["topico"],
                "disciplina": c["disciplina"],
                "metodo": c["metodo_recomendado"],
                "minutos": _minutos_do_conteudo(c, complemento),
                "risco_de_esquecimento": c["risco_de_esquecimento"],
                "prioridade": c.get("prioridade"),
                "retencao_atual": c.get("nivel_de_retencao"),
                # O estouro de bloco viaja junto: quem lê a sessão precisa saber
                # que aquele item passa do tempo reservado, e por quê.
                **(
                    {"excede_o_bloco_do_dia": c["excede_o_bloco_do_dia"]}
                    if c.get("excede_o_bloco_do_dia")
                    else {}
                ),
            }
            for c in conteudos
        ],
        "metodos_de_revisao": metodos,
        "metodo_complementar": complemento,
        "materiais_necessarios": sorted(
            {MATERIAL_POR_METODO[m] for m in metodos if m in MATERIAL_POR_METODO}
        ),
        "criterios_de_conclusao": [
            {"metodo": m, "criterio": CRITERIO_POR_METODO[m]}
            for m in metodos
            if m in CRITERIO_POR_METODO
        ],
        "meta": _meta(tipo, conteudos, duracao),
        "disciplinas": disciplinas,
        "equilibrio": {
            "pesados": sum(
                1 for c in conteudos if c["risco_de_esquecimento"] in ("alto", "critico")
            ),
            "leves": sum(
                1
                for c in conteudos
                if c["risco_de_esquecimento"] not in ("alto", "critico")
            ),
        },
    }


def _objetivo(tipo: str, conteudos: list[dict]) -> str:
    nomes = ", ".join(c["topico"] for c in conteudos)
    return {
        "rapida": f"Manter a retenção de {nomes} com passagem rápida",
        "aprofundada": f"Consolidar {nomes} com recuperação ativa",
        "critica": f"Recuperar {nomes}, em risco alto de esquecimento",
    }[tipo]


def _meta(tipo: str, conteudos: list[dict], duracao: float) -> dict:
    return {
        "conteudos_a_revisar": len(conteudos),
        "minutos": round(duracao, 1),
        "resultado_esperado": {
            "rapida": "reconhecer todos os conceitos sem hesitação",
            "aprofundada": "explicar cada conceito sem consultar o material",
            "critica": "reconstruir o raciocínio completo do zero",
        }[tipo],
    }


# --------------------------------------------------------------------------- #
# Indicadores
# --------------------------------------------------------------------------- #


def _indicadores(
    sessoes: list[dict], plano_de_revisoes: dict, nao_alocados: list[dict]
) -> dict:
    conteudos_em_sessao = [
        c for sessao in sessoes for c in sessao["conteudos"]
    ]
    total_monitorado = len(plano_de_revisoes.get("conteudos", []))

    por_disciplina: dict[str, int] = {}
    for conteudo in conteudos_em_sessao:
        chave = conteudo["disciplina"] or "sem disciplina"
        por_disciplina[chave] = por_disciplina.get(chave, 0) + 1

    pesados = sum(s["equilibrio"]["pesados"] for s in sessoes)
    leves = sum(s["equilibrio"]["leves"] for s in sessoes)
    duracoes = [s["duracao_min"] for s in sessoes]

    return {
        "cobertura_das_revisoes": (
            round(len(conteudos_em_sessao) / total_monitorado, 4)
            if total_monitorado
            else 0.0
        ),
        "conteudos_em_sessao": len(conteudos_em_sessao),
        "conteudos_monitorados": total_monitorado,
        "conteudos_nao_alocados": len(nao_alocados),
        "distribuicao_por_disciplina": por_disciplina,
        "equilibrio_de_dificuldade": {
            "pesados": pesados,
            "leves": leves,
            "proporcao_pesados": (
                round(pesados / (pesados + leves), 4) if pesados + leves else 0.0
            ),
        },
        "tempo_medio_por_sessao_min": (
            round(sum(duracoes) / len(duracoes), 1) if duracoes else 0.0
        ),
        "percentual_planejado": (
            round(len(conteudos_em_sessao) / total_monitorado, 4)
            if total_monitorado
            else 0.0
        ),
        "sessoes_por_tipo": {
            tipo: sum(1 for s in sessoes if s["tipo"] == tipo) for tipo in TIPOS_DE_SESSAO
        },
    }


def _mudancas(sessoes: list[dict], anteriores: Any) -> dict:
    if not isinstance(anteriores, dict) or not anteriores.get("sessoes"):
        return {
            "houve_replanejamento": False,
            "base": "nenhum plano de sessões anterior informado",
        }

    antes = {s["id"]: s for s in anteriores["sessoes"]}
    agora = {s["id"]: s for s in sessoes}
    return {
        "houve_replanejamento": True,
        "sessoes_novas": sorted(set(agora) - set(antes)),
        "sessoes_removidas": sorted(set(antes) - set(agora)),
        "sessoes_alteradas": sorted(
            identificador
            for identificador in set(antes) & set(agora)
            if antes[identificador]["conteudos"] != agora[identificador]["conteudos"]
        ),
        "base": "comparação com o plano de sessões anterior",
    }


# --------------------------------------------------------------------------- #
# Entrada principal
# --------------------------------------------------------------------------- #


def planejar(entradas: dict[str, Any], hoje: date | None = None) -> dict[str, Any]:
    """Constrói o Plano de Sessões de Revisão."""
    hoje = hoje or date.today()
    dados = entradas.get("dados_usuario", {}) or {}
    campos = {k: v for k, v in dados.items() if k != "perfil"}
    if isinstance(dados.get("perfil"), dict):
        campos = {**campos, **dados["perfil"]}

    anteriores = entradas.get("saidas_anteriores", {})
    plano_de_estudos = anteriores.get("06", {}) or {}
    plano_de_revisoes = anteriores.get("14", {}) or {}

    por_data, origem_do_tempo = _tempo_por_dia(campos, plano_de_estudos)

    sessoes, nao_alocados, adiados = _montar_agenda(
        plano_de_revisoes.get("conteudos", []), por_data, campos
    )

    indicadores = _indicadores(sessoes, plano_de_revisoes, nao_alocados)
    criticos = [
        c["topico"]
        for s in sessoes
        for c in s["conteudos"]
        if c["risco_de_esquecimento"] in ("alto", "critico")
    ]
    prioritarios = [
        c["topico"] for s in sessoes for c in s["conteudos"] if c["prioridade"] == "alta"
    ]

    return {
        "recalculado_em": hoje.isoformat(),
        "resumo_geral": {
            "numero_total_de_sessoes": len(sessoes),
            "tempo_total_de_revisao_min": round(
                sum(s["duracao_min"] for s in sessoes), 1
            ),
            "conteudos_prioritarios": prioritarios,
            "conteudos_criticos": criticos,
            "origem_do_tempo_disponivel": origem_do_tempo,
            "periodo": {
                "inicio": sessoes[0]["data"] if sessoes else None,
                "fim": sessoes[-1]["data"] if sessoes else None,
            },
        },
        "sessoes": sessoes,
        "conteudos_adiados": adiados,
        "conteudos_nao_alocados": nao_alocados,
        "indicadores": indicadores,
        "replanejamento": _mudancas(sessoes, campos.get("sessoes_anteriores")),
        "consumido_por": ["16", "17", "18", "19", "21", "22", "23", "24"],
        "observacoes": _observacoes(
            sessoes, nao_alocados, adiados, plano_de_revisoes, origem_do_tempo
        ),
        "lacunas": [] if plano_de_revisoes else ["plano_de_revisoes_do_agente_14"],
        "confiabilidade": (
            "alta" if sessoes and not nao_alocados
            else "media" if sessoes
            else "baixa"
        ),
        "constantes_aplicadas": {
            "maximo_minutos_por_sessao": MAXIMO_MINUTOS_POR_SESSAO,
            "minimo_minutos_por_sessao": MINIMO_MINUTOS_POR_SESSAO,
            "maximo_criticos_por_sessao": MAXIMO_CRITICOS_POR_SESSAO,
            "tipo_por_risco": TIPO_POR_RISCO,
            "minutos_do_complemento": MINUTOS_DO_COMPLEMENTO,
        },
    }


def _observacoes(
    sessoes: list[dict],
    nao_alocados: list[dict],
    adiados: list[dict],
    plano_de_revisoes: dict,
    origem_do_tempo: str,
) -> list[str]:
    observacoes: list[str] = []
    if not plano_de_revisoes:
        observacoes.append(
            "Nenhum Plano de Revisões recebido do agente 14: não há sessões a montar."
        )
    elif not plano_de_revisoes.get("conteudos"):
        observacoes.append(
            "O agente 14 não elegeu nenhum conteúdo para revisão — conteúdo não "
            "estudado não entra em sessão."
        )
    if adiados:
        observacoes.append(
            f"{len(adiados)} revisão(ões) adiada(s) para o próximo dia com bloco "
            "livre — o corte do dia respeitou a ordem de prioridade do agente 14."
        )
    if nao_alocados:
        observacoes.append(
            f"{len(nao_alocados)} conteúdo(s) sem espaço em nenhum dia do "
            "horizonte. Declarados em conteudos_nao_alocados, não descartados."
        )
    longas = [s for s in sessoes if s["duracao_min"] > MAXIMO_MINUTOS_POR_SESSAO]
    if longas:
        observacoes.append(
            f"{len(longas)} sessão(ões) acima do teto de {MAXIMO_MINUTOS_POR_SESSAO} min."
        )
    observacoes.append(f"Tempo disponível: {origem_do_tempo}.")
    observacoes.append(
        "Este plano não altera o Plano de Estudos principal nem a Árvore "
        "Curricular — ele ocupa o bloco de revisão que o agente 06 já reservou."
    )
    return observacoes


__all__ = [
    "CRITERIO_POR_METODO",
    "MAXIMO_CRITICOS_POR_SESSAO",
    "HORIZONTE_DE_ADIAMENTO_DIAS",
    "MAXIMO_MINUTOS_POR_SESSAO",
    "TIPO_POR_RISCO",
    "planejar",
]
