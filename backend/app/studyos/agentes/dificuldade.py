"""Agente 12 — Difficulty Detector.

Única responsabilidade: medir onde o estudante trava. Não ensina, não cria
cronograma, não gera conteúdo, não avalia aprovação, não toca no Plano de
Estudos nem no Grafo de Dependências.

Como o agente 03, este módulo é inteiramente determinístico e obedece à mesma
regra dura: **nunca assumir dificuldade sem evidência**. Conteúdo sem dado
medido sai com índice ``None`` e nível ``indeterminado`` — nunca "difícil por
precaução". Dificuldade suposta viraria reforço desnecessário lá na frente.

Os quatro tipos de dificuldade (conceitual, procedimental, de interpretação e
de memorização) não são adivinhados: eles saem da **categoria da questão errada**
na taxonomia do agente 09, ou do tipo declarado no relatório de erros.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from app.studyos.agentes.comum import (
    como_data,
    como_lista,
    como_lista_de_dicts,
    como_numero,
    como_texto,
    preenchido,
)

# --------------------------------------------------------------------------- #
# Constantes declaradas
# --------------------------------------------------------------------------- #

#: Peso de cada evidência no Índice de Dificuldade (soma 1.0).
PESOS_DO_INDICE: dict[str, float] = {
    "erro": 0.45,
    "esquecimento": 0.20,
    "tempo": 0.20,
    "recorrencia": 0.15,
}

#: Faixas do Índice de Dificuldade → classificação.
FAIXAS: tuple[tuple[float, str], ...] = (
    (0.20, "muito_facil"),
    (0.40, "facil"),
    (0.60, "medio"),
    (0.80, "dificil"),
    (1.01, "critico"),
)

NIVEIS = tuple(nome for _, nome in FAIXAS)

#: Acima disso, o tempo gasto sinaliza sobrecarga.
LIMIAR_SOBRECARGA_TEMPO = 1.5

#: Abaixo desta retenção, o esquecimento vira componente do índice.
LIMIAR_DECAIMENTO_RELEVANTE = 0.9

#: Número de ocorrências para um erro virar padrão recorrente.
LIMIAR_PADRAO_RECORRENTE = 2

#: Faltas registradas que acendem risco de abandono.
LIMIAR_FALTAS_ABANDONO = 3

#: Variação mínima do índice para a evolução não ser "estável".
LIMIAR_VARIACAO_RELEVANTE = 0.05

#: Categoria da questão errada → tipo de dificuldade que ela revela.
TIPO_POR_CATEGORIA: dict[str, str] = {
    "fixacao": "memorizacao",
    "compreensao": "conceitual",
    "aplicacao": "procedimental",
    "analise": "interpretacao",
    "sintese": "conceitual",
    "desafio": "procedimental",
}

TIPOS_DE_DIFICULDADE = ("conceitual", "procedimental", "interpretacao", "memorizacao")

#: Tipo de erro do agente 17 → vocabulário de dificuldade daqui. Os tipos que
#: não descrevem falha com o conteúdo (atenção, estratégia, gestão do tempo)
#: mapeiam para nada de propósito: são erros de execução da prova.
TIPO_DO_AGENTE_17: dict[str, str | None] = {
    "conceitual": "conceitual",
    "interpretacao": "interpretacao",
    "memorizacao": "memorizacao",
    "calculo": "procedimental",
    "estrategia": None,
    "atencao": None,
    "gestao_do_tempo": None,
}


def _classificar(indice: float | None) -> str:
    if indice is None:
        return "indeterminado"
    for limite, nome in FAIXAS:
        if indice < limite:
            return nome
    return "critico"


# --------------------------------------------------------------------------- #
# Coleta de evidências
# --------------------------------------------------------------------------- #


def _erros_registrados(campos: dict, relatorio_de_erros: dict, exercicios: dict) -> list[dict]:
    """Erros do usuário, do agente 17 ou inferidos do gabarito do agente 09."""
    brutos: list[Any] = []
    brutos.extend(como_lista_de_dicts(campos.get("erros")))
    brutos.extend(como_lista_de_dicts(relatorio_de_erros.get("erros")))

    categoria_por_numero = {
        item["numero"]: item["categoria"]
        for item in exercicios.get("exercicios", [])
        if preenchido(item.get("categoria"))
    }
    conceito_por_numero = {
        item["numero"]: item.get("conceito_alvo")
        for item in exercicios.get("exercicios", [])
    }

    erros: list[dict] = []
    for bruto in brutos:
        numero = como_numero(bruto.get("questao") or bruto.get("numero"))
        categoria = bruto.get("categoria") or (
            categoria_por_numero.get(int(numero)) if numero is not None else None
        )
        tipo = bruto.get("tipo") or TIPO_POR_CATEGORIA.get(como_texto(categoria or ""))
        topico = bruto.get("topico") or bruto.get("conteudo") or (
            conceito_por_numero.get(int(numero)) if numero is not None else None
        )
        erros.append(
            {
                "topico": topico,
                "disciplina": bruto.get("disciplina"),
                "categoria": categoria,
                "tipo": tipo,
                "data": como_data(bruto.get("data")),
            }
        )
    return erros


def _tempos(campos: dict, revisoes: dict) -> dict[str, dict]:
    """Tempo real × estimado por conteúdo, quando houver registro."""
    registros: list[dict] = []
    registros.extend(como_lista_de_dicts(campos.get("historico_sessoes")))
    registros.extend(como_lista_de_dicts(revisoes.get("historico")))

    por_conteudo: dict[str, dict] = {}
    for registro in registros:
        nome = registro.get("conteudo") or registro.get("topico")
        gasto = como_numero(registro.get("tempo_gasto_min"))
        if not preenchido(nome) or gasto is None:
            continue
        alvo = por_conteudo.setdefault(
            como_texto(nome), {"conteudo": nome, "gasto_min": 0.0, "sessoes": 0}
        )
        alvo["gasto_min"] += gasto
        alvo["sessoes"] += 1
        estimado = como_numero(registro.get("tempo_estimado_min"))
        if estimado:
            alvo["estimado_min"] = alvo.get("estimado_min", 0.0) + estimado
    return por_conteudo


def _estimado_da_arvore(arvore: dict) -> dict[str, float]:
    estimados: dict[str, float] = {}
    for disciplina in arvore.get("disciplinas", []):
        for modulo in disciplina.get("modulos", []):
            for topico in modulo.get("topicos", []):
                estimados[como_texto(topico["nome"])] = (
                    float(topico.get("tempo_estimado_h") or 0.0) * 60
                )
                for subtopico in topico.get("subtopicos", []):
                    estimados[como_texto(subtopico["nome"])] = (
                        float(subtopico.get("tempo_estimado_h") or 0.0) * 60
                    )
    return estimados


# --------------------------------------------------------------------------- #
# Índice de dificuldade por tópico
# --------------------------------------------------------------------------- #


def _indice_do_topico(
    medicao: dict,
    erros_do_topico: list[dict],
    tempo: dict | None,
    estimado_min: float | None,
) -> dict:
    """Combina erro, esquecimento, tempo e recorrência — só com o que existe."""
    componentes: dict[str, dict] = {}

    taxa = medicao.get("taxa_acerto")
    if taxa is not None and medicao.get("amostra"):
        componentes["erro"] = {
            "valor": round(1 - taxa, 4),
            "base": f"{medicao['amostra']} questões, {taxa:.0%} de acerto",
        }

    # Só entra quando houve decaimento de fato: retenção intacta não é
    # evidência de facilidade, é ausência de esquecimento — contá-la como
    # componente diluiria o sinal de erro e faria conteúdo crítico parecer
    # apenas difícil.
    retencao = medicao.get("retencao_estimada")
    if retencao is not None and retencao < LIMIAR_DECAIMENTO_RELEVANTE:
        componentes["esquecimento"] = {
            "valor": round(1 - retencao, 4),
            "base": f"retenção estimada de {retencao:.0%}",
        }

    if tempo and estimado_min:
        razao = tempo["gasto_min"] / estimado_min
        componentes["tempo"] = {
            "valor": round(min(1.0, max(0.0, (razao - 1) / 2)), 4),
            "base": (
                f"{tempo['gasto_min']:.0f} min gastos contra {estimado_min:.0f} min "
                f"estimados ({razao:.1f}×)"
            ),
            "razao": round(razao, 2),
        }

    if erros_do_topico:
        componentes["recorrencia"] = {
            "valor": round(min(1.0, len(erros_do_topico) / 5), 4),
            "base": f"{len(erros_do_topico)} erro(s) registrado(s)",
        }

    if not componentes:
        return {
            "indice": None,
            "nivel": "indeterminado",
            "componentes": {},
            "base": "sem evidência medida — dificuldade não é presumida",
            "confianca": "nenhuma",
        }

    peso_total = sum(PESOS_DO_INDICE[c] for c in componentes)
    indice = (
        sum(PESOS_DO_INDICE[c] * dados["valor"] for c, dados in componentes.items())
        / peso_total
    )
    return {
        "indice": round(indice, 4),
        "nivel": _classificar(indice),
        "componentes": componentes,
        "base": "; ".join(dados["base"] for dados in componentes.values()),
        "confianca": (
            "alta" if len(componentes) >= 3 else "media" if len(componentes) == 2 else "baixa"
        ),
    }


def _tipos_de_dificuldade(erros: list[dict]) -> dict:
    contagem = {tipo: 0 for tipo in TIPOS_DE_DIFICULDADE}
    sem_classificacao = 0
    fora_do_conteudo = 0
    for erro in erros:
        tipo = como_texto(erro.get("tipo") or "")
        traduzido = TIPO_DO_AGENTE_17.get(tipo, tipo)
        if traduzido in contagem:
            contagem[traduzido] += 1
        elif tipo in TIPO_DO_AGENTE_17:
            # Classificado pelo agente 17, mas como falha de execução da prova
            # (atenção, estratégia, tempo). Não é dificuldade com o conteúdo, e
            # contá-lo aqui inflaria o índice do tópico.
            fora_do_conteudo += 1
        else:
            sem_classificacao += 1

    detectados = {tipo: n for tipo, n in contagem.items() if n}
    predominante = max(detectados, key=lambda t: detectados[t]) if detectados else None
    return {
        "predominante": predominante,
        "contagem": detectados,
        "erros_sem_classificacao": sem_classificacao,
        "erros_nao_atribuiveis_ao_conteudo": fora_do_conteudo,
        "base": (
            "categoria da questão errada (taxonomia do agente 09) ou tipo "
            "declarado no relatório de erros"
        ),
    }


# --------------------------------------------------------------------------- #
# Agregações
# --------------------------------------------------------------------------- #


def _media(valores: list[float]) -> float | None:
    return round(sum(valores) / len(valores), 4) if valores else None


def _padroes_recorrentes(erros: list[dict]) -> list[dict]:
    por_topico: dict[str, list[dict]] = {}
    por_tipo: dict[str, int] = {}
    for erro in erros:
        if preenchido(erro.get("topico")):
            por_topico.setdefault(como_texto(erro["topico"]), []).append(erro)
        if preenchido(erro.get("tipo")):
            por_tipo[erro["tipo"]] = por_tipo.get(erro["tipo"], 0) + 1

    padroes = [
        {
            "padrao": "erro_repetido_no_topico",
            "alvo": ocorrencias[0]["topico"],
            "ocorrencias": len(ocorrencias),
            "tipos": sorted({o["tipo"] for o in ocorrencias if o["tipo"]}),
        }
        for ocorrencias in por_topico.values()
        if len(ocorrencias) >= LIMIAR_PADRAO_RECORRENTE
    ]
    padroes.extend(
        {
            "padrao": "tipo_de_erro_recorrente",
            "alvo": tipo,
            "ocorrencias": quantidade,
            "tipos": [tipo],
        }
        for tipo, quantidade in por_tipo.items()
        if quantidade >= LIMIAR_PADRAO_RECORRENTE
    )
    padroes.sort(key=lambda p: -p["ocorrencias"])
    return padroes


def _velocidade(tempos: dict[str, dict], estimados: dict[str, float]) -> dict:
    pares = [
        (dados["gasto_min"], estimados[chave])
        for chave, dados in tempos.items()
        if estimados.get(chave)
    ]
    if not pares:
        return {
            "razao_tempo_real_sobre_estimado": None,
            "conteudos_medidos": 0,
            "base": "nenhum tempo de estudo registrado",
            "leitura": None,
        }

    gasto = sum(p[0] for p in pares)
    estimado = sum(p[1] for p in pares)
    razao = gasto / estimado if estimado else None
    return {
        "razao_tempo_real_sobre_estimado": round(razao, 2) if razao else None,
        "minutos_gastos": round(gasto, 1),
        "minutos_estimados": round(estimado, 1),
        "conteudos_medidos": len(pares),
        "leitura": (
            "acima do previsto" if razao and razao > 1.1
            else "abaixo do previsto" if razao and razao < 0.9
            else "dentro do previsto"
        ),
    }


def _sobrecarga(
    perfil: dict, plano: dict, tempos: dict, estimados: dict, topicos: list[dict]
) -> list[dict]:
    sinais: list[dict] = []

    lentos = [
        chave
        for chave, dados in tempos.items()
        if estimados.get(chave)
        and dados["gasto_min"] / estimados[chave] > LIMIAR_SOBRECARGA_TEMPO
    ]
    if lentos:
        sinais.append(
            {
                "sinal": "tempo_muito_acima_do_estimado",
                "severidade": "media",
                "evidencia": f"{len(lentos)} conteúdo(s) acima de {LIMIAR_SOBRECARGA_TEMPO}× o tempo previsto",
            }
        )

    criticos = [t for t in topicos if t["dificuldade"]["nivel"] in ("dificil", "critico")]
    if len(criticos) >= 3:
        sinais.append(
            {
                "sinal": "acumulo_de_conteudos_dificeis",
                "severidade": "alta",
                "evidencia": f"{len(criticos)} tópicos em nível difícil ou crítico ao mesmo tempo",
            }
        )

    if any(r.get("risco") == "sobrecarga" for r in perfil.get("riscos", [])):
        sinais.append(
            {
                "sinal": "carga_diaria_no_teto",
                "severidade": "media",
                "evidencia": "o agente 01 já sinalizou sobrecarga na carga diária declarada",
            }
        )

    faltas = [r for r in plano.get("riscos", []) if r.get("risco") == "faltas_registradas"]
    if faltas:
        sinais.append(
            {
                "sinal": "faltas_no_cronograma",
                "severidade": "media",
                "evidencia": faltas[0]["evidencia"],
            }
        )
    return sinais


def _gargalos(topicos: list[dict], grafo: dict) -> list[dict]:
    """Conteúdo difícil que ainda trava outros — dificuldade × bloqueio."""
    dependentes = {
        no["nome"]: no["dependentes_transitivos"]
        for no in grafo.get("nos", [])
        if no.get("dependentes_transitivos")
    }
    gargalos = [
        {
            "topico": topico["topico"],
            "disciplina": topico["disciplina"],
            "indice_de_dificuldade": topico["dificuldade"]["indice"],
            "nivel": topico["dificuldade"]["nivel"],
            "conteudos_bloqueados": dependentes.get(topico["topico"], 0),
        }
        for topico in topicos
        if topico["dificuldade"]["indice"] is not None
        and topico["dificuldade"]["nivel"] in ("dificil", "critico")
    ]
    gargalos.sort(
        key=lambda g: (-g["conteudos_bloqueados"], -(g["indice_de_dificuldade"] or 0))
    )
    return gargalos


def _evolucao(atuais: list[dict], anterior: dict | None) -> dict:
    if not anterior:
        return {
            "disponivel": False,
            "base": "nenhum relatório anterior informado para comparação",
            "tendencia": "indeterminada",
            "variacoes": [],
        }

    antes = {
        como_texto(t["topico"]): t["dificuldade"]["indice"]
        for disciplina in anterior.get("disciplinas", [])
        for t in disciplina.get("topicos", [])
        if t.get("dificuldade", {}).get("indice") is not None
    }
    variacoes = []
    for topico in atuais:
        indice = topico["dificuldade"]["indice"]
        anterior_indice = antes.get(como_texto(topico["topico"]))
        if indice is None or anterior_indice is None:
            continue
        delta = round(indice - anterior_indice, 4)
        variacoes.append(
            {
                "topico": topico["topico"],
                "antes": anterior_indice,
                "agora": indice,
                "delta": delta,
                "movimento": (
                    "melhorou" if delta <= -LIMIAR_VARIACAO_RELEVANTE
                    else "piorou" if delta >= LIMIAR_VARIACAO_RELEVANTE
                    else "estavel"
                ),
            }
        )

    if not variacoes:
        tendencia = "indeterminada"
    else:
        media = sum(v["delta"] for v in variacoes) / len(variacoes)
        tendencia = (
            "melhorando" if media <= -LIMIAR_VARIACAO_RELEVANTE
            else "piorando" if media >= LIMIAR_VARIACAO_RELEVANTE
            else "estavel"
        )

    return {
        "disponivel": True,
        "tendencia": tendencia,
        "variacoes": variacoes,
        "melhoraram": [v["topico"] for v in variacoes if v["movimento"] == "melhorou"],
        "pioraram": [v["topico"] for v in variacoes if v["movimento"] == "piorou"],
    }


# --------------------------------------------------------------------------- #
# Entrada principal
# --------------------------------------------------------------------------- #


def detectar(entradas: dict[str, Any], hoje: date | None = None) -> dict[str, Any]:
    """Constrói o Mapa Dinâmico de Dificuldades."""
    hoje = hoje or date.today()
    dados = entradas.get("dados_usuario", {}) or {}
    campos = {k: v for k, v in dados.items() if k != "perfil"}
    if isinstance(dados.get("perfil"), dict):
        campos = {**campos, **dados["perfil"]}

    anteriores = entradas.get("saidas_anteriores", {})
    perfil = anteriores.get("01", {}) or {}
    mapa_estrategico = anteriores.get("02", {}) or {}
    mapa_conhecimento = anteriores.get("03", {}) or {}
    arvore = anteriores.get("04", {}) or {}
    grafo = anteriores.get("05", {}) or {}
    plano = anteriores.get("06", {}) or {}
    exercicios = anteriores.get("09", {}) or {}
    revisoes = anteriores.get("14", {}) or {}
    relatorio_de_erros = anteriores.get("17", {}) or {}

    erros = _erros_registrados(campos, relatorio_de_erros, exercicios)
    tempos = _tempos(campos, revisoes)
    estimados = _estimado_da_arvore(arvore)

    erros_por_topico: dict[str, list[dict]] = {}
    for erro in erros:
        if preenchido(erro.get("topico")):
            erros_por_topico.setdefault(como_texto(erro["topico"]), []).append(erro)

    topicos: list[dict] = []
    disciplinas: list[dict] = []

    for disciplina in mapa_conhecimento.get("disciplinas", []):
        nome_disciplina = disciplina["disciplina"]
        do_disciplina: list[dict] = []

        for medicao in disciplina.get("topicos", []):
            chave = como_texto(medicao["topico"])
            erros_do_topico = erros_por_topico.get(chave, [])
            dificuldade = _indice_do_topico(
                medicao, erros_do_topico, tempos.get(chave), estimados.get(chave)
            )
            registro = {
                "topico": medicao["topico"],
                "disciplina": nome_disciplina,
                "taxa_de_acertos": medicao.get("taxa_acerto"),
                "amostra": medicao.get("amostra"),
                "tempo_medio_de_resolucao_min": (
                    round(tempos[chave]["gasto_min"] / tempos[chave]["sessoes"], 1)
                    if chave in tempos and tempos[chave]["sessoes"]
                    else None
                ),
                "frequencia_de_erros": len(erros_do_topico),
                "esquecido": bool(medicao.get("esquecido")),
                "dificuldade": dificuldade,
                "tipos_de_dificuldade": _tipos_de_dificuldade(erros_do_topico),
            }
            topicos.append(registro)
            do_disciplina.append(registro)

        indices = [
            t["dificuldade"]["indice"]
            for t in do_disciplina
            if t["dificuldade"]["indice"] is not None
        ]
        indice_disciplina = _media(indices)
        disciplinas.append(
            {
                "disciplina": nome_disciplina,
                "indice_de_dificuldade": indice_disciplina,
                "nivel": _classificar(indice_disciplina),
                "topicos_medidos": len(indices),
                "topicos_totais": len(do_disciplina),
                "conteudos_criticos": [
                    t["topico"]
                    for t in do_disciplina
                    if t["dificuldade"]["nivel"] in ("dificil", "critico")
                ],
                "conteudos_dominados": [
                    t["topico"]
                    for t in do_disciplina
                    if t["dificuldade"]["nivel"] in ("muito_facil", "facil")
                ],
                "conteudos_sem_evidencia": [
                    t["topico"]
                    for t in do_disciplina
                    if t["dificuldade"]["nivel"] == "indeterminado"
                ],
                "topicos": do_disciplina,
            }
        )

    prioridades = {
        como_texto(p["disciplina"]): p["prioridade"]
        for p in mapa_estrategico.get("prioridade_disciplinas", [])
    }
    reforco = _priorizar_reforco(topicos, prioridades, grafo)
    evolucao = _evolucao(topicos, campos.get("relatorio_anterior"))
    indices_gerais = [
        t["dificuldade"]["indice"] for t in topicos if t["dificuldade"]["indice"] is not None
    ]
    indice_geral = _media(indices_gerais)

    esquecidos = [t["topico"] for t in topicos if t["esquecido"]]
    gargalos = _gargalos(topicos, grafo)
    sobrecarga = _sobrecarga(perfil, plano, tempos, estimados, topicos)

    return {
        "recalculado_em": hoje.isoformat(),
        "resumo_geral": {
            "indice_geral_de_dificuldade": indice_geral,
            "nivel_geral": _classificar(indice_geral),
            "topicos_medidos": len(indices_gerais),
            "topicos_totais": len(topicos),
            "evolucao": evolucao,
            "tendencia_de_aprendizagem": evolucao["tendencia"],
            "velocidade_de_aprendizagem": _velocidade(tempos, estimados),
        },
        "disciplinas": disciplinas,
        "topicos": topicos,
        "padroes_de_erro": _padroes_recorrentes(erros),
        "tipos_de_dificuldade": _tipos_de_dificuldade(erros),
        "sinais_de_sobrecarga": sobrecarga,
        "principais_gargalos": gargalos,
        "conceitos_que_bloqueiam_o_progresso": [
            g for g in gargalos if g["conteudos_bloqueados"] > 0
        ],
        "conteudos_esquecidos": esquecidos,
        "risco_de_abandono": _risco_de_abandono(
            indice_geral, evolucao, sobrecarga, plano
        ),
        "recomendacoes_de_reforco": reforco,
        "consumido_por": [
            "13", "14", "15", "17", "18", "19", "21", "22", "23", "24"
        ],
        "observacoes": _observacoes(topicos, erros, tempos, mapa_conhecimento),
        "lacunas": _lacunas(mapa_conhecimento, erros, tempos),
        "confiabilidade": (
            "alta" if len(indices_gerais) == len(topicos) and topicos and erros
            else "media" if indices_gerais
            else "baixa"
        ),
        "constantes_aplicadas": {
            "pesos_do_indice": PESOS_DO_INDICE,
            "faixas": {nome: limite for limite, nome in FAIXAS},
            "limiar_sobrecarga_tempo": LIMIAR_SOBRECARGA_TEMPO,
            "limiar_decaimento_relevante": LIMIAR_DECAIMENTO_RELEVANTE,
            "limiar_padrao_recorrente": LIMIAR_PADRAO_RECORRENTE,
            "tipo_por_categoria": TIPO_POR_CATEGORIA,
        },
    }


def _priorizar_reforco(
    topicos: list[dict], prioridades: dict[str, str], grafo: dict
) -> list[dict]:
    peso_prioridade = {"alta": 1.0, "media": 0.7, "baixa": 0.4}
    dependentes = {
        no["nome"]: no.get("dependentes_transitivos", 0) for no in grafo.get("nos", [])
    }

    reforco = []
    for topico in topicos:
        indice = topico["dificuldade"]["indice"]
        if indice is None:
            continue
        peso = peso_prioridade.get(
            prioridades.get(como_texto(topico["disciplina"]), "media"), 0.7
        )
        bloqueia = dependentes.get(topico["topico"], 0)
        score = indice * peso * (1 + 0.2 * bloqueia)
        reforco.append(
            {
                "topico": topico["topico"],
                "disciplina": topico["disciplina"],
                "score": round(score, 3),
                "indice_de_dificuldade": indice,
                "nivel": topico["dificuldade"]["nivel"],
                "bloqueia_conteudos": bloqueia,
                "tipo_predominante": topico["tipos_de_dificuldade"]["predominante"],
                "acao_sugerida": (
                    "reforço imediato" if topico["dificuldade"]["nivel"] == "critico"
                    else "reforço programado" if topico["dificuldade"]["nivel"] == "dificil"
                    else "manutenção por revisão"
                ),
            }
        )
    reforco.sort(key=lambda r: -r["score"])
    return reforco


def _risco_de_abandono(
    indice_geral: float | None, evolucao: dict, sobrecarga: list[dict], plano: dict
) -> dict:
    fatores: list[str] = []
    if indice_geral is not None and indice_geral >= 0.7:
        fatores.append(f"índice geral de dificuldade em {indice_geral:.0%}")
    if evolucao["tendencia"] == "piorando":
        fatores.append("tendência de piora entre as medições")
    if any(s["severidade"] == "alta" for s in sobrecarga):
        fatores.append("sinal de sobrecarga em severidade alta")
    faltas = [r for r in plano.get("riscos", []) if r.get("risco") == "faltas_registradas"]
    if faltas:
        fatores.append(faltas[0]["evidencia"])

    if not fatores:
        return {"nivel": "baixo", "fatores": [], "base": "nenhum fator de risco medido"}
    nivel = "alto" if len(fatores) >= 3 else "medio" if len(fatores) == 2 else "baixo"
    return {
        "nivel": nivel,
        "fatores": fatores,
        "base": f"{len(fatores)} fator(es) de risco com evidência",
    }


def _observacoes(
    topicos: list[dict], erros: list[dict], tempos: dict, mapa_conhecimento: dict
) -> list[str]:
    observacoes: list[str] = []
    if not mapa_conhecimento:
        observacoes.append(
            "Nenhum Mapa de Conhecimento recebido do agente 03: não há o que medir."
        )
    sem_evidencia = [t["topico"] for t in topicos if t["dificuldade"]["indice"] is None]
    if sem_evidencia:
        observacoes.append(
            f"{len(sem_evidencia)} tópico(s) sem índice: sem evidência medida, a "
            "dificuldade não é presumida."
        )
    if not erros:
        observacoes.append(
            "Nenhum erro registrado: os tipos de dificuldade (conceitual, "
            "procedimental, interpretação, memorização) não puderam ser separados."
        )
    if not tempos:
        observacoes.append(
            "Nenhum tempo de estudo registrado: velocidade de aprendizagem e "
            "sinais de sobrecarga por tempo ficam indisponíveis."
        )
    observacoes.append(
        "Este relatório não altera o Plano de Estudos nem o Grafo de "
        "Dependências — a decisão é dos agentes 15 e 23."
    )
    return observacoes


def _lacunas(mapa_conhecimento: dict, erros: list[dict], tempos: dict) -> list[str]:
    lacunas: list[str] = []
    if not mapa_conhecimento:
        lacunas.append("mapa_de_conhecimento_do_agente_03")
    if not erros:
        lacunas.append("registro_de_erros")
    if not tempos:
        lacunas.append("historico_sessoes")
    return lacunas


__all__ = [
    "FAIXAS",
    "LIMIAR_DECAIMENTO_RELEVANTE",
    "PESOS_DO_INDICE",
    "TIPO_POR_CATEGORIA",
    "detectar",
]
