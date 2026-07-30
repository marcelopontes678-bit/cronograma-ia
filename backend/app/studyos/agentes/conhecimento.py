"""Agente 03 — Knowledge Analyzer.

Única responsabilidade: medir o conhecimento atual antes do plano existir. Não
ensina, não cria cronograma, não gera resumos, aulas, questões ou flashcards.

A regra que estrutura o módulo inteiro: **domínio só existe com evidência
prática**. Percepção do estudante ("gosto de Português") e histórico de estudo
("já vi essa matéria") não classificam tópico — no máximo registram contato.
Sem evidência suficiente, o tópico fica `indeterminado` e o agente **pede uma
avaliação diagnóstica** em vez de estimar.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from app.studyos.agentes.comum import (
    como_data,
    como_lista,
    como_numero,
    como_texto,
    preenchido,
)

# --------------------------------------------------------------------------- #
# Constantes declaradas
# --------------------------------------------------------------------------- #

#: Faixas de acerto ponderado que definem a classificação do tópico.
FAIXA_AVANCADO = 0.85
FAIXA_INTERMEDIARIO = 0.60
FAIXA_BASICO = 0.35

#: Amostra mínima para uma classificação valer. Abaixo disso, `indeterminado`.
MINIMO_QUESTOES_POR_TOPICO = 5

#: Peso de cada tipo de evidência. Percepção e histórico não entram: eles não
#: são prova de domínio.
PESO_EVIDENCIA: dict[str, float] = {
    "simulado": 1.0,
    "diagnostico": 1.0,
    "exercicio": 0.8,
}

#: Meia-vida da retenção sem contato (curva de esquecimento).
RETENCAO_MEIA_VIDA_DIAS = 30
#: Abaixo desta retenção estimada, o tópico é marcado como esquecido.
LIMIAR_ESQUECIMENTO = 0.5

#: Horas-base para dominar um tópico, moduladas pela classificação atual.
HORAS_BASE_POR_TOPICO = 2.5
FATOR_ESFORCO: dict[str, float] = {
    "nao_conhece": 1.0,
    "basico": 0.7,
    "intermediario": 0.4,
    "avancado": 0.15,
    "indeterminado": 1.0,  # conservador: só cai quando houver medição
}

#: Cobertura diagnóstica mínima para o percentual da disciplina ser confiável.
COBERTURA_MINIMA_CONFIAVEL = 0.5
#: Cobertura necessária para o IGC valer como medida, e não como indicação.
COBERTURA_ALTA_CONFIANCA = 0.8

#: Questões sugeridas por tópico ao *solicitar* diagnóstico (o agente 09 gera).
QUESTOES_SUGERIDAS_POR_TOPICO = 5

#: Peso da disciplina no IGC, conforme prioridade vinda do agente 02.
PESO_PRIORIDADE = {"alta": 3.0, "media": 2.0, "baixa": 1.0}

VALOR_CLASSIFICACAO = {
    "avancado": 1.0,
    "intermediario": 0.6,
    "basico": 0.3,
    "nao_conhece": 0.0,
}

CAMPOS_EVIDENCIA: tuple[tuple[str, str], ...] = (
    ("resultados_simulados", "simulado"),
    ("resultados_exercicios", "exercicio"),
    ("questionario_diagnostico", "diagnostico"),
    ("historico", "exercicio"),
)


# --------------------------------------------------------------------------- #
# Coleta de evidências
# --------------------------------------------------------------------------- #


def _normalizar_evidencia(item: Any, tipo: str) -> dict | None:
    """Aceita `{acertos, total}` ou `{percentual, amostra}`, com ou sem tópico."""
    if not isinstance(item, dict):
        return None

    acertos = como_numero(item.get("acertos"))
    total = como_numero(item.get("total")) or como_numero(item.get("questoes"))
    percentual = como_numero(item.get("percentual")) or como_numero(item.get("acerto"))
    amostra = como_numero(item.get("amostra"))

    if acertos is not None and total:
        taxa, tamanho = acertos / total, total
    elif percentual is not None:
        taxa = percentual / 100 if percentual > 1 else percentual
        tamanho = amostra or 0
    else:
        return None

    return {
        "tipo": item.get("tipo") or tipo,
        "disciplina": item.get("disciplina") or item.get("materia"),
        "topico": item.get("topico") or item.get("assunto"),
        "taxa_acerto": round(min(max(taxa, 0.0), 1.0), 4),
        "amostra": int(tamanho),
        "data": como_data(item.get("data") or item.get("quando")),
        "peso": PESO_EVIDENCIA.get(item.get("tipo") or tipo, 0.8),
    }


def _coletar_evidencias(campos: dict[str, Any]) -> list[dict]:
    evidencias: list[dict] = []
    for campo, tipo in CAMPOS_EVIDENCIA:
        bruto = campos.get(campo)
        if not preenchido(bruto):
            continue
        itens = bruto if isinstance(bruto, (list, tuple)) else [bruto]
        for item in itens:
            normalizada = _normalizar_evidencia(item, tipo)
            if normalizada:
                evidencias.append(normalizada)
    return evidencias


def _classificar(taxa: float | None, amostra: int) -> tuple[str, str, str]:
    """Devolve (classificação, confiança, base)."""
    if taxa is None or amostra == 0:
        return (
            "indeterminado",
            "nenhuma",
            "sem evidência prática — classificação não estimada",
        )
    if amostra < MINIMO_QUESTOES_POR_TOPICO:
        return (
            "indeterminado",
            "baixa",
            f"amostra insuficiente ({amostra} < {MINIMO_QUESTOES_POR_TOPICO} questões)",
        )

    if taxa >= FAIXA_AVANCADO:
        classificacao = "avancado"
    elif taxa >= FAIXA_INTERMEDIARIO:
        classificacao = "intermediario"
    elif taxa >= FAIXA_BASICO:
        classificacao = "basico"
    else:
        classificacao = "nao_conhece"

    confianca = "alta" if amostra >= 2 * MINIMO_QUESTOES_POR_TOPICO else "media"
    return (
        classificacao,
        confianca,
        f"{amostra} questões com {taxa:.0%} de acerto ponderado",
    )


def _rebaixar(classificacao: str) -> str:
    ordem = ["nao_conhece", "basico", "intermediario", "avancado"]
    if classificacao not in ordem:
        return classificacao
    return ordem[max(0, ordem.index(classificacao) - 1)]


def _esquecimento(
    ultimo_contato: date | None, hoje: date
) -> tuple[int | None, float | None, bool]:
    if ultimo_contato is None:
        return None, None, False
    dias = (hoje - ultimo_contato).days
    if dias < 0:
        return dias, None, False
    retencao = 0.5 ** (dias / RETENCAO_MEIA_VIDA_DIAS)
    return dias, round(retencao, 3), retencao < LIMIAR_ESQUECIMENTO


# --------------------------------------------------------------------------- #
# Montagem por tópico e por disciplina
# --------------------------------------------------------------------------- #


def _agregar(evidencias: list[dict]) -> tuple[float | None, int]:
    """Taxa de acerto ponderada pelo tipo de evidência e o tamanho da amostra."""
    if not evidencias:
        return None, 0
    peso_total = sum(e["peso"] * max(e["amostra"], 1) for e in evidencias)
    if not peso_total:
        return None, 0
    taxa = (
        sum(e["taxa_acerto"] * e["peso"] * max(e["amostra"], 1) for e in evidencias)
        / peso_total
    )
    return round(taxa, 4), sum(e["amostra"] for e in evidencias)


def _analisar_topico(
    nome: str,
    subtopicos: list[str],
    evidencias: list[dict],
    ultimo_contato: date | None,
    hoje: date,
) -> dict:
    taxa, amostra = _agregar(evidencias)
    classificacao, confianca, base = _classificar(taxa, amostra)

    contato = ultimo_contato or max(
        (e["data"] for e in evidencias if e["data"]), default=None
    )
    dias, retencao, esquecido = _esquecimento(contato, hoje)

    if esquecido and classificacao not in ("indeterminado", "nao_conhece"):
        anterior = classificacao
        classificacao = _rebaixar(classificacao)
        base += (
            f"; rebaixado de '{anterior}' por {dias} dias sem contato "
            f"(retenção estimada {retencao:.0%})"
        )

    return {
        "topico": nome,
        "subtopicos": subtopicos,
        "classificacao": classificacao,
        "confianca": confianca,
        "base": base,
        "taxa_acerto": taxa,
        "amostra": amostra,
        "evidencias": [
            {k: (v.isoformat() if isinstance(v, date) else v) for k, v in e.items()}
            for e in evidencias
        ],
        "dias_sem_contato": dias,
        "retencao_estimada": retencao,
        "esquecido": esquecido,
        "esforco_estimado_h": round(
            HORAS_BASE_POR_TOPICO * FATOR_ESFORCO[classificacao], 2
        ),
    }


def _pre_requisitos_ausentes(
    topicos: list[dict], mapa: dict[str, list[str]]
) -> list[dict]:
    """Pré-requisito ausente = base fraca sob um tópico que se pretende dominar."""
    if not mapa:
        return []

    por_nome = {como_texto(t["topico"]): t for t in topicos}
    ausentes: list[dict] = []
    for topico in topicos:
        for pre in mapa.get(como_texto(topico["topico"]), []):
            base = por_nome.get(como_texto(pre))
            if base is None:
                ausentes.append(
                    {
                        "topico": topico["topico"],
                        "pre_requisito": pre,
                        "situacao": "fora do escopo mapeado",
                    }
                )
            elif base["classificacao"] in ("nao_conhece", "basico"):
                ausentes.append(
                    {
                        "topico": topico["topico"],
                        "pre_requisito": base["topico"],
                        "situacao": f"pré-requisito em nível '{base['classificacao']}'",
                    }
                )
            elif base["classificacao"] == "indeterminado":
                ausentes.append(
                    {
                        "topico": topico["topico"],
                        "pre_requisito": base["topico"],
                        "situacao": "pré-requisito sem evidência medida",
                    }
                )
    return ausentes


def _grau_dificuldade(percentual: float | None, dificuldade_declarada: bool) -> dict:
    if percentual is None:
        return {
            "grau": "indeterminado",
            "base": "sem percentual de domínio medido",
            "percepcao_de_dificuldade": dificuldade_declarada,
        }

    lacuna = 1 - percentual
    if dificuldade_declarada:
        lacuna += 0.15  # percepção pesa na dificuldade, nunca no domínio
    grau = "dificil" if lacuna >= 0.6 else "moderada" if lacuna >= 0.3 else "facil"
    return {
        "grau": grau,
        "base": f"lacuna de {lacuna:.0%}"
        + (" (inclui dificuldade declarada pelo estudante)" if dificuldade_declarada else ""),
        "percepcao_de_dificuldade": dificuldade_declarada,
    }


def _prioridade_estudo(
    prioridade_02: str | None, percentual: float | None, cobertura: float
) -> dict:
    if percentual is None:
        return {
            "prioridade": "diagnosticar_primeiro",
            "base": "sem medição de domínio; diagnóstico precede o planejamento",
        }

    score = PESO_PRIORIDADE.get(prioridade_02 or "media", 2.0) * (1 - percentual)
    prioridade = "alta" if score >= 1.5 else "media" if score >= 0.7 else "baixa"
    return {
        "prioridade": prioridade,
        "score": round(score, 2),
        "base": (
            f"prioridade '{prioridade_02 or 'media'}' do agente 02 × lacuna de "
            f"{1 - percentual:.0%} (cobertura diagnóstica {cobertura:.0%})"
        ),
    }


def _analisar_disciplina(
    disciplina: dict,
    prioridade_02: str | None,
    evidencias: list[dict],
    subtopicos: dict[str, list[str]],
    pre_requisitos: dict[str, list[str]],
    ultimo_contato: dict[str, date],
    dificuldade_declarada: bool,
    hoje: date,
) -> dict:
    nome = disciplina["nome"]
    chave = como_texto(nome)

    da_disciplina = [e for e in evidencias if como_texto(e["disciplina"]) == chave]
    sem_topico = [e for e in da_disciplina if not preenchido(e["topico"])]

    topicos: list[dict] = []
    for topico in disciplina["topicos"]:
        chave_topico = como_texto(topico)
        do_topico = [
            e for e in da_disciplina if como_texto(e["topico"]) == chave_topico
        ]
        topicos.append(
            _analisar_topico(
                topico,
                como_lista(subtopicos.get(topico) or subtopicos.get(chave_topico)),
                do_topico,
                ultimo_contato.get(chave_topico) or ultimo_contato.get(chave),
                hoje,
            )
        )

    conhecidos = [t for t in topicos if t["classificacao"] != "indeterminado"]
    cobertura = len(conhecidos) / len(topicos) if topicos else 0.0

    if conhecidos:
        percentual = round(
            sum(VALOR_CLASSIFICACAO[t["classificacao"]] for t in conhecidos)
            / len(conhecidos),
            4,
        )
        base_percentual = (
            f"{len(conhecidos)} de {len(topicos)} tópicos com evidência prática"
        )
    elif sem_topico:
        taxa, amostra = _agregar(sem_topico)
        classificacao, _, _ = _classificar(taxa, amostra)
        percentual = taxa if classificacao != "indeterminado" else None
        base_percentual = (
            f"evidência agregada da disciplina ({amostra} questões)"
            if percentual is not None
            else "evidência da disciplina insuficiente"
        )
    else:
        percentual, base_percentual = None, "sem nenhuma evidência prática"

    if percentual is not None and cobertura < COBERTURA_MINIMA_CONFIAVEL:
        base_percentual += (
            f"; cobertura diagnóstica de {cobertura:.0%} abaixo do mínimo confiável "
            f"({COBERTURA_MINIMA_CONFIAVEL:.0%})"
        )

    return {
        "disciplina": nome,
        "percentual_dominio": percentual,
        "base_do_percentual": base_percentual,
        "cobertura_diagnostica": round(cobertura, 2),
        "confiavel": percentual is not None and cobertura >= COBERTURA_MINIMA_CONFIAVEL,
        "topicos_dominados": [t["topico"] for t in topicos if t["classificacao"] == "avancado"],
        "topicos_parcialmente_dominados": [
            t["topico"] for t in topicos if t["classificacao"] in ("basico", "intermediario")
        ],
        "topicos_desconhecidos": [
            t["topico"] for t in topicos if t["classificacao"] == "nao_conhece"
        ],
        "topicos_sem_evidencia": [
            t["topico"] for t in topicos if t["classificacao"] == "indeterminado"
        ],
        "topicos_esquecidos": [t["topico"] for t in topicos if t["esquecido"]],
        "pre_requisitos_ausentes": _pre_requisitos_ausentes(topicos, pre_requisitos),
        "grau_dificuldade": _grau_dificuldade(percentual, dificuldade_declarada),
        "prioridade_estudo": _prioridade_estudo(prioridade_02, percentual, cobertura),
        "esforco_estimado_h": round(sum(t["esforco_estimado_h"] for t in topicos), 2),
        "prioridade_do_agente_02": prioridade_02,
        "topicos": topicos,
    }


# --------------------------------------------------------------------------- #
# Diagnóstico, IGC e resumo
# --------------------------------------------------------------------------- #


def _solicitar_diagnostico(disciplinas: list[dict]) -> dict:
    escopo = [
        {
            "disciplina": d["disciplina"],
            "topicos": d["topicos_sem_evidencia"],
            "questoes_sugeridas": len(d["topicos_sem_evidencia"])
            * QUESTOES_SUGERIDAS_POR_TOPICO,
        }
        for d in disciplinas
        if d["topicos_sem_evidencia"]
    ]
    if not escopo:
        return {
            "necessaria": False,
            "motivo": "todos os tópicos mapeados têm evidência prática",
            "escopo": [],
        }

    return {
        "necessaria": True,
        "motivo": (
            "há tópicos sem evidência prática; o nível não pode ser estimado sem "
            "avaliação diagnóstica"
        ),
        "escopo": escopo,
        "total_questoes_sugeridas": sum(e["questoes_sugeridas"] for e in escopo),
        "executor": "09 Exercise Generator (o agente 03 não gera questões)",
    }


def _igc(disciplinas: list[dict]) -> dict:
    medidas = [d for d in disciplinas if d["percentual_dominio"] is not None]
    if not medidas:
        return {
            "valor": None,
            "base": "nenhuma disciplina com evidência prática",
            "confianca": "nenhuma",
            "disciplinas_medidas": 0,
            "disciplinas_totais": len(disciplinas),
        }

    peso_total = sum(
        PESO_PRIORIDADE.get(d["prioridade_do_agente_02"] or "media", 2.0) for d in medidas
    )
    valor = (
        sum(
            d["percentual_dominio"]
            * PESO_PRIORIDADE.get(d["prioridade_do_agente_02"] or "media", 2.0)
            for d in medidas
        )
        / peso_total
    )

    cobertura_media = sum(d["cobertura_diagnostica"] for d in medidas) / len(medidas)
    proporcao_medida = len(medidas) / len(disciplinas)
    # Um IGC só é "alto" quando quase todo o escopo foi medido: metade dos
    # tópicos sem evidência não sustenta uma medida de conhecimento.
    if cobertura_media >= COBERTURA_ALTA_CONFIANCA and proporcao_medida == 1:
        confianca = "alta"
    elif cobertura_media >= COBERTURA_MINIMA_CONFIAVEL:
        confianca = "media"
    else:
        confianca = "baixa"

    return {
        "valor": round(valor, 4),
        "percentual": f"{valor:.0%}",
        "base": (
            f"média das {len(medidas)} disciplina(s) medida(s), ponderada pela "
            "prioridade do agente 02"
        ),
        "confianca": confianca,
        "cobertura_diagnostica_media": round(cobertura_media, 2),
        "disciplinas_medidas": len(medidas),
        "disciplinas_totais": len(disciplinas),
    }


def _resumo(disciplinas: list[dict], diagnostico: dict, igc: dict) -> dict:
    fortes = [
        f"{d['disciplina']}: {d['percentual_dominio']:.0%} de domínio medido"
        for d in disciplinas
        if d["percentual_dominio"] is not None and d["percentual_dominio"] >= FAIXA_AVANCADO
    ]
    fracos = [
        f"{d['disciplina']}: {d['percentual_dominio']:.0%} de domínio medido"
        for d in disciplinas
        if d["percentual_dominio"] is not None and d["percentual_dominio"] < FAIXA_BASICO
    ]

    riscos: list[dict] = []
    if diagnostico["necessaria"]:
        riscos.append(
            {
                "risco": "conhecimento_nao_medido",
                "severidade": "alta",
                "evidencia": (
                    f"{sum(len(e['topicos']) for e in diagnostico['escopo'])} tópico(s) "
                    "sem evidência prática"
                ),
            }
        )
    for disciplina in disciplinas:
        if disciplina["pre_requisitos_ausentes"]:
            riscos.append(
                {
                    "risco": "pre_requisito_ausente",
                    "severidade": "alta",
                    "evidencia": (
                        f"{disciplina['disciplina']}: "
                        f"{len(disciplina['pre_requisitos_ausentes'])} pendência(s)"
                    ),
                }
            )
        if disciplina["topicos_esquecidos"]:
            riscos.append(
                {
                    "risco": "esquecimento",
                    "severidade": "media",
                    "evidencia": (
                        f"{disciplina['disciplina']}: "
                        + ", ".join(disciplina["topicos_esquecidos"])
                    ),
                }
            )
        if (
            disciplina["prioridade_do_agente_02"] == "alta"
            and disciplina["percentual_dominio"] is not None
            and disciplina["percentual_dominio"] < FAIXA_INTERMEDIARIO
        ):
            riscos.append(
                {
                    "risco": "lacuna_em_disciplina_prioritaria",
                    "severidade": "alta",
                    "evidencia": (
                        f"{disciplina['disciplina']} tem prioridade alta e "
                        f"{disciplina['percentual_dominio']:.0%} de domínio"
                    ),
                }
            )

    recomendacoes: list[str] = []
    if diagnostico["necessaria"]:
        recomendacoes.append(
            "Aplicar avaliação diagnóstica antes de fechar o cronograma: "
            + ", ".join(e["disciplina"] for e in diagnostico["escopo"])
        )
    ordenadas = sorted(
        (d for d in disciplinas if d["prioridade_estudo"].get("score") is not None),
        key=lambda d: -d["prioridade_estudo"]["score"],
    )
    if ordenadas:
        recomendacoes.append(
            "Ordem sugerida por lacuna × prioridade: "
            + ", ".join(d["disciplina"] for d in ordenadas)
        )
    esquecidos = [d["disciplina"] for d in disciplinas if d["topicos_esquecidos"]]
    if esquecidos:
        recomendacoes.append(
            "Agendar revisão de recuperação (agentes 14/15) em: " + ", ".join(esquecidos)
        )
    if igc["valor"] is not None and igc["confianca"] != "alta":
        recomendacoes.append(
            "Tratar o IGC como provisório: cobertura diagnóstica ainda insuficiente"
        )

    return {
        "pontos_fortes": fortes,
        "pontos_fracos": fracos,
        "riscos_de_aprendizagem": riscos,
        "recomendacoes_para_planejamento": recomendacoes,
    }


# --------------------------------------------------------------------------- #
# Entrada principal
# --------------------------------------------------------------------------- #


def _mapa_de_datas(bruto: Any) -> dict[str, date]:
    if not isinstance(bruto, dict):
        return {}
    mapa: dict[str, date] = {}
    for chave, valor in bruto.items():
        data = como_data(valor)
        if data:
            mapa[como_texto(chave)] = data
    return mapa


def _mapa_de_listas(bruto: Any) -> dict[str, list[str]]:
    if not isinstance(bruto, dict):
        return {}
    return {como_texto(chave): como_lista(valor) for chave, valor in bruto.items()}


def analisar(entradas: dict[str, Any], hoje: date | None = None) -> dict[str, Any]:
    """Constrói o Mapa de Conhecimento Estruturado."""
    hoje = hoje or date.today()
    dados = entradas.get("dados_usuario", {}) or {}
    campos = {k: v for k, v in dados.items() if k != "perfil"}
    if isinstance(dados.get("perfil"), dict):
        campos = {**campos, **dados["perfil"]}

    anteriores = entradas.get("saidas_anteriores", {})
    perfil = anteriores.get("01", {}) or {}
    mapa_estrategico = anteriores.get("02", {}) or {}

    disciplinas_alvo = mapa_estrategico.get("disciplinas", [])
    prioridades_02 = {
        como_texto(p["disciplina"]): p["prioridade"]
        for p in mapa_estrategico.get("prioridade_disciplinas", [])
    }

    evidencias = _coletar_evidencias(campos)
    subtopicos = {
        chave: valor for chave, valor in _mapa_de_listas(campos.get("subtopicos")).items()
    }
    pre_requisitos = _mapa_de_listas(campos.get("pre_requisitos"))
    ultimo_contato = _mapa_de_datas(campos.get("ultimo_contato"))
    dificuldades = {como_texto(d) for d in como_lista(campos.get("disciplinas_dificuldade"))}

    analisadas = [
        _analisar_disciplina(
            disciplina,
            prioridades_02.get(como_texto(disciplina["nome"])),
            evidencias,
            subtopicos,
            pre_requisitos,
            ultimo_contato,
            como_texto(disciplina["nome"]) in dificuldades,
            hoje,
        )
        for disciplina in disciplinas_alvo
    ]

    diagnostico = _solicitar_diagnostico(analisadas)
    igc = _igc(analisadas)

    nomes_conhecidos = {como_texto(d["nome"]) for d in disciplinas_alvo}
    nao_mapeadas = [
        {
            "disciplina": e["disciplina"],
            "topico": e["topico"],
            "motivo": "não consta nas disciplinas do objetivo (agente 02)",
        }
        for e in evidencias
        if como_texto(e["disciplina"]) not in nomes_conhecidos
    ]

    observacoes: list[str] = []
    if not disciplinas_alvo:
        observacoes.append(
            "Nenhuma disciplina recebida do agente 02: não há escopo para medir. "
            "Informe o edital ou as matérias antes do diagnóstico."
        )
    if not evidencias:
        observacoes.append(
            "Nenhum resultado prático informado. Percepção do estudante e histórico "
            "de estudo não classificam domínio — é necessária avaliação diagnóstica."
        )
    if not subtopicos and disciplinas_alvo:
        observacoes.append(
            "Sem detalhamento de subtópicos: o tópico é a menor granularidade "
            "medida. Subtópicos não foram inferidos."
        )
    if not pre_requisitos and disciplinas_alvo:
        observacoes.append(
            "Sem mapa de pré-requisitos informado: a detecção depende do agente 05 "
            "Dependency Mapper."
        )
    if nao_mapeadas:
        observacoes.append(
            f"{len(nao_mapeadas)} evidência(s) fora do escopo do objetivo foram "
            "registradas, mas não entraram no cálculo."
        )

    lacunas: list[str] = []
    if not mapa_estrategico:
        lacunas.append("mapa_estrategico_do_agente_02")
    if not perfil:
        lacunas.append("perfil_cognitivo_do_agente_01")
    if not evidencias:
        lacunas.append("resultados_praticos")
    if not pre_requisitos:
        lacunas.append("pre_requisitos")
    if not ultimo_contato:
        lacunas.append("ultimo_contato")

    return {
        "indice_geral_de_conhecimento": igc,
        "disciplinas": analisadas,
        "avaliacao_diagnostica": diagnostico,
        "resumo": _resumo(analisadas, diagnostico, igc),
        "evidencias_consideradas": {
            "total": len(evidencias),
            "por_tipo": {
                tipo: sum(1 for e in evidencias if e["tipo"] == tipo)
                for tipo in sorted({e["tipo"] for e in evidencias})
            },
            "fora_do_escopo": nao_mapeadas,
        },
        "esforco_total_estimado_h": round(
            sum(d["esforco_estimado_h"] for d in analisadas), 2
        ),
        "consumido_por": ["04", "05", "06", "12", "14", "15", "17", "18", "21", "22", "23"],
        "observacoes": observacoes,
        "lacunas": lacunas,
        "confiabilidade": igc["confianca"],
        "constantes_aplicadas": {
            "faixas": {
                "avancado": FAIXA_AVANCADO,
                "intermediario": FAIXA_INTERMEDIARIO,
                "basico": FAIXA_BASICO,
            },
            "minimo_questoes_por_topico": MINIMO_QUESTOES_POR_TOPICO,
            "cobertura_alta_confianca": COBERTURA_ALTA_CONFIANCA,
            "peso_evidencia": PESO_EVIDENCIA,
            "retencao_meia_vida_dias": RETENCAO_MEIA_VIDA_DIAS,
            "limiar_esquecimento": LIMIAR_ESQUECIMENTO,
            "horas_base_por_topico": HORAS_BASE_POR_TOPICO,
            "cobertura_minima_confiavel": COBERTURA_MINIMA_CONFIAVEL,
        },
    }


__all__ = ["analisar"]
