"""Agente 22 — Forecast Agent.

Única responsabilidade: projetar a evolução do estudante a partir do que já
foi medido. Não ensina, não cria cronograma, não gera exercício, não altera o
plano.

As duas regras que moldam o módulo:

* **"Nunca apresentar previsões como certezas."** Aqui isso não é um aviso no
  rodapé: nenhuma projeção sai como número solto. Toda estimativa é um objeto
  com `estimativa`, `intervalo`, `confianca` e `base`, e o intervalo alarga
  quando os dados encolhem. Além disso, todo texto passa por um filtro de
  termos de certeza — "vai passar", "garantido", "com certeza" — e é recusado
  se prometer resultado.
* **"Nunca utilizar dados inexistentes."** A PAO só entra em cena com os
  componentes que existem, e o peso é redistribuído. Sem insumo nenhum ela sai
  `None` com a lista do que falta, em vez de um número bonito apoiado em nada.

A decisão estrutural é ter **um modelo só**. Cenários e alavancas não são
histórias diferentes: são a mesma função `_projetar` chamada com o estado
alterado por um delta declarado. Assim o cenário otimista não pode contradizer
o esperado — os dois saem da mesma conta, e a diferença entre eles é
exatamente o delta que está escrito na saída.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from app.studyos.agentes.comum import como_data, como_numero, como_texto

# --------------------------------------------------------------------------- #
# Constantes declaradas
# --------------------------------------------------------------------------- #

CENARIOS = ("otimista", "esperado", "pessimista")

#: Delta aplicado ao estado observado em cada cenário. O cenário esperado é o
#: estado como está — nenhuma correção "de bom senso" embutida.
DELTA_POR_CENARIO: dict[str, dict[str, float]] = {
    "otimista": {"aderencia": 0.15, "acerto": 0.05},
    "esperado": {"aderencia": 0.0, "acerto": 0.0},
    "pessimista": {"aderencia": -0.15, "acerto": -0.05},
}

#: Alavancas simuláveis: o delta que cada mudança aplica ao estado.
ALAVANCAS: dict[str, dict[str, Any]] = {
    "aumento_da_carga_horaria": {
        "delta": {"ritmo": 0.25},
        "descricao": "aumentar em 25% o tempo diário efetivo de estudo",
    },
    "melhora_na_consistencia": {
        "delta": {"aderencia": 0.20},
        "descricao": "cumprir 20 pontos percentuais a mais dos dias planejados",
    },
    "reforco_de_conteudos_criticos": {
        "delta": {"acerto": 0.08},
        "descricao": "recuperar os conteúdos em nível crítico do agente 18",
    },
    "aumento_da_retencao": {
        "delta": {"retencao": 0.15},
        "descricao": "elevar a retenção com revisão espaçada em dia",
    },
}

#: Peso de cada componente da Probabilidade de Atingimento do Objetivo.
PESOS_DA_PAO: dict[str, float] = {
    "cobertura": 0.35,
    "acerto": 0.35,
    "aderencia": 0.20,
    "retencao": 0.10,
}

#: Faixas da PAO.
FAIXAS_DA_PAO: tuple[tuple[float, str], ...] = (
    (0.35, "baixa"),
    (0.60, "moderada"),
    (0.80, "boa"),
)
PAO_MAXIMA = "alta"

#: Largura do intervalo da estimativa por nível de confiança. Menos dado,
#: intervalo mais largo — é assim que a incerteza aparece no número.
LARGURA_DO_INTERVALO: dict[str, float] = {"alta": 0.08, "media": 0.15, "baixa": 0.25}

#: Componentes mínimos para a PAO ser calculada.
MINIMO_DE_COMPONENTES = 2

#: Quanto a variação mensal medida pesa na extrapolação. Metade, porque
#: extrapolar uma tendência inteira até a data da prova é fingir que o
#: estudante vai melhorar para sempre no mesmo ritmo.
AMORTECIMENTO_DA_TENDENCIA = 0.5

#: Teto do ganho (ou da perda) extrapolado, em pontos de acerto.
#:
#: O amortecimento sozinho não basta: uma janela em que o estudante saltou 25
#: pontos, extrapolada por seis meses, chega a 100% de acerto — e um modelo que
#: projeta gabaritar a prova não está prevendo, está torcendo. O teto mantém a
#: tendência visível sem deixá-la virar promessa.
GANHO_MAXIMO_EXTRAPOLADO = 0.15

#: Termos que prometem resultado. Previsão que promete deixa de ser previsão.
TERMOS_DE_CERTEZA: tuple[str, ...] = (
    "com certeza",
    "certamente",
    "garantido",
    "garante",
    "sem duvida",
    "vai passar",
    "vai ser aprovado",
    "com toda certeza",
    "e certo que",
    "sera aprovado",
)

#: Frase que acompanha o relatório inteiro.
AVISO = (
    "Todos os números deste relatório são estimativas calculadas a partir dos "
    "dados disponíveis até a data de emissão. Não são garantia de resultado e "
    "mudam quando novos dados chegam."
)


class PrevisaoComoCerteza(Exception):
    """Texto de previsão que promete resultado em vez de estimá-lo."""


def _validar_texto(texto: str) -> None:
    normalizado = como_texto(texto)
    for termo in TERMOS_DE_CERTEZA:
        if termo in normalizado:
            raise PrevisaoComoCerteza(f"texto apresenta previsão como certeza: '{termo}'")


def _nivel_da_pao(valor: float) -> str:
    for limite, nome in FAIXAS_DA_PAO:
        if valor < limite:
            return nome
    return PAO_MAXIMA


def _estimativa(valor: float | None, confianca: str, base: str) -> dict:
    """Nenhum número de previsão sai sozinho: sempre com intervalo e base."""
    if valor is None:
        return {
            "estimativa": None,
            "intervalo": None,
            "confianca": "baixa",
            "base": base,
            "natureza": "estimativa",
        }
    largura = LARGURA_DO_INTERVALO[confianca]
    return {
        "estimativa": round(valor, 4),
        "intervalo": [
            round(max(0.0, valor - largura), 4),
            round(min(1.0, valor + largura), 4),
        ],
        "confianca": confianca,
        "base": base,
        "natureza": "estimativa",
    }


# --------------------------------------------------------------------------- #
# Estado observado
# --------------------------------------------------------------------------- #


def _estado(
    painel: dict, plano: dict, mapa_estrategico: dict, campos: dict, hoje: date
) -> dict:
    """O ponto de partida da projeção — só o que foi medido entra."""
    metricas = painel.get("metricas_para_previsao") or {}
    resumo = painel.get("resumo_geral") or {}
    progresso = (resumo.get("percentual_de_progresso") or {}).get("percentual")

    prazo = mapa_estrategico.get("prazo_final") or {}
    data_alvo = como_data(prazo.get("data")) or como_data(campos.get("data_prova"))
    dias_restantes = prazo.get("dias_restantes")
    if dias_restantes is None and data_alvo:
        dias_restantes = (data_alvo - hoje).days

    inicio = como_data((plano.get("resumo_geral") or {}).get("data_inicio"))
    dias_decorridos = max(1, (hoje - inicio).days) if inicio else None

    ritmo = None
    if progresso is not None and dias_decorridos:
        ritmo = progresso / dias_decorridos

    corte = como_numero(campos.get("nota_corte"))
    if corte is not None and corte > 1:
        corte = corte / 100

    return {
        "cobertura_atual": progresso,
        "ritmo_diario": ritmo,
        "acerto_atual": metricas.get("taxa_de_acertos"),
        "aderencia": metricas.get("aderencia_aos_dias"),
        "retencao": metricas.get("retencao_estimada"),
        "variacao_mensal": metricas.get("variacao_mensal"),
        "igp": metricas.get("igp"),
        "dias_restantes": dias_restantes,
        "dias_decorridos": dias_decorridos,
        "data_alvo": data_alvo.isoformat() if data_alvo else None,
        "nota_de_corte": corte,
        "base": (
            "métricas do agente 21, prazo do agente 02 e início do plano do agente 06"
        ),
    }


def _com_delta(estado: dict, delta: dict[str, float]) -> dict:
    """Aplica o delta declarado, mantendo tudo dentro de limites plausíveis."""
    ajustado = dict(estado)
    if "aderencia" in delta and estado["aderencia"] is not None:
        ajustado["aderencia"] = round(
            min(1.0, max(0.0, estado["aderencia"] + delta["aderencia"])), 4
        )
    if "acerto" in delta and estado["acerto_atual"] is not None:
        ajustado["acerto_atual"] = round(
            min(1.0, max(0.0, estado["acerto_atual"] + delta["acerto"])), 4
        )
    if "retencao" in delta and estado["retencao"] is not None:
        ajustado["retencao"] = round(
            min(1.0, max(0.0, estado["retencao"] + delta["retencao"])), 4
        )
    if "ritmo" in delta and estado["ritmo_diario"] is not None:
        ajustado["ritmo_diario"] = round(estado["ritmo_diario"] * (1 + delta["ritmo"]), 6)
    return ajustado


# --------------------------------------------------------------------------- #
# O modelo — um só, para cenários e alavancas
# --------------------------------------------------------------------------- #


def _projetar(estado: dict) -> dict:
    """Cobertura e acerto projetados na data-alvo.

    A cobertura avança no ritmo observado, descontado pela aderência: quem
    cumpre 60% dos dias avança 60% do ritmo. O acerto extrapola a variação
    medida com amortecimento — projetar a tendência inteira até a prova seria
    supor que o estudante melhora para sempre no mesmo passo.
    """
    dias = estado["dias_restantes"]
    cobertura = estado["cobertura_atual"]
    ritmo = estado["ritmo_diario"]
    aderencia = estado["aderencia"]

    if cobertura is None or ritmo is None or dias is None:
        cobertura_projetada = None
        base_cobertura = "sem progresso medido, ritmo ou prazo: cobertura não projetada"
    else:
        fator = aderencia if aderencia is not None else 1.0
        cobertura_projetada = min(1.0, cobertura + ritmo * max(0, dias) * fator)
        base_cobertura = (
            f"cobertura de {cobertura:.0%} avançando {ritmo:.4f}/dia por {dias} dias, "
            f"descontada pela aderência de {fator:.0%}"
        )

    acerto = estado["acerto_atual"]
    variacao = estado["variacao_mensal"]
    if acerto is None:
        acerto_projetado = None
        base_acerto = "sem taxa de acerto medida: desempenho não projetado"
    elif variacao is None or dias is None:
        acerto_projetado = acerto
        base_acerto = (
            f"acerto atual de {acerto:.0%} mantido; sem variação mensal medida "
            "para extrapolar"
        )
    else:
        meses = max(0, dias) / 30
        bruto = variacao * meses * AMORTECIMENTO_DA_TENDENCIA
        ganho = max(-GANHO_MAXIMO_EXTRAPOLADO, min(GANHO_MAXIMO_EXTRAPOLADO, bruto))
        acerto_projetado = min(1.0, max(0.0, acerto + ganho))
        base_acerto = (
            f"acerto de {acerto:.0%} extrapolado por {meses:.1f} meses com "
            f"amortecimento de {AMORTECIMENTO_DA_TENDENCIA:.0%}, "
            + (
                f"limitado ao teto de {GANHO_MAXIMO_EXTRAPOLADO:+.0%}"
                if abs(bruto) > GANHO_MAXIMO_EXTRAPOLADO
                else f"variação de {ganho:+.0%}"
            )
        )

    return {
        "cobertura_projetada": cobertura_projetada,
        "base_da_cobertura": base_cobertura,
        "acerto_projetado": acerto_projetado,
        "base_do_acerto": base_acerto,
    }


def _confianca(estado: dict, componentes: dict) -> str:
    """Confiança nasce da quantidade de insumo, não do otimismo do resultado."""
    if len(componentes) >= len(PESOS_DA_PAO) and estado["variacao_mensal"] is not None:
        return "alta"
    if len(componentes) >= MINIMO_DE_COMPONENTES:
        return "media"
    return "baixa"


def _componentes_da_pao(estado: dict, projecao: dict) -> dict[str, dict]:
    componentes: dict[str, dict] = {}

    if projecao["cobertura_projetada"] is not None:
        componentes["cobertura"] = {
            "valor": projecao["cobertura_projetada"],
            "base": projecao["base_da_cobertura"],
        }

    acerto = projecao["acerto_projetado"]
    if acerto is not None:
        corte = estado["nota_de_corte"]
        if corte:
            # Distância até o corte, normalizada: no corte vale 0,5; o dobro do
            # corte satura em 1. Sem corte informado, o próprio acerto responde.
            valor = min(1.0, max(0.0, 0.5 * acerto / corte)) if corte else acerto
            base = f"acerto projetado de {acerto:.0%} contra corte de {corte:.0%}"
        else:
            valor = acerto
            base = f"acerto projetado de {acerto:.0%}; nota de corte não informada"
        componentes["acerto"] = {"valor": round(valor, 4), "base": base}

    if estado["aderencia"] is not None:
        componentes["aderencia"] = {
            "valor": estado["aderencia"],
            "base": f"aderência de {estado['aderencia']:.0%} aos dias planejados",
        }

    if estado["retencao"] is not None:
        componentes["retencao"] = {
            "valor": estado["retencao"],
            "base": f"retenção estimada de {estado['retencao']:.0%}",
        }

    return componentes


def _pao(estado: dict, projecao: dict) -> dict:
    componentes = _componentes_da_pao(estado, projecao)
    if len(componentes) < MINIMO_DE_COMPONENTES:
        faltando = [c for c in PESOS_DA_PAO if c not in componentes]
        return {
            **_estimativa(
                None,
                "baixa",
                (
                    f"são necessários {MINIMO_DE_COMPONENTES} componentes medidos; "
                    f"faltam: {', '.join(faltando)}"
                ),
            ),
            "nivel": "indeterminada",
            "componentes": componentes,
        }

    peso_total = sum(PESOS_DA_PAO[c] for c in componentes)
    valor = (
        sum(PESOS_DA_PAO[c] * d["valor"] for c, d in componentes.items()) / peso_total
    )
    confianca = _confianca(estado, componentes)
    return {
        **_estimativa(
            valor,
            confianca,
            (
                f"média ponderada de {len(componentes)} componente(s) projetados; "
                "peso redistribuído entre os presentes"
            ),
        ),
        "nivel": _nivel_da_pao(valor),
        "componentes": componentes,
    }


# --------------------------------------------------------------------------- #
# Cenários
# --------------------------------------------------------------------------- #


def _cenario(nome: str, estado: dict, riscos: list[dict]) -> dict:
    delta = DELTA_POR_CENARIO[nome]
    ajustado = _com_delta(estado, delta)
    projecao = _projetar(ajustado)
    pao = _pao(ajustado, projecao)

    condicoes = [
        f"aderência {'subir' if valor > 0 else 'cair'} {abs(valor):.0%} em relação à atual"
        if chave == "aderencia"
        else f"taxa de acerto {'subir' if valor > 0 else 'cair'} {abs(valor):.0%}"
        for chave, valor in delta.items()
        if valor
    ]
    return {
        "cenario": nome,
        "delta_aplicado": delta,
        "cobertura_projetada": _estimativa(
            projecao["cobertura_projetada"], pao["confianca"], projecao["base_da_cobertura"]
        ),
        "acerto_projetado": _estimativa(
            projecao["acerto_projetado"], pao["confianca"], projecao["base_do_acerto"]
        ),
        "probabilidade": pao,
        "condicoes_necessarias": condicoes or ["manter o comportamento atual"],
        "principais_riscos": [r["risco"] for r in riscos[:3]],
    }


# --------------------------------------------------------------------------- #
# Fatores e alavancas
# --------------------------------------------------------------------------- #


def _fatores_positivos(
    estado: dict, painel: dict, habitos: dict, arvore: dict
) -> list[dict]:
    fatores: list[dict] = []

    for habito in (habitos.get("habitos_positivos") or {}).get("consolidados", []):
        fatores.append(
            {
                "fator": f"hábito consolidado: {habito['habito']}",
                "base": habito.get("base", "agente 20"),
                "origem": "agente 20",
            }
        )

    mensal = (painel.get("resumo_geral") or {}).get("evolucao_mensal") or {}
    if mensal.get("disponivel") and mensal.get("tendencia") == "melhora":
        fatores.append(
            {
                "fator": "evolução consistente na janela mensal",
                "base": mensal["base"],
                "origem": "agente 21",
            }
        )

    dominados = arvore.get("conteudos_dominados") or []
    if dominados:
        fatores.append(
            {
                "fator": f"{len(dominados)} conteúdo(s) já dominado(s)",
                "base": ", ".join(dominados[:5]),
                "origem": "agente 04",
            }
        )

    if estado["aderencia"] is not None and estado["aderencia"] >= 0.8:
        fatores.append(
            {
                "fator": f"aderência de {estado['aderencia']:.0%} ao cronograma",
                "base": "dias planejados cumpridos",
                "origem": "agente 21",
            }
        )
    return fatores


def _fatores_de_risco(
    estado: dict, painel: dict, mapa_de_fraquezas: dict, acompanhamento: dict
) -> list[dict]:
    riscos: list[dict] = []

    for alerta in painel.get("alertas", []):
        riscos.append(
            {
                "risco": alerta["detalhe"],
                "tipo": alerta["tipo"],
                "gravidade": alerta["gravidade"],
                "base": alerta["base"],
                "origem": "agente 21",
            }
        )

    if estado["retencao"] is not None and estado["retencao"] < 0.6:
        riscos.append(
            {
                "risco": f"retenção estimada de {estado['retencao']:.0%}",
                "tipo": "baixa_retencao",
                "gravidade": "media",
                "base": "média das retenções medidas pelo agente 03",
                "origem": "agente 21",
            }
        )

    abandono = (acompanhamento.get("resumo_geral") or {}).get("risco_de_abandono") or {}
    if abandono.get("nivel") in ("alto", "critico"):
        riscos.append(
            {
                "risco": f"risco de abandono {abandono['nivel']}",
                "tipo": "baixa_frequencia",
                "gravidade": "alta",
                "base": abandono.get("base", "agente 19"),
                "origem": "agente 19",
            }
        )

    criticos = [
        f["topico"]
        for f in mapa_de_fraquezas.get("fraquezas", [])
        if f.get("nivel_de_prioridade") == "prioridade_maxima"
    ]
    if criticos:
        riscos.append(
            {
                "risco": f"{len(criticos)} conteúdo(s) em prioridade máxima",
                "tipo": "conteudo_critico",
                "gravidade": "alta",
                "base": ", ".join(criticos[:5]),
                "origem": "agente 18",
            }
        )

    ordem = {"alta": 0, "media": 1, "baixa": 2}
    return sorted(riscos, key=lambda r: ordem.get(r["gravidade"], 3))


def _simular_alavancas(estado: dict, base: dict) -> list[dict]:
    """Cada alavanca é o mesmo modelo com um delta declarado — nada inventado."""
    referencia = base["estimativa"]
    simulacoes: list[dict] = []

    for nome, alavanca in ALAVANCAS.items():
        ajustado = _com_delta(estado, alavanca["delta"])
        if ajustado == estado:
            simulacoes.append(
                {
                    "acao": nome,
                    "descricao": alavanca["descricao"],
                    "impacto_na_probabilidade": None,
                    "base": "o dado que esta alavanca move não foi medido",
                }
            )
            continue

        resultado = _pao(ajustado, _projetar(ajustado))
        ganho = (
            round(resultado["estimativa"] - referencia, 4)
            if resultado["estimativa"] is not None and referencia is not None
            else None
        )
        simulacoes.append(
            {
                "acao": nome,
                "descricao": alavanca["descricao"],
                "delta_aplicado": alavanca["delta"],
                "probabilidade_resultante": resultado["estimativa"],
                "impacto_na_probabilidade": ganho,
                "base": (
                    "mesma projeção com o estado alterado pelo delta declarado"
                ),
            }
        )

    com_impacto = [s for s in simulacoes if s["impacto_na_probabilidade"] is not None]
    sem_impacto = [s for s in simulacoes if s["impacto_na_probabilidade"] is None]
    return (
        sorted(com_impacto, key=lambda s: -s["impacto_na_probabilidade"]) + sem_impacto
    )


def _recomendacoes(
    simulacoes: list[dict], riscos: list[dict], mapa_de_fraquezas: dict
) -> dict:
    """A ação de maior impacto simulado vira prioridade — com o número junto."""
    uteis = [s for s in simulacoes if s["impacto_na_probabilidade"]]
    urgentes = (mapa_de_fraquezas.get("ranking") or {}).get("mais_urgentes", [])

    prioridade = None
    if uteis:
        alvo = uteis[0]
        prioridade = {
            "acao": alvo["acao"],
            "descricao": alvo["descricao"],
            "impacto_estimado": alvo["impacto_na_probabilidade"],
            "base": "maior ganho entre as alavancas simuladas",
        }
    elif urgentes:
        prioridade = {
            "acao": "reforco_de_conteudos_criticos",
            "descricao": f"tratar {urgentes[0]['topico']}, o conteúdo mais urgente",
            "impacto_estimado": None,
            "base": "ranking de urgência do agente 18; impacto não simulável sem medição",
        }

    return {
        "prioridade_maxima": prioridade,
        "acoes_recomendadas": [
            {
                "acao": s["acao"],
                "descricao": s["descricao"],
                "impacto_estimado": s["impacto_na_probabilidade"],
            }
            for s in simulacoes
        ],
        "riscos_a_mitigar": [r["risco"] for r in riscos[:3]],
        "executor": "23",
        "base": (
            "este agente recomenda e estima impacto; quem reorganiza o plano é o "
            "agente 23"
        ),
    }


# --------------------------------------------------------------------------- #
# Entrada principal
# --------------------------------------------------------------------------- #

CONSUMIDORES = ["23", "24"]


def _observacoes(estado: dict, pao: dict, recusados: list[dict]) -> list[str]:
    observacoes: list[str] = [AVISO]

    if pao["estimativa"] is None:
        observacoes.append(f"PAO não calculada: {pao['base']}.")
    else:
        ausentes = [c for c in PESOS_DA_PAO if c not in pao["componentes"]]
        if ausentes:
            observacoes.append(
                f"PAO apoiada em {len(pao['componentes'])} de {len(PESOS_DA_PAO)} "
                f"componentes; sem dado para: {', '.join(ausentes)}."
            )
    if estado["dias_restantes"] is None:
        observacoes.append(
            "Sem data-alvo informada: a projeção não tem horizonte e a cobertura "
            "futura não foi estimada."
        )
    if estado["variacao_mensal"] is None:
        observacoes.append(
            "Sem variação mensal medida: o acerto foi mantido no valor atual em vez "
            "de extrapolado."
        )
    if recusados:
        observacoes.append(
            f"{len(recusados)} texto(s) recusado(s) por apresentar previsão como "
            "certeza."
        )
    return observacoes


def prever(entradas: dict[str, Any], hoje: date | None = None) -> dict[str, Any]:
    """Constrói o Relatório de Previsão."""
    hoje = hoje or date.today()
    dados = entradas.get("dados_usuario", {}) or {}
    campos = {k: v for k, v in dados.items() if k != "perfil"}
    if isinstance(dados.get("perfil"), dict):
        campos = {**campos, **dados["perfil"]}

    anteriores = entradas.get("saidas_anteriores", {})
    mapa_estrategico = anteriores.get("02", {}) or {}
    arvore = anteriores.get("04", {}) or {}
    plano = anteriores.get("06", {}) or {}
    mapa_de_fraquezas = anteriores.get("18", {}) or {}
    acompanhamento = anteriores.get("19", {}) or {}
    habitos = anteriores.get("20", {}) or {}
    painel = anteriores.get("21", {}) or {}

    estado = _estado(painel, plano, mapa_estrategico, campos, hoje)
    projecao = _projetar(estado)
    pao = _pao(estado, projecao)

    positivos = _fatores_positivos(estado, painel, habitos, arvore)
    riscos = _fatores_de_risco(estado, painel, mapa_de_fraquezas, acompanhamento)
    cenarios = {nome: _cenario(nome, estado, riscos) for nome in CENARIOS}
    simulacoes = _simular_alavancas(estado, pao)
    recomendacoes = _recomendacoes(simulacoes, riscos, mapa_de_fraquezas)

    recusados: list[dict] = []
    for rotulo, texto in [
        ("aviso", AVISO),
        *(
            (f"condicao:{nome}", condicao)
            for nome, cenario in cenarios.items()
            for condicao in cenario["condicoes_necessarias"]
        ),
        *((f"acao:{s['acao']}", s["descricao"]) for s in simulacoes),
    ]:
        try:
            _validar_texto(texto)
        except PrevisaoComoCerteza as recusa:
            recusados.append({"onde": rotulo, "texto": texto, "motivo": str(recusa)})

    tendencia = (painel.get("resumo_geral") or {}).get("tendencia_geral", "indeterminada")

    return {
        "emitido_em": hoje.isoformat(),
        "aviso": AVISO,
        "resumo_geral": {
            "probabilidade_de_atingir_o_objetivo": pao,
            "tendencia_geral": tendencia,
            "evolucao_prevista": {
                "cobertura_projetada": _estimativa(
                    projecao["cobertura_projetada"],
                    pao["confianca"],
                    projecao["base_da_cobertura"],
                ),
                "acerto_projetado": _estimativa(
                    projecao["acerto_projetado"],
                    pao["confianca"],
                    projecao["base_do_acerto"],
                ),
                "data_alvo": estado["data_alvo"],
                "dias_restantes": estado["dias_restantes"],
            },
            "nivel_de_confianca": pao["confianca"],
            "base_da_confianca": (
                "quantidade de componentes medidos e existência de tendência "
                "mensal; confiança não depende do resultado projetado"
            ),
        },
        "cenarios": cenarios,
        "fatores_positivos": positivos,
        "fatores_de_risco": riscos,
        "simulacoes": simulacoes,
        "recomendacoes": recomendacoes,
        "estado_observado": estado,
        "textos_recusados": recusados,
        "consumido_por": CONSUMIDORES,
        "observacoes": _observacoes(estado, pao, recusados),
        "lacunas": [
            nome
            for nome, presente in (
                ("painel_de_performance_do_agente_21", bool(painel)),
                ("data_alvo", estado["dias_restantes"] is not None),
                ("nota_corte", estado["nota_de_corte"] is not None),
            )
            if not presente
        ],
        "confiabilidade": pao["confianca"],
        "constantes_aplicadas": {
            "delta_por_cenario": DELTA_POR_CENARIO,
            "alavancas": {nome: a["delta"] for nome, a in ALAVANCAS.items()},
            "pesos_da_pao": PESOS_DA_PAO,
            "faixas_da_pao": {nome: limite for limite, nome in FAIXAS_DA_PAO},
            "largura_do_intervalo": LARGURA_DO_INTERVALO,
            "amortecimento_da_tendencia": AMORTECIMENTO_DA_TENDENCIA,
            "ganho_maximo_extrapolado": GANHO_MAXIMO_EXTRAPOLADO,
            "minimo_de_componentes": MINIMO_DE_COMPONENTES,
            "termos_de_certeza": TERMOS_DE_CERTEZA,
        },
    }


__all__ = [
    "ALAVANCAS",
    "AMORTECIMENTO_DA_TENDENCIA",
    "AVISO",
    "CENARIOS",
    "DELTA_POR_CENARIO",
    "FAIXAS_DA_PAO",
    "GANHO_MAXIMO_EXTRAPOLADO",
    "LARGURA_DO_INTERVALO",
    "MINIMO_DE_COMPONENTES",
    "PAO_MAXIMA",
    "PESOS_DA_PAO",
    "TERMOS_DE_CERTEZA",
    "PrevisaoComoCerteza",
    "prever",
]
