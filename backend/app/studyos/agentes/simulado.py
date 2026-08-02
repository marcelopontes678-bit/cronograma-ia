"""Agente 16 — Exam Simulator.

Única responsabilidade: montar simulados que meçam o nível atual. Não ensina,
não cria cronograma, não altera o Plano de Estudos.

Este agente resolve uma tensão que ficou registrada no agente 09: a spec do 16
abre a **exceção do diagnóstico** — "nunca gerar questões sobre conteúdos ainda
não estudados, *salvo em simulados diagnósticos*". É a única porta pela qual o
StudyOS avalia o que ainda não ensinou, e ela é explícita.

Duas decisões estruturais:

* **O caderno do estudante não carrega resposta.** "Nunca fornecer dicas antes
  da conclusão" só é verificável se a resposta viver em outro lugar: o caderno
  tem enunciado e alternativas, o gabarito tem resposta e critério.
* **Questão já existente é reaproveitada, não regerada.** O banco do agente 09
  tem enunciado, resposta e explicação; regerar arriscaria contradizê-lo. O
  redator só é chamado para o que falta.
"""

from __future__ import annotations

import random
from datetime import date
from typing import Any, Callable

from app.studyos.agentes.comum import como_data, como_lista, como_numero, como_texto, preenchido
from app.studyos.agentes.comum import declara_confiabilidade

# --------------------------------------------------------------------------- #
# Constantes declaradas
# --------------------------------------------------------------------------- #

FORMATOS = (
    "diagnostico",
    "parcial",
    "disciplina",
    "assunto",
    "completo",
    "revisao_final",
)

#: O único formato que pode cobrir conteúdo ainda não estudado.
FORMATO_DIAGNOSTICO = "diagnostico"

#: Quantidade padrão de questões por formato.
QUESTOES_POR_FORMATO: dict[str, int] = {
    "diagnostico": 20,
    "parcial": 30,
    "disciplina": 20,
    "assunto": 10,
    "completo": 60,
    "revisao_final": 40,
}

#: Mistura de dificuldade por formato — a soma é 1.0 e nenhum formato é
#: monocromático, porque "sempre variar os níveis de dificuldade" é regra.
MISTURA_POR_FORMATO: dict[str, dict[str, float]] = {
    "diagnostico": {"facil": 0.40, "medio": 0.40, "dificil": 0.20},
    "parcial": {"facil": 0.30, "medio": 0.50, "dificil": 0.20},
    "disciplina": {"facil": 0.30, "medio": 0.50, "dificil": 0.20},
    "assunto": {"facil": 0.30, "medio": 0.50, "dificil": 0.20},
    "completo": {"facil": 0.25, "medio": 0.50, "dificil": 0.25},
    "revisao_final": {"facil": 0.20, "medio": 0.50, "dificil": 0.30},
}

DIFICULDADES = ("facil", "medio", "dificil")

#: Minutos e peso por dificuldade da questão.
MINUTOS_POR_DIFICULDADE: dict[str, float] = {"facil": 1.5, "medio": 2.5, "dificil": 4.0}
PESO_POR_DIFICULDADE: dict[str, int] = {"facil": 1, "medio": 2, "dificil": 3}

#: Dias até a prova que caracterizam a reta final.
DIAS_PARA_RETA_FINAL = 30

#: Acerto esperado por nível de domínio medido (agente 03) — usado só para a
#: estatística prevista, nunca para escolher a resposta.
ACERTO_ESPERADO_POR_DOMINIO: dict[str, float] = {
    "avancado": 0.90,
    "intermediario": 0.70,
    "basico": 0.45,
    "nao_conhece": 0.20,
    "indeterminado": 0.35,
}

#: Semente padrão do embaralhamento — declarada para o simulado ser reproduzível.
SEMENTE_PADRAO = 20260101

#: Desconto assumido quando o estudante confirma que a banca penaliza o erro
#: mas não diz quanto: a convenção mais comum é erro anular acerto.
PENALIDADE_PADRAO = 1.0

#: Respostas que o estudante dá no lugar de um número.
AFIRMATIVOS = ("sim", "s", "true", "tem", "possui", "com penalidade", "verdadeiro")


class ConteudoNaoEstudado(Exception):
    """Simulado não diagnóstico sobre conteúdo que o estudante não estudou."""


