"""Agente 21 — Performance Analyzer.

Única responsabilidade: transformar o que os outros agentes produziram em
indicadores objetivos. Não ensina, não cria cronograma, não gera exercício,
não altera o plano.

Este agente é o primeiro que **quase não mede nada sozinho** — e essa é a
decisão que o define. Domínio já foi medido pelo 03, dificuldade pelo 12,
erro pelo 17, fragilidade pelo 18, consistência pelo 19 e hábito pelo 20.
Recalcular qualquer um desses números aqui produziria uma segunda versão dele,
e um painel que discorda dos próprios relatórios não é painel, é ruído.

Então o que este agente faz é:

* **Consolidar com procedência.** Todo indicador carrega `origem` — o agente
  que o produziu — e `base`, a frase que explica de onde o número saiu. Quem
  ler o painel consegue voltar até a medição.
* **Calcular só o que ninguém calculou:** o Índice Geral de Performance, o
  progresso curricular, o desvio entre planejado e realizado e a evolução
  entre janelas.
* **Nunca preencher lacuna com zero.** Componente sem dado fica de fora do IGP
  e o peso é redistribuído entre os presentes; indicador sem fonte sai `None`
  com o motivo. Zero é uma afirmação sobre o estudante — ausência de dado não é.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from app.studyos.agentes.comum import como_data, como_lista_de_dicts, como_numero, como_texto
from app.studyos.agentes.frequencia import (
    consistencia as consistencia_de,
    dias_estudados,
    dias_planejados,
    sessoes_registradas,
)

# --------------------------------------------------------------------------- #
# Constantes declaradas
# --------------------------------------------------------------------------- #

#: Peso de cada componente do Índice Geral de Performance. Componente sem dado
#: não entra e o peso é redistribuído entre os presentes.
PESOS_DO_IGP: dict[str, float] = {
    "dominio": 0.30,
    "acerto": 0.25,
    "progresso": 0.20,
    "consistencia": 0.15,
    "retencao": 0.10,
}

#: Classificação do agente 03 → valor de domínio no IGP. É a mesma escala do
#: agente 18 invertida: lá mede fragilidade, aqui mede performance.
VALOR_POR_CLASSIFICACAO: dict[str, float] = {
    "avancado": 1.00,
    "intermediario": 0.65,
    "basico": 0.30,
    "nao_conhece": 0.00,
}

#: Faixas do IGP.
FAIXAS_DO_IGP: tuple[tuple[float, str], ...] = (
    (0.40, "critico"),
    (0.60, "abaixo_do_esperado"),
    (0.80, "adequado"),
)
NIVEL_MAXIMO_DO_IGP = "forte"

#: Janelas de comparação, em dias.
JANELA_SEMANAL = 7
JANELA_MENSAL = 30

#: Variação a partir da qual a evolução deixa de ser estável.
VARIACAO_RELEVANTE = 0.05

#: Questões mínimas para uma taxa de acerto valer como indicador.
MINIMO_DE_QUESTOES = 10

#: Atraso no cronograma, em pontos percentuais de progresso, que vira alerta.
ATRASO_RELEVANTE = 0.15

#: Margem sobre a nota de corte abaixo da qual o desempenho previsto acende
#: alerta. Não é previsão — previsão é do agente 22.
MARGEM_DE_SEGURANCA_NA_NOTA = 0.10

TIPOS_DE_ALERTA = (
    "queda_de_desempenho",
    "atraso_no_cronograma",
    "conteudo_critico",
    "risco_na_nota",
)


def _nivel_do_igp(valor: float) -> str:
    for limite, nome in FAIXAS_DO_IGP:
        if valor < limite:
            return nome
    return NIVEL_MAXIMO_DO_IGP


def _indicador(valor: Any, base: str, origem: str | None = None) -> dict:
    """Todo número do painel sai daqui: valor, de onde veio e por quê."""
    return {"valor": valor, "base": base, "origem": origem}


# --------------------------------------------------------------------------- #
# Histórico de questões
# --------------------------------------------------------------------------- #


def _registros(campos: dict) -> list[dict]:
    """Resultados de questões com data, para as janelas de evolução."""
    registros: list[dict] = []
    for chave in ("resultados_exercicios", "historico_respostas", "historico_desempenho"):
        for bruto in como_lista_de_dicts(campos.get(chave)):
            total = como_numero(bruto.get("total") or bruto.get("questoes"))
            acertos = como_numero(bruto.get("acertos"))
            data = como_data(bruto.get("data"))
            if total and acertos is not None and data:
                registros.append(
                    {
                        "data": data,
                        "topico": bruto.get("topico") or bruto.get("conteudo"),
                        "disciplina": bruto.get("disciplina"),
                        "total": total,
                        "acertos": acertos,
                        "minutos": como_numero(bruto.get("tempo_min") or bruto.get("minutos")),
                    }
                )
    return sorted(registros, key=lambda r: r["data"])


def _taxa(registros: list[dict]) -> dict:
    total = sum(r["total"] for r in registros)
    if not total:
        return _indicador(None, "nenhuma questão registrada")
    acertos = sum(r["acertos"] for r in registros)
    return _indicador(
        round(acertos / total, 4),
        f"{int(acertos)} acertos em {int(total)} questões",
        "histórico do estudante",
    )


def _evolucao(registros: list[dict], hoje: date, janela: int) -> dict:
    """Taxa de acerto da janela contra a janela imediatamente anterior."""
    atual = [r for r in registros if (hoje - r["data"]).days < janela]
    anterior = [r for r in registros if janela <= (hoje - r["data"]).days < janela * 2]

    total_atual = sum(r["total"] for r in atual)
    total_anterior = sum(r["total"] for r in anterior)
    if total_atual < MINIMO_DE_QUESTOES or total_anterior < MINIMO_DE_QUESTOES:
        return {
            "disponivel": False,
            "tendencia": "indeterminada",
            "base": (
                f"são necessárias {MINIMO_DE_QUESTOES} questões em cada janela de "
                f"{janela} dias; há {int(total_atual)} e {int(total_anterior)}"
            ),
        }

    taxa_atual = sum(r["acertos"] for r in atual) / total_atual
    taxa_anterior = sum(r["acertos"] for r in anterior) / total_anterior
    variacao = taxa_atual - taxa_anterior
    return {
        "disponivel": True,
        "tendencia": (
            "melhora" if variacao >= VARIACAO_RELEVANTE
            else "queda" if variacao <= -VARIACAO_RELEVANTE
            else "estavel"
        ),
        "taxa_atual": round(taxa_atual, 4),
        "taxa_anterior": round(taxa_anterior, 4),
        "variacao": round(variacao, 4),
        "base": f"{int(total_atual)} questões contra {int(total_anterior)} na janela anterior",
    }


# --------------------------------------------------------------------------- #
# Desempenho por nível curricular
# --------------------------------------------------------------------------- #


def _desempenho_por_nivel(
    arvore: dict, mapa_conhecimento: dict, relatorio: dict, registros: list[dict]
) -> dict:
    """Disciplina → módulo → tópico → microtópico, com o que foi medido em cada."""
    medicao = {
        como_texto(t["topico"]): t
        for d in mapa_conhecimento.get("disciplinas", [])
        for t in d.get("topicos", [])
    }
    dificuldade = {
        como_texto(t["topico"]): t for t in relatorio.get("topicos", [])
    }
    por_topico: dict[str, dict] = {}
    for registro in registros:
        chave = como_texto(registro.get("topico") or "")
        if not chave:
            continue
        acumulado = por_topico.setdefault(chave, {"total": 0.0, "acertos": 0.0})
        acumulado["total"] += registro["total"]
        acumulado["acertos"] += registro["acertos"]

    def do_topico(nome: str, tipo: str) -> dict:
        chave = como_texto(nome)
        medido = medicao.get(chave, {})
        contagem = por_topico.get(chave)
        return {
            "nome": nome,
            "tipo": tipo,
            "classificacao": medido.get("classificacao", "indeterminado"),
            "taxa_de_acertos": (
                round(contagem["acertos"] / contagem["total"], 4) if contagem else
                medido.get("taxa_acerto")
            ),
            "questoes": int(contagem["total"]) if contagem else medido.get("amostra"),
            "retencao_estimada": medido.get("retencao_estimada"),
            "indice_de_dificuldade": (
                dificuldade.get(chave, {}).get("dificuldade") or {}
            ).get("indice"),
            "status": None,
        }

    disciplinas: list[dict] = []
    for disciplina in arvore.get("disciplinas", []):
        modulos: list[dict] = []
        for modulo in disciplina.get("modulos", []):
            topicos: list[dict] = []
            for topico in modulo.get("topicos", []):
                registro = do_topico(topico["nome"], "topico")
                registro["status"] = topico.get("status")
                registro["microtopicos"] = [
                    do_topico(sub["nome"], "subtopico")
                    for sub in topico.get("subtopicos", [])
                ]
                topicos.append(registro)
            modulos.append(
                {
                    "nome": modulo["nome"],
                    "status": modulo.get("status"),
                    "topicos": topicos,
                    "taxa_de_acertos": _media([t["taxa_de_acertos"] for t in topicos]),
                }
            )
        disciplinas.append(
            {
                "nome": disciplina["nome"],
                "status": disciplina.get("status"),
                "percentual_de_dominio": disciplina.get("percentual_dominio_do_agente_03"),
                "peso_no_edital": disciplina.get("peso"),
                "modulos": modulos,
                "taxa_de_acertos": _media([m["taxa_de_acertos"] for m in modulos]),
            }
        )
    return {
        "disciplinas": disciplinas,
        "base": (
            "estrutura da Árvore Curricular (agente 04) com as medições dos "
            "agentes 03 e 12 e o histórico de questões"
        ),
    }


def _media(valores: list[Any]) -> float | None:
    presentes = [v for v in valores if v is not None]
    return round(sum(presentes) / len(presentes), 4) if presentes else None


# --------------------------------------------------------------------------- #
# Progresso e desvio
# --------------------------------------------------------------------------- #


def _progresso(arvore: dict) -> dict:
    """Tópicos dominados sobre o total da Árvore Curricular.

    O agente 04 devolve os conteúdos como **listas de nomes**, não como
    contagens — o painel conta, mas não recategoriza nada.
    """
    concluidos = len(arvore.get("conteudos_dominados") or [])
    pendentes = len(arvore.get("conteudos_pendentes") or [])
    total = (arvore.get("totais") or {}).get("topicos")
    if not total:
        return {
            "percentual": None,
            "concluidos": concluidos,
            "pendentes": pendentes,
            "base": "árvore curricular sem contagem de tópicos",
        }
    return {
        "percentual": round(concluidos / total, 4),
        "concluidos": concluidos,
        "pendentes": pendentes or total - concluidos,
        "total": total,
        "base": f"{concluidos} de {total} tópicos concluídos na Árvore Curricular",
    }


def _desvio_do_plano(
    plano: dict, sessoes: list[dict], estudados: list[date], hoje: date
) -> dict:
    """Planejado até hoje contra realizado até hoje, em dias e em horas."""
    dias_ate_hoje = [
        d
        for d in dias_planejados(plano, date.min, hoje)
        if d <= hoje
    ]
    if not dias_ate_hoje:
        return {
            "disponivel": False,
            "base": "nenhum dia planejado até hoje; sem referência para comparar",
        }

    cumpridos = [d for d in dias_ate_hoje if d in set(estudados)]
    horas_planejadas = sum(
        float(dia.get("tempo_total_h") or 0)
        for dia in plano.get("cronograma", [])
        if (como_data(dia.get("data")) or hoje) <= hoje
    )
    minutos_estudados = sum(
        s["minutos"] for s in sessoes if s["houve_estudo"] and s["minutos"]
    )
    horas_estudadas = round(minutos_estudados / 60, 2) if minutos_estudados else 0.0

    return {
        "disponivel": True,
        "dias_planejados": len(dias_ate_hoje),
        "dias_cumpridos": len(cumpridos),
        "aderencia_aos_dias": round(len(cumpridos) / len(dias_ate_hoje), 4),
        "horas_planejadas": round(horas_planejadas, 2),
        "horas_estudadas": horas_estudadas,
        "horas_de_diferenca": round(horas_estudadas - horas_planejadas, 2),
        "base": (
            f"{len(cumpridos)} de {len(dias_ate_hoje)} dias planejados até "
            f"{hoje.isoformat()}"
        ),
    }


# --------------------------------------------------------------------------- #
# Índice Geral de Performance
# --------------------------------------------------------------------------- #


def _componentes_do_igp(
    mapa_conhecimento: dict,
    taxa_de_acertos: dict,
    progresso: dict,
    consistencia: Any,
    retencao: dict,
) -> dict[str, dict]:
    componentes: dict[str, dict] = {}

    medicoes = [
        t.get("classificacao")
        for d in mapa_conhecimento.get("disciplinas", [])
        for t in d.get("topicos", [])
    ]
    conhecidas = [VALOR_POR_CLASSIFICACAO[c] for c in medicoes if c in VALOR_POR_CLASSIFICACAO]
    if conhecidas:
        componentes["dominio"] = {
            "valor": round(sum(conhecidas) / len(conhecidas), 4),
            "base": f"{len(conhecidas)} tópicos classificados pelo agente 03",
            "origem": "agente 03",
        }

    if taxa_de_acertos["valor"] is not None:
        componentes["acerto"] = {
            "valor": taxa_de_acertos["valor"],
            "base": taxa_de_acertos["base"],
            "origem": taxa_de_acertos["origem"],
        }

    if progresso["percentual"] is not None:
        componentes["progresso"] = {
            "valor": progresso["percentual"],
            "base": progresso["base"],
            "origem": "agente 04",
        }

    if consistencia is not None:
        componentes["consistencia"] = {
            "valor": consistencia,
            "base": "índice de consistência do acompanhamento",
            "origem": "agente 19",
        }

    if retencao["valor"] is not None:
        componentes["retencao"] = {
            "valor": retencao["valor"],
            "base": retencao["base"],
            "origem": retencao["origem"],
        }

    return componentes


def _igp(componentes: dict[str, dict]) -> dict:
    if not componentes:
        return {
            "valor": None,
            "nivel": "indeterminado",
            "componentes": {},
            "confianca": "baixa",
            "base": "nenhum componente com dado; o IGP não é calculado sem medição",
        }
    peso_total = sum(PESOS_DO_IGP[c] for c in componentes)
    valor = (
        sum(PESOS_DO_IGP[c] * dados["valor"] for c, dados in componentes.items())
        / peso_total
    )
    return {
        "valor": round(valor, 4),
        "nivel": _nivel_do_igp(valor),
        "componentes": componentes,
        "confianca": (
            "alta" if len(componentes) >= 4
            else "media" if len(componentes) >= 2
            else "baixa"
        ),
        "base": (
            f"média ponderada de {len(componentes)} componente(s) medidos; "
            "peso redistribuído entre os presentes"
        ),
    }


# --------------------------------------------------------------------------- #
# Alertas
# --------------------------------------------------------------------------- #


def _alertas(
    evolucao_semanal: dict,
    evolucao_mensal: dict,
    desvio: dict,
    mapa_de_fraquezas: dict,
    simulado: dict,
    campos: dict,
) -> list[dict]:
    """Alerta é consequência de número medido, nunca de impressão."""
    alertas: list[dict] = []

    for nome, evolucao in (("semanal", evolucao_semanal), ("mensal", evolucao_mensal)):
        if evolucao["disponivel"] and evolucao["tendencia"] == "queda":
            alertas.append(
                {
                    "tipo": "queda_de_desempenho",
                    "gravidade": "alta" if nome == "mensal" else "media",
                    "detalhe": (
                        f"taxa de acerto caiu de {evolucao['taxa_anterior']:.0%} para "
                        f"{evolucao['taxa_atual']:.0%} na janela {nome}"
                    ),
                    "base": evolucao["base"],
                }
            )

    if desvio.get("disponivel") and desvio["aderencia_aos_dias"] < 1 - ATRASO_RELEVANTE:
        alertas.append(
            {
                "tipo": "atraso_no_cronograma",
                "gravidade": "alta" if desvio["aderencia_aos_dias"] < 0.5 else "media",
                "detalhe": (
                    f"{desvio['dias_cumpridos']} de {desvio['dias_planejados']} dias "
                    f"planejados cumpridos ({desvio['horas_de_diferenca']:+g}h em relação "
                    "ao previsto)"
                ),
                "base": desvio["base"],
            }
        )

    criticos = [
        f
        for f in mapa_de_fraquezas.get("fraquezas", [])
        if f.get("nivel_de_prioridade") in ("critico", "prioridade_maxima")
    ]
    for fraqueza in criticos[:3]:
        alertas.append(
            {
                "tipo": "conteudo_critico",
                "gravidade": "alta" if fraqueza["nivel_de_prioridade"] == "prioridade_maxima" else "media",
                "detalhe": (
                    f"{fraqueza['topico']} com índice de fraqueza "
                    f"{fraqueza['indice_de_fraqueza']}"
                ),
                "base": "classificação do agente 18",
            }
        )

    previsto = (simulado.get("estatisticas_previstas") or {}).get("acerto_previsto")
    corte = como_numero(campos.get("nota_corte"))
    if previsto is not None and corte is not None:
        alvo = corte / 100 if corte > 1 else corte
        if previsto < alvo * (1 + MARGEM_DE_SEGURANCA_NA_NOTA):
            alertas.append(
                {
                    "tipo": "risco_na_nota",
                    "gravidade": "alta" if previsto < alvo else "media",
                    "detalhe": (
                        f"acerto previsto de {previsto:.0%} contra nota de corte de "
                        f"{alvo:.0%}"
                    ),
                    "base": (
                        "projeção do simulado (agente 16) comparada à nota de corte "
                        "informada; a previsão de desempenho é do agente 22"
                    ),
                }
            )

    return alertas


# --------------------------------------------------------------------------- #
# Entrada principal
# --------------------------------------------------------------------------- #

CONSUMIDORES = ["22", "23", "24"]


def _tempo_medio_por_questao(registros: list[dict], simulado: dict) -> dict:
    com_tempo = [r for r in registros if r["minutos"] and r["total"]]
    if com_tempo:
        minutos = sum(r["minutos"] for r in com_tempo)
        questoes = sum(r["total"] for r in com_tempo)
        return _indicador(
            round(minutos / questoes, 2),
            f"{minutos:g} min em {int(questoes)} questões registradas",
            "histórico do estudante",
        )
    previsto = (simulado.get("resumo_geral") or {}).get("tempo_previsto_min")
    questoes = (simulado.get("resumo_geral") or {}).get("numero_de_questoes")
    if previsto and questoes:
        return _indicador(
            round(previsto / questoes, 2),
            "tempo previsto do simulado, não medido: nenhum tempo real registrado",
            "agente 16",
        )
    return _indicador(None, "nenhum tempo de resolução registrado")


def _retencao(mapa_conhecimento: dict) -> dict:
    valores = [
        t.get("retencao_estimada")
        for d in mapa_conhecimento.get("disciplinas", [])
        for t in d.get("topicos", [])
        if t.get("retencao_estimada") is not None
    ]
    if not valores:
        return _indicador(None, "nenhuma retenção estimada")
    return _indicador(
        round(sum(valores) / len(valores), 4),
        f"média de {len(valores)} tópicos com retenção estimada",
        "agente 03",
    )


def _observacoes(igp: dict, desvio: dict, semanal: dict, mensal: dict) -> list[str]:
    observacoes: list[str] = []
    ausentes = [c for c in PESOS_DO_IGP if c not in igp["componentes"]]

    if igp["valor"] is None:
        observacoes.append(
            "IGP não calculado: nenhum componente tem dado. O painel não preenche "
            "lacuna com zero, porque zero é uma afirmação sobre o estudante."
        )
        return observacoes
    if ausentes:
        observacoes.append(
            f"IGP apoiado em {len(igp['componentes'])} de {len(PESOS_DO_IGP)} "
            f"componentes; sem dado para: {', '.join(ausentes)}. O peso foi "
            "redistribuído entre os presentes."
        )
    if not semanal["disponivel"] and not mensal["disponivel"]:
        observacoes.append(f"Evolução não declarada: {semanal['base']}.")
    if not desvio.get("disponivel"):
        observacoes.append(f"Desvio do cronograma não medido: {desvio['base']}.")
    return observacoes


def analisar(entradas: dict[str, Any], hoje: date | None = None) -> dict[str, Any]:
    """Constrói o Painel Inteligente de Performance."""
    hoje = hoje or date.today()
    dados = entradas.get("dados_usuario", {}) or {}
    campos = {k: v for k, v in dados.items() if k != "perfil"}
    if isinstance(dados.get("perfil"), dict):
        campos = {**campos, **dados["perfil"]}

    anteriores = entradas.get("saidas_anteriores", {})
    mapa_estrategico = anteriores.get("02", {}) or {}
    mapa_conhecimento = anteriores.get("03", {}) or {}
    arvore = anteriores.get("04", {}) or {}
    plano = anteriores.get("06", {}) or {}
    relatorio = anteriores.get("12", {}) or {}
    revisoes = anteriores.get("15", {}) or {}
    simulado = anteriores.get("16", {}) or {}
    relatorio_de_erros = anteriores.get("17", {}) or {}
    mapa_de_fraquezas = anteriores.get("18", {}) or {}
    acompanhamento = anteriores.get("19", {}) or {}
    habitos = anteriores.get("20", {}) or {}

    registros = _registros(campos)
    sessoes = sessoes_registradas(campos)
    estudados = dias_estudados(campos)

    taxa_de_acertos = _taxa(registros)
    taxa_de_erros = _indicador(
        round(1 - taxa_de_acertos["valor"], 4) if taxa_de_acertos["valor"] is not None else None,
        taxa_de_acertos["base"],
        taxa_de_acertos["origem"],
    )
    progresso = _progresso(arvore)
    retencao = _retencao(mapa_conhecimento)
    consistencia_do_coach = (acompanhamento.get("resumo_geral") or {}).get(
        "indice_de_consistencia"
    )
    if consistencia_do_coach is None:
        # Sem o agente 19 no fluxo, o painel mede a consistência pelo mesmo
        # código que ele usaria — nunca por uma fórmula própria.
        janela = consistencia_de(
            estudados,
            dias_planejados(plano, hoje - timedelta(days=JANELA_MENSAL - 1), hoje),
            JANELA_MENSAL,
        )
        consistencia_do_coach = janela["indice"]
        origem_da_consistencia = "medida pelo painel com o mesmo cálculo do agente 19"
    else:
        origem_da_consistencia = "agente 19"

    igp = _igp(
        _componentes_do_igp(
            mapa_conhecimento, taxa_de_acertos, progresso, consistencia_do_coach, retencao
        )
    )
    semanal = _evolucao(registros, hoje, JANELA_SEMANAL)
    mensal = _evolucao(registros, hoje, JANELA_MENSAL)
    desvio = _desvio_do_plano(plano, sessoes, estudados, hoje)
    minutos_estudados = sum(
        s["minutos"] for s in sessoes if s["houve_estudo"] and s["minutos"]
    )

    return {
        "atualizado_em": hoje.isoformat(),
        "resumo_geral": {
            "indice_geral_de_performance": igp,
            "percentual_de_progresso": progresso,
            "evolucao_semanal": semanal,
            "evolucao_mensal": mensal,
            "tendencia_geral": (
                mensal["tendencia"] if mensal["disponivel"] else semanal["tendencia"]
            ),
            "objetivo": mapa_estrategico.get("objetivo_principal"),
        },
        "indicadores_academicos": {
            "taxa_de_acertos": taxa_de_acertos,
            "taxa_de_erros": taxa_de_erros,
            "tempo_medio_por_questao_min": _tempo_medio_por_questao(registros, simulado),
            "tempo_total_estudado_h": _indicador(
                round(minutos_estudados / 60, 2) if minutos_estudados else None,
                f"{len([s for s in sessoes if s['houve_estudo']])} sessões registradas"
                if sessoes
                else "nenhuma sessão registrada",
                "histórico do estudante",
            ),
            "conteudos_concluidos": _indicador(
                progresso["concluidos"], progresso["base"], "agente 04"
            ),
            "conteudos_pendentes": _indicador(
                progresso["pendentes"], progresso["base"], "agente 04"
            ),
        },
        "indicadores_de_aprendizagem": {
            "retencao_estimada": retencao,
            "consistencia": _indicador(
                consistencia_do_coach,
                "dias estudados sobre dias planejados",
                origem_da_consistencia,
            ),
            "evolucao_do_conhecimento": _indicador(
                (relatorio.get("resumo_geral") or {}).get("tendencia_de_aprendizagem"),
                "tendência de aprendizagem medida no relatório de dificuldades",
                "agente 12",
            ),
            "evolucao_das_dificuldades": _indicador(
                (relatorio.get("resumo_geral") or {}).get("evolucao"),
                "comparação com o relatório de dificuldades anterior",
                "agente 12",
            ),
            "fragilidade_geral": _indicador(
                (mapa_de_fraquezas.get("resumo_geral") or {}).get(
                    "indice_geral_de_fragilidade"
                ),
                "índice geral de fragilidade do mapa de fraquezas",
                "agente 18",
            ),
            "erros_recorrentes": _indicador(
                len((relatorio_de_erros.get("indicadores") or {}).get("erros_recorrentes", [])),
                "padrões de erro que se repetiram",
                "agente 17",
            ),
        },
        "indicadores_comportamentais": {
            "frequencia_de_estudo": _indicador(
                (habitos.get("resumo_geral") or {}).get("frequencia"),
                "dias com estudo registrado nas últimas semanas",
                "agente 20",
            ),
            "regularidade": _indicador(
                (habitos.get("resumo_geral") or {}).get("sequencia_atual"),
                "sequência de dias consecutivos de estudo",
                "agente 20",
            ),
            "cumprimento_de_metas": _indicador(
                {
                    "cumpridas": len(
                        (acompanhamento.get("indicadores") or {}).get("metas_cumpridas", [])
                    ),
                    "pendentes": len(
                        (acompanhamento.get("indicadores") or {}).get("metas_pendentes", [])
                    ),
                },
                "metas registradas no plano de acompanhamento",
                "agente 19",
            ),
            "evolucao_dos_habitos": _indicador(
                (habitos.get("indicadores") or {}).get("evolucao_da_consistencia"),
                "adesão da janela atual contra a anterior",
                "agente 20",
            ),
            "engajamento": _indicador(
                (acompanhamento.get("resumo_geral") or {}).get("nivel_de_engajamento"),
                "nível de engajamento do plano de acompanhamento",
                "agente 19",
            ),
            "revisoes_agendadas": _indicador(
                len(revisoes.get("sessoes", [])),
                "sessões no plano de revisões",
                "agente 15",
            ),
        },
        "desempenho_por_nivel": _desempenho_por_nivel(
            arvore, mapa_conhecimento, relatorio, registros
        ),
        "desvio_do_planejado": desvio,
        "alertas": _alertas(semanal, mensal, desvio, mapa_de_fraquezas, simulado, campos),
        "metricas_para_previsao": {
            "destinatario": "22",
            "igp": igp["valor"],
            "taxa_de_acertos": taxa_de_acertos["valor"],
            "percentual_de_progresso": progresso["percentual"],
            "aderencia_aos_dias": desvio.get("aderencia_aos_dias"),
            "variacao_mensal": mensal.get("variacao"),
            "retencao_estimada": retencao["valor"],
            "base": (
                "insumos objetivos para a projeção do agente 22; este agente não "
                "projeta desempenho futuro"
            ),
        },
        "consumido_por": CONSUMIDORES,
        "observacoes": _observacoes(igp, desvio, semanal, mensal),
        "lacunas": [
            nome for nome, presente in (
                ("historico_de_questoes", bool(registros)),
                ("historico_frequencia", bool(sessoes)),
            )
            if not presente
        ],
        "confiabilidade": igp["confianca"],
        "constantes_aplicadas": {
            "pesos_do_igp": PESOS_DO_IGP,
            "valor_por_classificacao": VALOR_POR_CLASSIFICACAO,
            "faixas_do_igp": {nome: limite for limite, nome in FAIXAS_DO_IGP},
            "janela_semanal": JANELA_SEMANAL,
            "janela_mensal": JANELA_MENSAL,
            "minimo_de_questoes": MINIMO_DE_QUESTOES,
            "variacao_relevante": VARIACAO_RELEVANTE,
            "atraso_relevante": ATRASO_RELEVANTE,
            "margem_de_seguranca_na_nota": MARGEM_DE_SEGURANCA_NA_NOTA,
        },
    }


__all__ = [
    "ATRASO_RELEVANTE",
    "FAIXAS_DO_IGP",
    "JANELA_MENSAL",
    "JANELA_SEMANAL",
    "MARGEM_DE_SEGURANCA_NA_NOTA",
    "MINIMO_DE_QUESTOES",
    "NIVEL_MAXIMO_DO_IGP",
    "PESOS_DO_IGP",
    "TIPOS_DE_ALERTA",
    "VALOR_POR_CLASSIFICACAO",
    "VARIACAO_RELEVANTE",
    "analisar",
]
