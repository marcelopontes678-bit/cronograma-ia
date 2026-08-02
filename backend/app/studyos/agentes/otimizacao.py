"""Agente 23 — Optimization Agent.

Única responsabilidade: encontrar onde o sistema está desperdiçando esforço e
propor a correção. Não ensina, não cria aula, não gera exercício, não altera o
currículo.

A regra mais importante aqui não é sobre o que o agente calcula, e sim sobre o
que ele **não faz**: "nunca modificar diretamente qualquer agente", "nunca
alterar o cronograma diretamente", "toda alteração deve ser enviada ao Master
Orchestrator para aprovação". Isso vira mecanismo de três formas:

* **A saída é um pedido, não um ato.** Cada otimização carrega
  `aprovacao_necessaria: True` e vira uma `solicitacao_de_atualizacao`
  endereçada ao orquestrador, com `status: "aguardando_aprovacao"`.
* **A saída não carrega estrutura executável.** Nenhum cronograma, nenhuma
  árvore, nenhuma sessão — só a descrição do que mudar e em qual agente. O
  teste verifica a ausência.
* **Otimização sem evidência não existe.** Cada recomendação nasce de um
  detector que só dispara com número medido, e cada uma lista as evidências
  com valor e origem. Detector sem dado não inventa problema: fica calado.

O ganho estimado também não é inventado: quando a otimização corresponde a uma
alavanca que o agente 22 já precificou, o número **é** o dele. Dois agentes
prometendo ganhos diferentes para a mesma ação seria pior que nenhum número.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from app.studyos.agentes.comum import como_numero, como_texto, preenchido

# --------------------------------------------------------------------------- #
# Constantes declaradas
# --------------------------------------------------------------------------- #

CATEGORIAS = (
    "gargalo",
    "desperdicio_de_tempo",
    "estudo_alem_do_necessario",
    "baixa_retencao",
    "cronograma",
    "revisao",
    "estrategia_didatica",
    "aceleracao",
)

#: Peso de cada componente do Índice Geral de Eficiência. Componente sem dado
#: não entra e o peso é redistribuído entre os presentes.
PESOS_DA_EFICIENCIA: dict[str, float] = {
    "aproveitamento_do_tempo": 0.30,
    "eficacia_do_estudo": 0.30,
    "cobertura_das_revisoes": 0.20,
    "retencao": 0.20,
}

#: Faixas do Índice Geral de Eficiência.
FAIXAS_DA_EFICIENCIA: tuple[tuple[float, str], ...] = (
    (0.40, "baixa"),
    (0.65, "moderada"),
    (0.85, "boa"),
)
EFICIENCIA_MAXIMA = "alta"

#: Retenção abaixo da qual o conteúdo entra como oportunidade de otimização.
LIMIAR_DE_RETENCAO = 0.60

#: Aderência ao cronograma abaixo da qual o plano é grande demais para a rotina.
LIMIAR_DE_ADERENCIA = 0.70

#: Erros do mesmo tipo a partir dos quais a estratégia didática é questionada.
MINIMO_DE_ERROS_DO_TIPO = 3

#: Peso da disciplina no edital abaixo do qual estudar além do necessário custa
#: mais do que rende.
PESO_BAIXO_NO_EDITAL = 0.15

#: Prioridade por gravidade do problema detectado.
ORDEM_DE_PRIORIDADE = ("critica", "alta", "media", "baixa")

#: Tipo de erro predominante (agente 17) → mudança de estratégia didática, com
#: o agente que executa a mudança.
ESTRATEGIA_POR_TIPO_DE_ERRO: dict[str, dict[str, str]] = {
    "conceitual": {
        "acao": "trocar a ordem: conceito antes de bateria de questões",
        "agente": "13",
    },
    "interpretacao": {
        "acao": "priorizar questões comentadas sobre leitura de resumo",
        "agente": "13",
    },
    "calculo": {
        "acao": "aumentar a proporção de exemplos resolvidos passo a passo",
        "agente": "08",
    },
    "memorizacao": {
        "acao": "antecipar a revisão e aumentar a carga de flashcards",
        "agente": "14",
    },
    "atencao": {
        "acao": "incluir conferência da resposta no critério de conclusão da sessão",
        "agente": "15",
    },
    "gestao_do_tempo": {
        "acao": "treinar com cronômetro por questão antes do próximo simulado",
        "agente": "16",
    },
    "estrategia": {
        "acao": "definir ordem de resolução e critério de abandono da questão",
        "agente": "19",
    },
}

#: Alavanca do agente 22 que precifica cada categoria. Quando existe, o ganho
#: estimado é o número dele — este agente não produz uma segunda versão.
ALAVANCA_POR_CATEGORIA: dict[str, str] = {
    "cronograma": "melhora_na_consistencia",
    "gargalo": "reforco_de_conteudos_criticos",
    "baixa_retencao": "aumento_da_retencao",
    "desperdicio_de_tempo": "aumento_da_carga_horaria",
}


def _nivel_da_eficiencia(valor: float) -> str:
    for limite, nome in FAIXAS_DA_EFICIENCIA:
        if valor < limite:
            return nome
    return EFICIENCIA_MAXIMA


def _evidencia(indicador: str, valor: Any, origem: str) -> dict:
    return {"indicador": indicador, "valor": valor, "origem": origem}


# --------------------------------------------------------------------------- #
# Índice Geral de Eficiência
# --------------------------------------------------------------------------- #


def _componentes_da_eficiencia(
    painel: dict, revisoes: dict, mapa_conhecimento: dict
) -> dict[str, dict]:
    """Eficiência é resultado por esforço — só entra o que foi medido."""
    componentes: dict[str, dict] = {}

    desvio = painel.get("desvio_do_planejado") or {}
    if desvio.get("disponivel"):
        planejadas = desvio.get("horas_planejadas") or 0
        estudadas = desvio.get("horas_estudadas") or 0
        if planejadas:
            componentes["aproveitamento_do_tempo"] = {
                "valor": round(min(1.0, estudadas / planejadas), 4),
                "base": f"{estudadas:g}h estudadas de {planejadas:g}h planejadas",
                "origem": "agente 21",
            }

    taxa = ((painel.get("indicadores_academicos") or {}).get("taxa_de_acertos") or {}).get(
        "valor"
    )
    if taxa is not None:
        componentes["eficacia_do_estudo"] = {
            "valor": taxa,
            "base": f"taxa de acerto de {taxa:.0%}",
            "origem": "agente 21",
        }

    cobertura = (revisoes.get("indicadores") or {}).get("cobertura_das_revisoes")
    if cobertura is not None:
        componentes["cobertura_das_revisoes"] = {
            "valor": round(float(cobertura), 4),
            "base": f"{cobertura:.0%} das revisões previstas viraram sessão",
            "origem": "agente 15",
        }

    retencoes = [
        t.get("retencao_estimada")
        for d in mapa_conhecimento.get("disciplinas", [])
        for t in d.get("topicos", [])
        if t.get("retencao_estimada") is not None
    ]
    if retencoes:
        componentes["retencao"] = {
            "valor": round(sum(retencoes) / len(retencoes), 4),
            "base": f"média de {len(retencoes)} tópicos com retenção estimada",
            "origem": "agente 03",
        }

    return componentes


def _eficiencia(componentes: dict[str, dict]) -> dict:
    if not componentes:
        return {
            "valor": None,
            "nivel": "indeterminado",
            "componentes": {},
            "confianca": "baixa",
            "base": "nenhum componente medido; a eficiência não é estimada sem dado",
        }
    peso_total = sum(PESOS_DA_EFICIENCIA[c] for c in componentes)
    valor = (
        sum(PESOS_DA_EFICIENCIA[c] * d["valor"] for c, d in componentes.items())
        / peso_total
    )
    return {
        "valor": round(valor, 4),
        "nivel": _nivel_da_eficiencia(valor),
        "componentes": componentes,
        "confianca": (
            "alta" if len(componentes) >= 3
            else "media" if len(componentes) == 2
            else "baixa"
        ),
        "base": (
            f"média ponderada de {len(componentes)} componente(s); peso "
            "redistribuído entre os presentes"
        ),
    }


# --------------------------------------------------------------------------- #
# Detectores — cada um só dispara com número medido
# --------------------------------------------------------------------------- #


def _gargalos(mapa_de_fraquezas: dict) -> list[dict]:
    """Conteúdo frágil que trava outros: o problema mais caro do sistema."""
    achados: list[dict] = []
    for fraqueza in mapa_de_fraquezas.get("fraquezas", []):
        dependentes = fraqueza.get("conteudos_dependentes_afetados") or []
        if not dependentes or fraqueza.get("nivel_de_prioridade") not in (
            "critico",
            "prioridade_maxima",
        ):
            continue
        achados.append(
            {
                "categoria": "gargalo",
                "problema": (
                    f"{fraqueza['topico']} está frágil e trava "
                    f"{len(dependentes)} conteúdo(s)"
                ),
                "evidencias": [
                    _evidencia(
                        "indice_de_fraqueza", fraqueza["indice_de_fraqueza"], "agente 18"
                    ),
                    _evidencia("conteudos_bloqueados", dependentes, "agente 05"),
                ],
                "acao": f"priorizar a recuperação de {fraqueza['topico']} antes dos dependentes",
                "agentes_afetados": ["06", "15"],
                "gravidade": "critica",
            }
        )
    return achados


def _desperdicio_de_tempo(painel: dict, relatorio: dict) -> list[dict]:
    """Tempo gasto muito acima do estimado, medido pelo agente 12."""
    achados: list[dict] = []
    velocidade = (relatorio.get("resumo_geral") or {}).get("velocidade_de_aprendizagem") or {}
    razao = velocidade.get("razao_tempo_real_sobre_estimado")
    if razao is not None and razao > 1.3:
        achados.append(
            {
                "categoria": "desperdicio_de_tempo",
                "problema": (
                    f"tempo real de estudo {razao:.0%} do estimado: o método atual "
                    "custa mais do que o previsto"
                ),
                "evidencias": [
                    _evidencia("razao_tempo_real_sobre_estimado", razao, "agente 12"),
                ],
                "acao": "revisar a estimativa de tempo por conteúdo ou o método de estudo",
                "agentes_afetados": ["04", "06", "13"],
                "gravidade": "media",
            }
        )

    desvio = painel.get("desvio_do_planejado") or {}
    if desvio.get("disponivel") and (desvio.get("horas_de_diferenca") or 0) > 0:
        achados.append(
            {
                "categoria": "desperdicio_de_tempo",
                "problema": (
                    f"{desvio['horas_de_diferenca']:+g}h estudadas além do planejado "
                    "sem ganho proporcional registrado"
                ),
                "evidencias": [
                    _evidencia("horas_planejadas", desvio["horas_planejadas"], "agente 06"),
                    _evidencia("horas_estudadas", desvio["horas_estudadas"], "agente 21"),
                ],
                "acao": "conferir se o excedente está indo para conteúdo prioritário",
                "agentes_afetados": ["06"],
                "gravidade": "baixa",
            }
        )
    return achados


def _estudo_alem_do_necessario(
    mapa_de_fraquezas: dict, mapa_estrategico: dict, plano: dict
) -> list[dict]:
    """Conteúdo dominado, de peso baixo, ainda ocupando espaço no cronograma."""
    pesos = _pesos_por_disciplina(mapa_estrategico)
    agendados = {
        como_texto(s.get("conteudo") or "")
        for dia in plano.get("cronograma", [])
        for s in dia.get("sessoes", [])
        if s.get("tipo") == "conteudo"
    }

    achados: list[dict] = []
    for fraqueza in mapa_de_fraquezas.get("fraquezas", []):
        if (fraqueza.get("recomendacao") or {}).get("acao") != "avancar":
            continue
        if como_texto(fraqueza["topico"]) not in agendados:
            continue
        peso = pesos.get(como_texto(fraqueza.get("disciplina") or ""), 0)
        if peso > PESO_BAIXO_NO_EDITAL:
            continue
        achados.append(
            {
                "categoria": "estudo_alem_do_necessario",
                "problema": (
                    f"{fraqueza['topico']} já está dominado e vale {peso:.0%} do "
                    "edital, mas continua no cronograma"
                ),
                "evidencias": [
                    _evidencia(
                        "indice_de_fraqueza", fraqueza["indice_de_fraqueza"], "agente 18"
                    ),
                    _evidencia("peso_no_edital", round(peso, 4), "agente 02"),
                ],
                "acao": (
                    f"liberar o tempo de {fraqueza['topico']} para conteúdo de maior "
                    "retorno"
                ),
                "agentes_afetados": ["06"],
                "gravidade": "media",
            }
        )
    return achados


def _baixa_retencao(mapa_conhecimento: dict, revisoes_agendadas: set[str]) -> list[dict]:
    """Retenção baixa em conteúdo que não está agendado para revisão."""
    achados: list[dict] = []
    for disciplina in mapa_conhecimento.get("disciplinas", []):
        for topico in disciplina.get("topicos", []):
            retencao = topico.get("retencao_estimada")
            if retencao is None or retencao >= LIMIAR_DE_RETENCAO:
                continue
            if como_texto(topico["topico"]) in revisoes_agendadas:
                continue
            achados.append(
                {
                    "categoria": "baixa_retencao",
                    "problema": (
                        f"{topico['topico']} com retenção de {retencao:.0%} e sem "
                        "revisão agendada"
                    ),
                    "evidencias": [
                        _evidencia("retencao_estimada", retencao, "agente 03"),
                        _evidencia(
                            "limiar_de_retencao", LIMIAR_DE_RETENCAO, "agente 23"
                        ),
                    ],
                    "acao": f"antecipar a revisão de {topico['topico']}",
                    "agentes_afetados": ["14", "15"],
                    "gravidade": "alta",
                }
            )
    return achados


def _cronograma(painel: dict, habitos: dict) -> list[dict]:
    """Plano que o estudante não consegue cumprir é plano grande demais."""
    desvio = painel.get("desvio_do_planejado") or {}
    if not desvio.get("disponivel"):
        return []
    aderencia = desvio.get("aderencia_aos_dias")
    if aderencia is None or aderencia >= LIMIAR_DE_ADERENCIA:
        return []

    meta = (habitos.get("plano_de_acao") or {}).get("meta_diaria") or {}
    evidencias = [
        _evidencia("aderencia_aos_dias", aderencia, "agente 21"),
        _evidencia("dias_cumpridos", desvio["dias_cumpridos"], "agente 21"),
    ]
    if meta.get("minutos") is not None:
        evidencias.append(_evidencia("meta_diaria_min", meta["minutos"], "agente 20"))

    return [
        {
            "categoria": "cronograma",
            "problema": (
                f"apenas {aderencia:.0%} dos dias planejados foram cumpridos: a carga "
                "diária não cabe na rotina"
            ),
            "evidencias": evidencias,
            "acao": "reduzir a carga diária até a aderência voltar a subir",
            "agentes_afetados": ["06", "20"],
            "gravidade": "alta",
        }
    ]


def _revisao(revisoes: dict, memoria: dict) -> list[dict]:
    """Revisão prevista que não virou sessão é revisão que não aconteceu."""
    achados: list[dict] = []
    nao_alocados = revisoes.get("conteudos_nao_alocados") or []
    if nao_alocados:
        achados.append(
            {
                "categoria": "revisao",
                "problema": (
                    f"{len(nao_alocados)} conteúdo(s) previstos para revisão ficaram "
                    "sem sessão"
                ),
                "evidencias": [
                    _evidencia(
                        "conteudos_nao_alocados",
                        [c.get("topico") for c in nao_alocados],
                        "agente 15",
                    ),
                    _evidencia(
                        "cobertura_das_revisoes",
                        (revisoes.get("indicadores") or {}).get("cobertura_das_revisoes"),
                        "agente 15",
                    ),
                ],
                "acao": "ampliar o bloco de revisão ou redistribuir as revisões do período",
                "agentes_afetados": ["06", "14", "15"],
                "gravidade": "alta",
            }
        )

    nao_elegiveis = (memoria.get("resumo_geral") or {}).get("conteudos_nao_elegiveis")
    if nao_elegiveis:
        achados.append(
            {
                "categoria": "revisao",
                "problema": (
                    f"{nao_elegiveis} conteúdo(s) fora do ciclo de revisão por não "
                    "terem sido estudados"
                ),
                "evidencias": [
                    _evidencia("conteudos_nao_elegiveis", nao_elegiveis, "agente 14")
                ],
                "acao": "avançar o estudo desses conteúdos antes de ampliar a revisão",
                "agentes_afetados": ["06"],
                "gravidade": "media",
            }
        )
    return achados


def _estrategia_didatica(relatorio_de_erros: dict) -> list[dict]:
    """Tipo de erro que se repete indica método errado, não esforço insuficiente."""
    contagem = (relatorio_de_erros.get("resumo_geral") or {}).get("contagem_por_tipo") or {}
    achados: list[dict] = []
    for tipo, quantidade in contagem.items():
        if quantidade < MINIMO_DE_ERROS_DO_TIPO or tipo not in ESTRATEGIA_POR_TIPO_DE_ERRO:
            continue
        estrategia = ESTRATEGIA_POR_TIPO_DE_ERRO[tipo]
        achados.append(
            {
                "categoria": "estrategia_didatica",
                "problema": f"{quantidade} erros do tipo {tipo} concentrados",
                "evidencias": [
                    _evidencia(f"erros_{tipo}", quantidade, "agente 17"),
                    _evidencia(
                        "minimo_de_erros_do_tipo", MINIMO_DE_ERROS_DO_TIPO, "agente 23"
                    ),
                ],
                "acao": estrategia["acao"],
                "agentes_afetados": [estrategia["agente"]],
                "gravidade": "media",
            }
        )
    return achados


def _aceleracao(mapa_de_fraquezas: dict, previsao: dict) -> list[dict]:
    """Onde dá para andar mais rápido sem perder o que já está firme."""
    achados: list[dict] = []
    prontos = [
        f["topico"]
        for f in mapa_de_fraquezas.get("fraquezas", [])
        if (f.get("recomendacao") or {}).get("acao") == "avancar"
    ]
    if prontos:
        achados.append(
            {
                "categoria": "aceleracao",
                "problema": (
                    f"{len(prontos)} conteúdo(s) com domínio suficiente para avançar"
                ),
                "evidencias": [_evidencia("conteudos_prontos", prontos, "agente 18")],
                "acao": "antecipar o conteúdo seguinte desses tópicos no cronograma",
                "agentes_afetados": ["06"],
                "gravidade": "baixa",
            }
        )

    cobertura = (
        ((previsao.get("resumo_geral") or {}).get("evolucao_prevista") or {})
        .get("cobertura_projetada", {})
        .get("estimativa")
    )
    if cobertura is not None and cobertura < 1.0:
        achados.append(
            {
                "categoria": "aceleracao",
                "problema": (
                    f"cobertura projetada de {cobertura:.0%} até a data-alvo: o ritmo "
                    "atual não fecha o edital"
                ),
                "evidencias": [
                    _evidencia("cobertura_projetada", cobertura, "agente 22"),
                ],
                "acao": "aumentar o ritmo ou reduzir o escopo com o peso do edital",
                "agentes_afetados": ["02", "06"],
                "gravidade": "alta",
            }
        )
    return achados


def _pesos_por_disciplina(mapa_estrategico: dict) -> dict[str, float]:
    pesos = {
        como_texto(d["nome"]): float(d.get("questoes") or d.get("peso") or 0)
        for d in mapa_estrategico.get("disciplinas", [])
    }
    total = sum(pesos.values())
    return {nome: valor / total for nome, valor in pesos.items()} if total else {}


# --------------------------------------------------------------------------- #
# Priorização e impacto
# --------------------------------------------------------------------------- #


def _ganho_da_alavanca(categoria: str, previsao: dict) -> dict | None:
    """Ganho precificado pelo agente 22 para a alavanca desta categoria.

    Se o 22 já estimou o impacto daquela mudança, o número é o dele. Dois
    agentes prometendo ganhos diferentes para a mesma ação seria pior que
    nenhum número.
    """
    alavanca = ALAVANCA_POR_CATEGORIA.get(categoria)
    if not alavanca:
        return None
    for simulacao in previsao.get("simulacoes", []):
        if simulacao["acao"] == alavanca:
            return {
                "ganho_na_probabilidade": simulacao.get("impacto_na_probabilidade"),
                "alavanca": alavanca,
                "origem": "agente 22",
                "base": simulacao.get("base", "simulação do agente 22"),
            }
    return None


def _montar(achados: list[dict], previsao: dict) -> list[dict]:
    """Otimização só existe com evidência; sem ela, nem entra na lista."""
    otimizacoes: list[dict] = []
    for achado in achados:
        evidencias = [e for e in achado["evidencias"] if preenchido(e["valor"])]
        if not evidencias:
            continue
        otimizacoes.append(
            {
                **achado,
                "evidencias": evidencias,
                "impacto_esperado": _ganho_da_alavanca(achado["categoria"], previsao),
                "aprovacao_necessaria": True,
            }
        )

    ordem = {nome: indice for indice, nome in enumerate(ORDEM_DE_PRIORIDADE)}
    otimizacoes.sort(
        key=lambda o: (
            ordem.get(o["gravidade"], len(ORDEM_DE_PRIORIDADE)),
            -((o["impacto_esperado"] or {}).get("ganho_na_probabilidade") or 0),
        )
    )
    for posicao, otimizacao in enumerate(otimizacoes, start=1):
        otimizacao["id"] = f"o{posicao:03d}"
        otimizacao["prioridade"] = posicao
    return otimizacoes


def _analise_de_impacto(otimizacoes: list[dict], previsao: dict, painel: dict) -> dict:
    """O que se espera ganhar — sempre com a origem do número."""
    ganhos = [
        (o["impacto_esperado"] or {}).get("ganho_na_probabilidade")
        for o in otimizacoes
        if o["impacto_esperado"]
    ]
    medidos = [g for g in ganhos if g is not None]

    por_categoria = {}
    for otimizacao in otimizacoes:
        por_categoria.setdefault(otimizacao["categoria"], 0)
        por_categoria[otimizacao["categoria"]] += 1

    tempo = [o for o in otimizacoes if o["categoria"] in
             ("estudo_alem_do_necessario", "desperdicio_de_tempo")]
    retencao = [o for o in otimizacoes if o["categoria"] == "baixa_retencao"]
    riscos = [o for o in otimizacoes if o["gravidade"] in ("critica", "alta")]

    return {
        "ganho_na_probabilidade": {
            "estimativa": round(max(medidos), 4) if medidos else None,
            "base": (
                "maior ganho entre as alavancas já precificadas pelo agente 22; "
                "ganhos não são somados porque as alavancas se sobrepõem"
                if medidos
                else "nenhuma alavanca precificada pelo agente 22 para estas otimizações"
            ),
            "origem": "agente 22",
        },
        "reducao_no_tempo_de_estudo": {
            "oportunidades": len(tempo),
            "conteudos": [o["problema"] for o in tempo],
            "base": (
                "conteúdos dominados ou tempo acima do estimado; a redução em horas "
                "depende da reorganização do agente 06"
            ),
        },
        "aumento_da_retencao": {
            "oportunidades": len(retencao),
            "conteudos": [o["problema"] for o in retencao],
            "base": f"tópicos abaixo do limiar de retenção de {LIMIAR_DE_RETENCAO:.0%}",
        },
        "melhoria_no_desempenho": {
            "alertas_enderecados": len(
                [o for o in otimizacoes if o["categoria"] in ("gargalo", "estrategia_didatica")]
            ),
            "base": "gargalos e mudanças de estratégia atacam a causa dos erros",
        },
        "reducao_de_riscos": {
            "riscos_enderecados": len(riscos),
            "riscos_abertos_no_painel": len(painel.get("alertas", [])),
            "base": "otimizações de gravidade crítica ou alta",
        },
        "distribuicao_por_categoria": por_categoria,
    }


def _plano_de_execucao(otimizacoes: list[dict]) -> dict:
    """Ordem, dependências e como saber se funcionou."""
    metrica_por_categoria = {
        "gargalo": ("indice_de_fraqueza do tópico", "18"),
        "desperdicio_de_tempo": ("razao_tempo_real_sobre_estimado", "12"),
        "estudo_alem_do_necessario": ("horas planejadas na disciplina", "06"),
        "baixa_retencao": ("retencao_estimada do tópico", "03"),
        "cronograma": ("aderencia_aos_dias", "21"),
        "revisao": ("cobertura_das_revisoes", "15"),
        "estrategia_didatica": ("contagem_por_tipo de erro", "17"),
        "aceleracao": ("cobertura_projetada", "22"),
    }

    passos: list[dict] = []
    ja_afetados: set[str] = set()
    for otimizacao in otimizacoes:
        metrica, agente = metrica_por_categoria.get(
            otimizacao["categoria"], ("indice_geral_de_performance", "21")
        )
        # Duas otimizações que mexem no mesmo agente não são independentes: a
        # segunda precisa esperar a primeira para o efeito ser atribuível.
        dependencias = [
            outro["id"]
            for outro in passos
            if set(outro["agentes_afetados"]) & set(otimizacao["agentes_afetados"])
        ]
        passos.append(
            {
                "id": otimizacao["id"],
                "ordem": len(passos) + 1,
                "acao": otimizacao["acao"],
                "agentes_afetados": otimizacao["agentes_afetados"],
                "depende_de": dependencias,
                "criterio_de_sucesso": f"{metrica} melhora na próxima medição",
                "metrica_de_validacao": {"metrica": metrica, "medida_por": agente},
            }
        )
        ja_afetados.update(otimizacao["agentes_afetados"])

    return {
        "passos": passos,
        "agentes_envolvidos": sorted(ja_afetados),
        "base": (
            "ordem por gravidade e ganho estimado; otimizações que tocam o mesmo "
            "agente são encadeadas para o efeito ser atribuível"
        ),
    }


def _solicitacoes(otimizacoes: list[dict]) -> list[dict]:
    """O que o agente pede ao orquestrador — pedido, nunca ato."""
    return [
        {
            "id": otimizacao["id"],
            "destinatario": "Master Orchestrator",
            "agentes_a_reexecutar": otimizacao["agentes_afetados"],
            "motivo": otimizacao["problema"],
            "mudanca_solicitada": otimizacao["acao"],
            "status": "aguardando_aprovacao",
            "base": (
                "este agente não modifica nenhum outro: a alteração só acontece se o "
                "orquestrador aprovar e reexecutar os agentes"
            ),
        }
        for otimizacao in otimizacoes
    ]


# --------------------------------------------------------------------------- #
# Entrada principal
# --------------------------------------------------------------------------- #

CONSUMIDORES = ["24", "Master Orchestrator"]


def _observacoes(
    otimizacoes: list[dict], eficiencia: dict, descartados: int, previsao: dict
) -> list[str]:
    observacoes: list[str] = []

    if not otimizacoes:
        observacoes.append(
            "Nenhuma otimização proposta: nenhum detector encontrou problema com "
            "evidência medida. Ausência de proposta não é ausência de problema — é "
            "ausência de dado que o comprove."
        )
    if descartados:
        observacoes.append(
            f"{descartados} problema(s) detectado(s) sem evidência utilizável foram "
            "descartados antes de virar recomendação."
        )
    if eficiencia["valor"] is None:
        observacoes.append(f"Índice Geral de Eficiência não calculado: {eficiencia['base']}.")
    if not previsao:
        observacoes.append(
            "Sem o relatório do agente 22: os ganhos não foram precificados e este "
            "agente não estimou impacto por conta própria."
        )
    observacoes.append(
        "Nenhuma alteração foi aplicada. Toda otimização é um pedido de aprovação ao "
        "Master Orchestrator."
    )
    return observacoes


def otimizar(entradas: dict[str, Any], hoje: date | None = None) -> dict[str, Any]:
    """Constrói o Plano de Otimização."""
    hoje = hoje or date.today()

    anteriores = entradas.get("saidas_anteriores", {})
    mapa_estrategico = anteriores.get("02", {}) or {}
    mapa_conhecimento = anteriores.get("03", {}) or {}
    plano = anteriores.get("06", {}) or {}
    relatorio = anteriores.get("12", {}) or {}
    memoria = anteriores.get("14", {}) or {}
    revisoes = anteriores.get("15", {}) or {}
    relatorio_de_erros = anteriores.get("17", {}) or {}
    mapa_de_fraquezas = anteriores.get("18", {}) or {}
    habitos = anteriores.get("20", {}) or {}
    painel = anteriores.get("21", {}) or {}
    previsao = anteriores.get("22", {}) or {}

    agendadas = {
        como_texto(c.get("topico") or "")
        for s in revisoes.get("sessoes", [])
        for c in s.get("conteudos", [])
    }

    achados = [
        *_gargalos(mapa_de_fraquezas),
        *_desperdicio_de_tempo(painel, relatorio),
        *_estudo_alem_do_necessario(mapa_de_fraquezas, mapa_estrategico, plano),
        *_baixa_retencao(mapa_conhecimento, agendadas),
        *_cronograma(painel, habitos),
        *_revisao(revisoes, memoria),
        *_estrategia_didatica(relatorio_de_erros),
        *_aceleracao(mapa_de_fraquezas, previsao),
    ]
    otimizacoes = _montar(achados, previsao)
    descartados = len(achados) - len(otimizacoes)

    eficiencia = _eficiencia(
        _componentes_da_eficiencia(painel, revisoes, mapa_conhecimento)
    )
    impacto = _analise_de_impacto(otimizacoes, previsao, painel)

    return {
        "emitido_em": hoje.isoformat(),
        "resumo_geral": {
            "indice_geral_de_eficiencia": eficiencia,
            "ganho_potencial_estimado": impacto["ganho_na_probabilidade"],
            "gargalos_identificados": [
                o["problema"] for o in otimizacoes if o["categoria"] == "gargalo"
            ],
            "oportunidades_encontradas": len(otimizacoes),
            "distribuicao_por_categoria": impacto["distribuicao_por_categoria"],
        },
        "otimizacoes_recomendadas": otimizacoes,
        "analise_de_impacto": impacto,
        "plano_de_execucao": _plano_de_execucao(otimizacoes),
        "solicitacoes_de_atualizacao": _solicitacoes(otimizacoes),
        "consumido_por": CONSUMIDORES,
        "observacoes": _observacoes(otimizacoes, eficiencia, descartados, previsao),
        "lacunas": [
            nome
            for nome, presente in (
                ("painel_de_performance_do_agente_21", bool(painel)),
                ("relatorio_de_previsao_do_agente_22", bool(previsao)),
            )
            if not presente
        ],
        "confiabilidade": eficiencia["confianca"],
        "constantes_aplicadas": {
            "categorias": CATEGORIAS,
            "pesos_da_eficiencia": PESOS_DA_EFICIENCIA,
            "faixas_da_eficiencia": {nome: limite for limite, nome in FAIXAS_DA_EFICIENCIA},
            "limiar_de_retencao": LIMIAR_DE_RETENCAO,
            "limiar_de_aderencia": LIMIAR_DE_ADERENCIA,
            "minimo_de_erros_do_tipo": MINIMO_DE_ERROS_DO_TIPO,
            "peso_baixo_no_edital": PESO_BAIXO_NO_EDITAL,
            "estrategia_por_tipo_de_erro": ESTRATEGIA_POR_TIPO_DE_ERRO,
            "alavanca_por_categoria": ALAVANCA_POR_CATEGORIA,
        },
    }


__all__ = [
    "ALAVANCA_POR_CATEGORIA",
    "CATEGORIAS",
    "EFICIENCIA_MAXIMA",
    "ESTRATEGIA_POR_TIPO_DE_ERRO",
    "FAIXAS_DA_EFICIENCIA",
    "LIMIAR_DE_ADERENCIA",
    "LIMIAR_DE_RETENCAO",
    "MINIMO_DE_ERROS_DO_TIPO",
    "ORDEM_DE_PRIORIDADE",
    "PESOS_DA_EFICIENCIA",
    "PESO_BAIXO_NO_EDITAL",
    "otimizar",
]