# --------------------------------------------------------------------------- #
# Formato e escopo
# --------------------------------------------------------------------------- #


def _formato(campos: dict, mapa_conhecimento: dict, prazo: dict, hoje: date) -> dict:
    pedido = como_texto(campos.get("tipo_de_simulado") or "")
    if pedido in FORMATOS:
        return {"formato": pedido, "base": "informado pelo usuário"}

    diagnostico = (mapa_conhecimento.get("avaliacao_diagnostica") or {}).get("necessaria")
    dias = prazo.get("dias_restantes")

    if diagnostico and not _tem_medicao(mapa_conhecimento):
        return {
            "formato": FORMATO_DIAGNOSTICO,
            "base": "o agente 03 pediu avaliação diagnóstica e não há medição prática",
        }
    if dias is not None and 0 < dias <= DIAS_PARA_RETA_FINAL:
        return {
            "formato": "revisao_final",
            "base": f"{dias} dias até a prova, dentro da reta final",
        }
    if preenchido(campos.get("disciplina_alvo")):
        return {"formato": "disciplina", "base": "disciplina específica solicitada"}
    if preenchido(campos.get("assunto_alvo")):
        return {"formato": "assunto", "base": "assunto específico solicitado"}
    return {"formato": "parcial", "base": "padrão: avaliação parcial do progresso"}


def _tem_medicao(mapa_conhecimento: dict) -> bool:
    return any(
        topico.get("classificacao") != "indeterminado"
        for disciplina in mapa_conhecimento.get("disciplinas", [])
        for topico in disciplina.get("topicos", [])
    )


def _elegiveis(
    formato: str,
    mapa_conhecimento: dict,
    grafo: dict,
    relatorio: dict,
    campos: dict,
) -> tuple[list[dict], list[dict]]:
    """Tópicos que podem cair, e os que ficaram de fora com o motivo."""
    status = {
        como_texto(no["nome"]): no.get("status_curricular")
        for no in grafo.get("nos", [])
    }
    dificuldades = {
        como_texto(t["topico"]): t for t in relatorio.get("topicos", [])
    }
    disciplina_alvo = como_texto(campos.get("disciplina_alvo") or "")
    assunto_alvo = como_texto(campos.get("assunto_alvo") or "")

    elegiveis: list[dict] = []
    excluidos: list[dict] = []

    for disciplina in mapa_conhecimento.get("disciplinas", []):
        nome_disciplina = disciplina["disciplina"]
        if disciplina_alvo and como_texto(nome_disciplina) != disciplina_alvo:
            continue

        for medicao in disciplina.get("topicos", []):
            chave = como_texto(medicao["topico"])
            if assunto_alvo and chave != assunto_alvo:
                continue

            estudado = (
                status.get(chave) in ("concluido", "em_andamento")
                or medicao.get("classificacao") != "indeterminado"
            )
            if not estudado and formato != FORMATO_DIAGNOSTICO:
                excluidos.append(
                    {
                        "topico": medicao["topico"],
                        "disciplina": nome_disciplina,
                        "motivo": (
                            "conteúdo ainda não estudado; só entra em simulado "
                            "diagnóstico"
                        ),
                    }
                )
                continue

            elegiveis.append(
                {
                    "topico": medicao["topico"],
                    "disciplina": nome_disciplina,
                    "classificacao": medicao.get("classificacao", "indeterminado"),
                    "taxa_acerto": medicao.get("taxa_acerto"),
                    "estudado": estudado,
                    "dificuldade": dificuldades.get(chave, {}),
                }
            )
    return elegiveis, excluidos


def _prioridade_do_topico(
    topico: dict, pesos_por_disciplina: dict[str, float], dias_para_prova: int | None
) -> dict:
    fatores: list[str] = []
    score = 1.0

    peso = pesos_por_disciplina.get(como_texto(topico["disciplina"]))
    if peso:
        score *= 1 + peso
        fatores.append(f"peso {peso:.0%} no edital")

    indice = (topico["dificuldade"].get("dificuldade") or {}).get("indice")
    if indice is not None:
        score *= 1 + indice
        fatores.append(f"índice de dificuldade {indice:.0%}")

    erros = topico["dificuldade"].get("frequencia_de_erros", 0)
    if erros:
        score *= 1 + 0.15 * erros
        fatores.append(f"{erros} erro(s) registrado(s)")

    if dias_para_prova is not None and dias_para_prova <= DIAS_PARA_RETA_FINAL:
        score *= 1.2
        fatores.append("reta final")

    return {"score": round(score, 3), "fatores": fatores}


# --------------------------------------------------------------------------- #
# Distribuição das questões
# --------------------------------------------------------------------------- #


def _pesos_por_disciplina(mapa_estrategico: dict) -> dict[str, float]:
    disciplinas = mapa_estrategico.get("disciplinas", [])
    pesos = {
        como_texto(d["nome"]): float(d.get("questoes") or d.get("peso") or 0)
        for d in disciplinas
    }
    total = sum(pesos.values())
    if not total:
        return {}
    return {nome: valor / total for nome, valor in pesos.items()}


def _quantidade(formato: str, campos: dict, mapa_estrategico: dict) -> dict:
    explicito = como_numero(campos.get("numero_de_questoes"))
    if explicito:
        return {"total": int(explicito), "base": "informado pelo usuário"}

    if formato in ("completo", "revisao_final"):
        do_edital = sum(
            float(d.get("questoes") or 0) for d in mapa_estrategico.get("disciplinas", [])
        )
        if do_edital:
            return {
                "total": int(do_edital),
                "base": "total de questões declarado no edital",
            }
    return {
        "total": QUESTOES_POR_FORMATO[formato],
        "base": f"padrão do formato '{formato}'",
    }


def _slots(
    formato: str,
    total: int,
    elegiveis: list[dict],
    pesos: dict[str, float],
    dias_para_prova: int | None,
) -> list[dict]:
    """Um slot por questão, com disciplina, tópico e dificuldade alvo."""
    if not elegiveis or total <= 0:
        return []

    mistura = MISTURA_POR_FORMATO[formato]
    por_dificuldade: list[str] = []
    for dificuldade in DIFICULDADES:
        por_dificuldade.extend([dificuldade] * round(total * mistura[dificuldade]))
    while len(por_dificuldade) < total:
        por_dificuldade.append("medio")
    por_dificuldade = por_dificuldade[:total]

    ordenados = sorted(
        (
            {**t, "prioridade": _prioridade_do_topico(t, pesos, dias_para_prova)}
            for t in elegiveis
        ),
        key=lambda t: -t["prioridade"]["score"],
    )

    slots: list[dict] = []
    for indice, dificuldade in enumerate(por_dificuldade):
        # Rodízio pela ordem de prioridade: o mais cobrado/difícil aparece mais
        # vezes porque volta primeiro na roda.
        topico = ordenados[indice % len(ordenados)]
        slots.append(
            {
                "numero": indice + 1,
                "disciplina": topico["disciplina"],
                "topico": topico["topico"],
                "dificuldade": dificuldade,
                "peso": PESO_POR_DIFICULDADE[dificuldade],
                "minutos": MINUTOS_POR_DIFICULDADE[dificuldade],
                "competencia": _competencia(dificuldade),
                "prioridade": topico["prioridade"],
                "estudado": topico["estudado"],
                "classificacao": topico["classificacao"],
            }
        )
    return slots


def _competencia(dificuldade: str) -> str:
    return {
        "facil": "Reconhecer e aplicar o conceito direto",
        "medio": "Aplicar o conceito em situação típica da prova",
        "dificil": "Resolver caso com nuance, exceção ou múltiplos conceitos",
    }[dificuldade]


# --------------------------------------------------------------------------- #
# Banco do agente 09
# --------------------------------------------------------------------------- #


def _banco(exercicios: dict) -> dict[str, list[dict]]:
    """Questões já geradas pelo agente 09, indexadas pelo tópico da lista.

    O agente 09 gera uma lista inteira sobre um conteúdo só, e é esse conteúdo
    que o slot do simulado conhece — o `conceito_alvo` de cada questão é
    granularidade interna da aula, invisível aqui. Indexar por conceito
    deixava o banco inalcançável.
    """
    conteudo = exercicios.get("conteudo") or {}
    topico = como_texto(conteudo.get("nome") or "")
    if not topico:
        return {}

    #: o agente 09 calibra a lista inteira num nível só; reaproveitar fora dele
    #: falsearia o peso e o tempo previsto da questão no simulado.
    nivel = como_texto(exercicios.get("nivel_de_dificuldade") or "")
    gabarito = {g["numero"]: g for g in exercicios.get("gabarito", [])}
    banco: dict[str, list[dict]] = {}
    for questao in exercicios.get("exercicios", []):
        resposta = gabarito.get(questao["numero"])
        if not resposta:
            continue
        banco.setdefault(f"{topico}|{nivel}", []).append(
            {
                "enunciado": questao["enunciado"],
                "alternativas": questao.get("alternativas"),
                "resposta": resposta["resposta"],
                "explicacao": resposta.get("explicacao"),
                "origem": "banco do agente 09",
            }
        )
    return banco


# --------------------------------------------------------------------------- #
# Briefing e montagem
# --------------------------------------------------------------------------- #


def montar_briefing(entradas: dict[str, Any], hoje: date | None = None) -> dict[str, Any]:
    hoje = hoje or date.today()
    dados = entradas.get("dados_usuario", {}) or {}
    campos = {k: v for k, v in dados.items() if k != "perfil"}
    if isinstance(dados.get("perfil"), dict):
        campos = {**campos, **dados["perfil"]}

    anteriores = entradas.get("saidas_anteriores", {})
    perfil = anteriores.get("01", {}) or {}
    mapa_estrategico = anteriores.get("02", {}) or {}
    mapa_conhecimento = anteriores.get("03", {}) or {}
    grafo = anteriores.get("05", {}) or {}
    exercicios = anteriores.get("09", {}) or {}
    relatorio = anteriores.get("12", {}) or {}

    prazo = mapa_estrategico.get("prazo_final") or {}
    data_prova = como_data(campos.get("data_prova")) or como_data(prazo.get("data"))
    dias_para_prova = (data_prova - hoje).days if data_prova else None

    decisao = _formato(campos, mapa_conhecimento, prazo, hoje)
    formato = decisao["formato"]

    elegiveis, excluidos = _elegiveis(
        formato, mapa_conhecimento, grafo, relatorio, campos
    )
    if not elegiveis:
        return {
            "bloqueio": {
                "motivo": "sem_conteudo_elegivel",
                "detalhe": (
                    "Nenhum conteúdo elegível para este formato. "
                    + (
                        f"{len(excluidos)} tópico(s) fora por não terem sido estudados."
                        if excluidos
                        else "Não há tópicos mapeados."
                    )
                ),
                "acao": (
                    "Rodar um simulado diagnóstico ou estudar o conteúdo antes."
                    if excluidos
                    else "Informar o edital ou as matérias."
                ),
            },
            "formato": decisao,
            "excluidos": excluidos,
            "slots": [],
        }

    pesos = _pesos_por_disciplina(mapa_estrategico)
    quantidade = _quantidade(formato, campos, mapa_estrategico)
    slots = _slots(formato, quantidade["total"], elegiveis, pesos, dias_para_prova)

    return {
        "bloqueio": None,
        "formato": decisao,
        "objetivo": _objetivo(formato, mapa_estrategico),
        "quantidade": quantidade,
        "slots": slots,
        "banco_disponivel": _banco(exercicios),
        "elegiveis": elegiveis,
        "excluidos": excluidos,
        "banca": {
            "nome": campos.get("banca"),
            "estilo": campos.get("estilo_da_banca"),
            "instrucao": (
                f"Reproduzir o estilo da banca {campos.get('banca')}"
                if preenchido(campos.get("banca"))
                else "Nenhuma banca informada: usar linguagem padrão de prova objetiva"
            ),
        },
        "correcao": _criterios_de_correcao(campos, slots),
        "perfil_do_estudante": {
            "nivel_geral": (perfil.get("nivel_conhecimento_geral") or {}).get("estimativa"),
            "idioma": (perfil.get("perfil_academico") or {}).get("idioma"),
        },
        "semente": int(como_numero(campos.get("semente")) or SEMENTE_PADRAO),
        "dias_para_prova": dias_para_prova,
        "proibicoes": [
            "não ensinar durante o simulado (agentes 07 e 13)",
            "não fornecer dica antes da conclusão",
            "não alterar o Plano de Estudos (agente 06)",
            "não criar cronograma",
        ],
    }


def _objetivo(formato: str, mapa_estrategico: dict) -> str:
    alvo = mapa_estrategico.get("objetivo_principal") or "o objetivo do estudante"
    return {
        "diagnostico": f"Medir o ponto de partida em relação a {alvo}",
        "parcial": f"Medir o progresso parcial em relação a {alvo}",
        "disciplina": "Medir o domínio da disciplina selecionada",
        "assunto": "Medir o domínio do assunto selecionado",
        "completo": f"Reproduzir a prova completa de {alvo}",
        "revisao_final": f"Simular a prova real na reta final de {alvo}",
    }[formato]


def _penalidade(bruto: Any) -> tuple[float, str]:
    """Desconto por erro em pontos, mais a origem do número.

    O estudante costuma responder "sim" ou marcar um booleano — só sabe que a
    banca desconta, não quanto. Ler isso como zero seria transformar um
    "tem penalidade" em "não tem", então a resposta afirmativa cai no padrão
    declarado em vez de sumir.
    """
    numero = como_numero(bruto)
    if numero is not None:
        return numero, "informado pelo usuário"
    if bruto is True or como_texto(bruto) in AFIRMATIVOS:
        return PENALIDADE_PADRAO, "usuário confirmou que há desconto, sem informar o valor"
    return 0.0, "nenhum desconto informado"


def _criterios_de_correcao(campos: dict, slots: list[dict]) -> dict:
    penalidade, origem = _penalidade(campos.get("penalidade_por_erro"))
    return {
        "pontuacao_maxima": sum(s["peso"] for s in slots),
        "peso_por_dificuldade": PESO_POR_DIFICULDADE,
        "penalidade_por_erro": penalidade,
        "origem_da_penalidade": origem,
        "regra": (
            f"Cada erro desconta {penalidade} ponto(s)"
            if penalidade
            else "Sem desconto por erro; questão em branco vale zero"
        ),
        "nota_de_corte": como_numero(campos.get("nota_corte")),
    }


def montar(
    briefing: dict[str, Any], questoes: dict[Any, Any] | None = None
) -> dict[str, Any]:
    """Monta o simulado — separando caderno e gabarito."""
    bloqueio = briefing.get("bloqueio")
    if bloqueio and questoes:
        raise ConteudoNaoEstudado(bloqueio["detalhe"])

    if bloqueio:
        return {
            "gerado": False,
            "bloqueio": bloqueio,
            "status": "bloqueado",
            "resumo_geral": None,
            "caderno_de_questoes": [],
            "questoes": [],
            "gabarito": [],
            "briefing": None,
            "consumido_por": CONSUMIDORES,
            "observacoes": [f"Simulado não gerado: {bloqueio['detalhe']}"],
            "lacunas": ["conteudo_elegivel"],
        }

    redigidas = _por_numero(questoes or {})
    banco = dict(briefing["banco_disponivel"])
    usados: set[str] = set()

    montadas: list[dict] = []
    pendentes: list[int] = []
    invalidas: list[dict] = []

    for slot in briefing["slots"]:
        bruta = redigidas.get(slot["numero"]) or _do_banco(banco, slot, usados)
        if not preenchido(bruta):
            pendentes.append(slot["numero"])
            continue

        problema = _validar(bruta)
        if problema:
            invalidas.append({"numero": slot["numero"], "motivo": problema})
            continue

        montadas.append({**slot, **bruta, "id": f"q{slot['numero']:03d}"})

    embaralhadas = _embaralhar(montadas, briefing["semente"])
    completo = bool(embaralhadas) and not pendentes and not invalidas

    return {
        "gerado": completo,
        "bloqueio": None,
        "resumo_geral": _resumo(briefing, embaralhadas),
        "caderno_de_questoes": [
            {
                "id": q["id"],
                "numero": indice + 1,
                "disciplina": q["disciplina"],
                "topico": q["topico"],
                "grau_de_dificuldade": q["dificuldade"],
                "enunciado": q["enunciado"],
                "alternativas": q.get("alternativas"),
                "peso": q["peso"],
            }
            for indice, q in enumerate(embaralhadas)
        ],
        "questoes": [
            {
                "id": q["id"],
                "disciplina": q["disciplina"],
                "topico": q["topico"],
                "grau_de_dificuldade": q["dificuldade"],
                "competencia_avaliada": q["competencia"],
                "peso": q["peso"],
                "minutos_previstos": q["minutos"],
                "origem": q.get("origem", "redator"),
                "conteudo_estudado": q["estudado"],
                "prioridade": q["prioridade"],
            }
            for q in embaralhadas
        ],
        "gabarito": [
            {
                "id": q["id"],
                "resposta_correta": q["resposta"],
                "explicacao": q.get("explicacao"),
                "competencia_avaliada": q["competencia"],
                "peso": q["peso"],
            }
            for q in embaralhadas
        ],
        "criterios_de_correcao": {
            **briefing["correcao"],
            "pontuacao_maxima": sum(q["peso"] for q in embaralhadas),
        },
        "estatisticas_previstas": _estatisticas(embaralhadas),
        "registro_para_analise": {
            "destinatarios": ["17", "18", "21"],
            "por_questao": [
                {
                    "id": q["id"],
                    "topico": q["topico"],
                    "disciplina": q["disciplina"],
                    "dificuldade": q["dificuldade"],
                    "competencia": q["competencia"],
                    "dominio_medido": q["classificacao"],
                    "peso": q["peso"],
                }
                for q in embaralhadas
            ],
        },
        "questoes_pendentes": pendentes,
        "questoes_invalidas": invalidas,
        "conteudos_excluidos": briefing["excluidos"],
        "status": "gerado" if completo else "pendente_de_redacao",
        "briefing": briefing,
        "consumido_por": CONSUMIDORES,
        "observacoes": _observacoes(briefing, pendentes, invalidas, embaralhadas),
        "constantes_aplicadas": {
            "questoes_por_formato": QUESTOES_POR_FORMATO,
            "mistura_por_formato": MISTURA_POR_FORMATO,
            "minutos_por_dificuldade": MINUTOS_POR_DIFICULDADE,
            "peso_por_dificuldade": PESO_POR_DIFICULDADE,
            "acerto_esperado_por_dominio": ACERTO_ESPERADO_POR_DOMINIO,
            "dias_para_reta_final": DIAS_PARA_RETA_FINAL,
            "penalidade_padrao": PENALIDADE_PADRAO,
            "semente_padrao": SEMENTE_PADRAO,
        },
        "lacunas": [],
    }


def _do_banco(banco: dict[str, list[dict]], slot: dict, usados: set[str]) -> dict | None:
    """Reaproveita questão do agente 09 antes de pedir uma nova.

    Só serve o slot cujo tópico e grau de dificuldade batem com a lista de
    origem: questão fácil ocupando slot difícil quebraria peso e tempo.
    """
    chave = f"{como_texto(slot['topico'])}|{como_texto(slot['dificuldade'])}"
    for questao in banco.get(chave, []):
        marca = como_texto(questao["enunciado"])
        if marca not in usados:
            usados.add(marca)
            return dict(questao)
    return None


def _por_numero(questoes: dict) -> dict[int, dict]:
    normalizadas: dict[int, dict] = {}
    for chave, valor in questoes.items():
        try:
            numero = int(chave)
        except (TypeError, ValueError):
            continue
        if isinstance(valor, dict):
            normalizadas[numero] = valor
    return normalizadas


def _validar(questao: dict) -> str | None:
    if not preenchido(questao.get("enunciado")):
        return "sem enunciado"
    if not preenchido(questao.get("resposta")):
        return "sem resposta correta"
    return None


def _embaralhar(questoes: list[dict], semente: int) -> list[dict]:
    """Embaralha questões e alternativas — com semente, para ser reproduzível."""
    sorteador = random.Random(semente)
    embaralhadas = list(questoes)
    sorteador.shuffle(embaralhadas)

    resultado: list[dict] = []
    for questao in embaralhadas:
        alternativas = questao.get("alternativas")
        if isinstance(alternativas, (list, tuple)) and len(alternativas) > 1:
            baralhadas = list(alternativas)
            sorteador.shuffle(baralhadas)
            questao = {**questao, "alternativas": baralhadas}
        resultado.append(questao)
    return resultado


def _resumo(briefing: dict, questoes: list[dict]) -> dict:
    por_disciplina: dict[str, int] = {}
    por_dificuldade: dict[str, int] = {}
    for questao in questoes:
        por_disciplina[questao["disciplina"]] = por_disciplina.get(questao["disciplina"], 0) + 1
        por_dificuldade[questao["dificuldade"]] = (
            por_dificuldade.get(questao["dificuldade"], 0) + 1
        )

    return {
        "tipo_de_simulado": briefing["formato"]["formato"],
        "base_do_formato": briefing["formato"]["base"],
        "objetivo": briefing["objetivo"],
        "numero_de_questoes": len(questoes),
        "tempo_previsto_min": round(sum(q["minutos"] for q in questoes), 1),
        "distribuicao_por_disciplina": por_disciplina,
        "distribuicao_por_dificuldade": por_dificuldade,
        "banca": briefing["banca"]["nome"],
        "semente_do_embaralhamento": briefing["semente"],
    }


def _estatisticas(questoes: list[dict]) -> dict:
    """Projeção de desempenho a partir do domínio medido — não é gabarito."""
    if not questoes:
        return {"acerto_previsto": None, "base": "sem questões"}

    esperado = sum(
        ACERTO_ESPERADO_POR_DOMINIO.get(q["classificacao"], 0.35) * q["peso"]
        for q in questoes
    )
    total = sum(q["peso"] for q in questoes)
    return {
        "acerto_previsto": round(esperado / total, 4) if total else None,
        "pontuacao_prevista": round(esperado, 2),
        "pontuacao_maxima": total,
        "base": (
            "domínio medido pelo agente 03 por tópico; projeção para os agentes "
            "21 e 22 comparar com o resultado real"
        ),
        "confianca": (
            "baixa"
            if all(q["classificacao"] == "indeterminado" for q in questoes)
            else "media"
        ),
    }


CONSUMIDORES = ["17", "18", "19", "21", "22", "23", "24"]


def _observacoes(
    briefing: dict, pendentes: list[int], invalidas: list[dict], questoes: list[dict]
) -> list[str]:
    observacoes: list[str] = []
    formato = briefing["formato"]["formato"]

    if formato == FORMATO_DIAGNOSTICO:
        nao_estudados = [q["topico"] for q in questoes if not q["estudado"]]
        if nao_estudados:
            observacoes.append(
                f"Simulado diagnóstico: {len(nao_estudados)} tópico(s) ainda não "
                "estudado(s) entraram, exceção prevista na spec deste agente."
            )
    if briefing["excluidos"]:
        observacoes.append(
            f"{len(briefing['excluidos'])} tópico(s) fora do simulado por não "
            "terem sido estudados."
        )
    reaproveitadas = sum(1 for q in questoes if q.get("origem") == "banco do agente 09")
    if reaproveitadas:
        observacoes.append(
            f"{reaproveitadas} questão(ões) reaproveitada(s) do banco do agente 09 "
            "em vez de regeradas."
        )
    if pendentes:
        observacoes.append(
            f"{len(pendentes)} questão(ões) sem enunciado. O banco do agente 09 não "
            "cobriu tudo e não há redator conectado."
        )
    if invalidas:
        observacoes.append(
            f"{len(invalidas)} questão(ões) recusada(s): "
            + ", ".join(f"#{i['numero']} ({i['motivo']})" for i in invalidas)
        )
    observacoes.append(
        "O caderno do estudante não contém respostas: gabarito e explicações "
        "ficam em blocos separados, para não entregar dica antes da conclusão."
    )
    return observacoes


# --------------------------------------------------------------------------- #
# Entrada principal
# --------------------------------------------------------------------------- #


@declara_confiabilidade
def gerar(
    entradas: dict[str, Any],
    redator: Callable[[dict], dict] | None = None,
    hoje: date | None = None,
) -> dict[str, Any]:
    """Gera o simulado do formato adequado ao momento do estudante."""
    briefing = montar_briefing(entradas, hoje=hoje)
    if briefing.get("bloqueio") or redator is None:
        return montar(briefing)
    return montar(briefing, redator(briefing))


__all__ = [
    "FORMATOS",
    "FORMATO_DIAGNOSTICO",
    "MISTURA_POR_FORMATO",
    "PENALIDADE_PADRAO",
    "PESO_POR_DIFICULDADE",
    "QUESTOES_POR_FORMATO",
    "ConteudoNaoEstudado",
    "gerar",
    "montar",
    "montar_briefing",
]
