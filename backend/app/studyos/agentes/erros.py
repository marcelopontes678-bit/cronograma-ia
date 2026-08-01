"""Agente 17 — Error Analyzer.

Única responsabilidade: transformar erro em inteligência. Não ensina, não gera
exercício, não mexe no Plano de Estudos nem no Grafo de Dependências.

A regra que define este agente é **"nunca assumir a causa de um erro sem
evidências"**. Ela só é verificável se a causa for derivada de sinais
declarados, então aqui a classificação não é um palpite sobre o erro: é o
resultado de regras ordenadas, cada uma com a evidência que a disparou. Erro
que não casa com nenhuma regra sai como ``indeterminado`` — com a lista do que
faltou para determiná-lo — em vez de receber um tipo plausível.

Duas consequências disso:

* **Sinal contraditório não é descartado.** Se o estudante declara "foi
  desatenção" mas o domínio medido no tópico é `nao_conhece`, os dois entram:
  a declaração vira a causa (é evidência direta) e a contradição fica
  registrada, para o agente 18 decidir com o quadro inteiro.
* **Ausência de erro não é erro resolvido.** Um par tópico+tipo que sumiu do
  relatório só conta como resolvido se houve prática nova no tópico depois.
  Sem prática nova, ele fica em `sem_nova_evidencia`.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from app.studyos.agentes.comum import (
    como_data,
    como_lista_de_dicts,
    como_numero,
    como_texto,
    preenchido,
)
from app.studyos.agentes.dificuldade import TIPO_DO_AGENTE_17

# --------------------------------------------------------------------------- #
# Constantes declaradas
# --------------------------------------------------------------------------- #

TIPOS_DE_ERRO = (
    "conceitual",
    "interpretacao",
    "calculo",
    "memorizacao",
    "atencao",
    "estrategia",
    "gestao_do_tempo",
)

#: Categoria da questão (taxonomia do agente 09) → tipo de erro que ela revela.
#: É a evidência mais fraca da escala: diz o que a questão cobrava, não o que
#: falhou na cabeça do estudante.
TIPO_POR_CATEGORIA: dict[str, str] = {
    "fixacao": "memorizacao",
    "compreensao": "conceitual",
    "aplicacao": "calculo",
    "analise": "interpretacao",
    "sintese": "conceitual",
    "desafio": "estrategia",
}

#: Tradução para o vocabulário de dificuldade do agente 12. A tabela mora lá
#: porque é lá que ela é aplicada — aqui só se declara qual foi usada, para os
#: dois agentes nunca discordarem sobre o que um erro significa.
EQUIVALENCIA_NO_AGENTE_12 = TIPO_DO_AGENTE_17

#: Classificações do agente 03 que caracterizam conteúdo não dominado.
DOMINIO_INSUFICIENTE = ("nao_conhece", "basico")

#: Acerto histórico a partir do qual um erro isolado no tópico vira sinal de
#: atenção, e não de desconhecimento.
LIMIAR_ACERTO_ALTO = 0.80

#: Quanto o tempo gasto precisa passar do previsto para virar evidência.
FATOR_TEMPO_EXCESSIVO = 2.0

#: Ocorrências do mesmo par tópico+tipo a partir das quais o erro é recorrente.
MINIMO_PARA_RECORRENCIA = 2

#: Respostas mínimas em cada janela para declarar tendência. Abaixo disso a
#: variação é ruído, e "melhorou" seria invenção.
MINIMO_PARA_TENDENCIA = 10

#: Faixas do score de gravidade.
FAIXAS_DE_GRAVIDADE: tuple[tuple[float, str], ...] = (
    (1.5, "baixa"),
    (2.5, "media"),
    (4.0, "alta"),
)

#: Intervenção sugerida por tipo de erro, com o agente responsável. Sugestão,
#: não execução: este agente não altera plano nem cria material.
INTERVENCAO_POR_TIPO: dict[str, dict[str, str]] = {
    "conceitual": {
        "intervencao": "reestudar o conceito antes de resolver mais questões",
        "agente_responsavel": "07",
    },
    "interpretacao": {
        "intervencao": "praticar leitura do enunciado com questões comentadas",
        "agente_responsavel": "09",
    },
    "calculo": {
        "intervencao": "refazer os passos do procedimento com exemplos resolvidos",
        "agente_responsavel": "08",
    },
    "memorizacao": {
        "intervencao": "reforçar com flashcards e antecipar a revisão",
        "agente_responsavel": "10",
    },
    "atencao": {
        "intervencao": "revisar a resposta antes de fechar a questão; conferir o que foi pedido",
        "agente_responsavel": "19",
    },
    "estrategia": {
        "intervencao": "definir ordem de resolução e critério de abandono da questão",
        "agente_responsavel": "19",
    },
    "gestao_do_tempo": {
        "intervencao": "treinar com cronômetro por questão antes do próximo simulado",
        "agente_responsavel": "16",
    },
}


# --------------------------------------------------------------------------- #
# Coleta dos erros
# --------------------------------------------------------------------------- #


def _respostas(campos: dict) -> dict[str, dict]:
    """Respostas do estudante indexadas pelo id/número da questão."""
    brutas: list[dict] = []
    for chave in ("respostas", "respostas_simulado", "gabarito_do_estudante"):
        brutas.extend(como_lista_de_dicts(campos.get(chave)))

    indexadas: dict[str, dict] = {}
    for bruta in brutas:
        identificador = bruta.get("id") or bruta.get("questao") or bruta.get("numero")
        if not preenchido(identificador):
            continue
        indexadas[como_texto(identificador)] = bruta
    return indexadas


def _erros_do_simulado(simulado: dict, respostas: dict[str, dict]) -> list[dict]:
    """Erros medidos: resposta do estudante contra o gabarito do agente 16.

    É a evidência mais forte que o sistema produz — o erro não é relatado, é
    observado. Sem respostas registradas não há erro medido, e o agente diz
    isso em vez de deduzir erro da taxa de acerto.
    """
    if not respostas:
        return []

    gabarito = {como_texto(g["id"]): g for g in simulado.get("gabarito", [])}
    registro = {
        como_texto(q["id"]): q
        for q in (simulado.get("registro_para_analise") or {}).get("por_questao", [])
    }
    previsto = {
        como_texto(q["id"]): q.get("minutos_previstos")
        for q in simulado.get("questoes", [])
    }

    erros: list[dict] = []
    for identificador, oficial in gabarito.items():
        dada = respostas.get(identificador)
        if dada is None:
            continue

        marcada = dada.get("resposta")
        em_branco = not preenchido(marcada)
        if not em_branco and como_texto(marcada) == como_texto(oficial["resposta_correta"]):
            continue

        contexto = registro.get(identificador, {})
        erros.append(
            {
                "questao": identificador,
                "topico": contexto.get("topico"),
                "disciplina": contexto.get("disciplina"),
                "dificuldade_da_questao": contexto.get("dificuldade"),
                "competencia": contexto.get("competencia"),
                "categoria": dada.get("categoria"),
                "peso": contexto.get("peso") or 1,
                "em_branco": em_branco,
                "minutos_gastos": como_numero(dada.get("tempo_min")),
                "minutos_previstos": previsto.get(identificador),
                "tipo_declarado": dada.get("tipo") or dada.get("motivo"),
                "data": como_data(dada.get("data")),
                "origem": "resposta conferida contra o gabarito do agente 16",
            }
        )
    return erros


def _erros_declarados(campos: dict) -> list[dict]:
    """Erros que o estudante registrou fora do simulado."""
    erros: list[dict] = []
    for bruto in como_lista_de_dicts(campos.get("erros")):
        erros.append(
            {
                "questao": bruto.get("questao") or bruto.get("numero"),
                "topico": bruto.get("topico") or bruto.get("conteudo"),
                "disciplina": bruto.get("disciplina"),
                "dificuldade_da_questao": bruto.get("dificuldade"),
                "competencia": None,
                "categoria": bruto.get("categoria"),
                "peso": como_numero(bruto.get("peso")) or 1,
                "em_branco": bool(bruto.get("em_branco")),
                "minutos_gastos": como_numero(bruto.get("tempo_min")),
                "minutos_previstos": None,
                "tipo_declarado": bruto.get("tipo") or bruto.get("motivo"),
                "data": como_data(bruto.get("data")),
                "origem": "erro registrado pelo estudante",
            }
        )
    return erros


# --------------------------------------------------------------------------- #
# Contexto: o que se sabe de cada tópico
# --------------------------------------------------------------------------- #


def _contexto_por_topico(
    mapa_conhecimento: dict, relatorio: dict, grafo: dict
) -> dict[str, dict]:
    """Domínio medido, esquecimento e posição no grafo, por tópico."""
    contexto: dict[str, dict] = {}

    for disciplina in mapa_conhecimento.get("disciplinas", []):
        for medicao in disciplina.get("topicos", []):
            contexto[como_texto(medicao["topico"])] = {
                "topico": medicao["topico"],
                "disciplina": disciplina["disciplina"],
                "classificacao": medicao.get("classificacao", "indeterminado"),
                "taxa_acerto": medicao.get("taxa_acerto"),
                "amostra": medicao.get("amostra"),
                "esquecido": bool(medicao.get("esquecido")),
                "retencao": medicao.get("retencao_estimada"),
            }

    for topico in relatorio.get("topicos", []):
        registro = contexto.setdefault(
            como_texto(topico["topico"]),
            {"topico": topico["topico"], "disciplina": topico.get("disciplina")},
        )
        registro.update(
            {
                "indice_de_dificuldade": (topico.get("dificuldade") or {}).get("indice"),
                "frequencia_de_erros": topico.get("frequencia_de_erros", 0),
                "esquecido": bool(topico.get("esquecido")) or registro.get("esquecido", False),
            }
        )
        if registro.get("taxa_acerto") is None:
            registro["taxa_acerto"] = topico.get("taxa_de_acertos")

    for no in grafo.get("nos", []):
        registro = contexto.get(como_texto(no["nome"]))
        if registro is None:
            continue
        registro["pre_requisitos"] = no.get("pre_requisitos_nomes") or []
        registro["conteudos_bloqueados"] = no.get("dependentes_transitivos", 0)

    return contexto


def _pre_requisito_fraco(registro: dict, contexto: dict[str, dict]) -> str | None:
    """Nome do pré-requisito cujo domínio medido é insuficiente, se houver."""
    for nome in registro.get("pre_requisitos", []):
        anterior = contexto.get(como_texto(nome))
        if anterior and anterior.get("classificacao") in DOMINIO_INSUFICIENTE:
            return anterior["topico"]
    return None


# --------------------------------------------------------------------------- #
# Classificação: cada tipo precisa de uma evidência
# --------------------------------------------------------------------------- #


def _sinais(erro: dict, contexto: dict[str, dict]) -> list[dict]:
    """Todos os sinais que o erro dispara, em ordem de força da evidência."""
    registro = contexto.get(como_texto(erro.get("topico") or ""), {})
    sinais: list[dict] = []

    declarado = como_texto(erro.get("tipo_declarado") or "")
    if declarado in TIPOS_DE_ERRO:
        sinais.append(
            {
                "tipo": declarado,
                "causa": f"o estudante identificou o erro como {declarado}",
                "evidencia": "tipo informado pelo próprio estudante",
                "forca": "declarada",
            }
        )

    if erro.get("em_branco"):
        sinais.append(
            {
                "tipo": "gestao_do_tempo",
                "causa": "questão não respondida",
                "evidencia": "questão deixada em branco",
                "forca": "medida",
            }
        )

    gastos, previstos = erro.get("minutos_gastos"), erro.get("minutos_previstos")
    if gastos and previstos and gastos > previstos * FATOR_TEMPO_EXCESSIVO:
        sinais.append(
            {
                "tipo": "gestao_do_tempo",
                "causa": "tempo na questão muito acima do previsto",
                "evidencia": (
                    f"{gastos:g} min gastos contra {previstos:g} min previstos "
                    f"(limite: {FATOR_TEMPO_EXCESSIVO:g}×)"
                ),
                "forca": "medida",
            }
        )

    faltante = _pre_requisito_fraco(registro, contexto)
    if faltante:
        sinais.append(
            {
                "tipo": "conceitual",
                "causa": f"pré-requisito não dominado: {faltante}",
                "evidencia": (
                    f"o grafo do agente 05 põe {faltante} antes deste tópico, e o "
                    "agente 03 mediu domínio insuficiente nele"
                ),
                "forca": "medida",
            }
        )

    if registro.get("classificacao") in DOMINIO_INSUFICIENTE:
        sinais.append(
            {
                "tipo": "conceitual",
                "causa": "domínio insuficiente do próprio conteúdo",
                "evidencia": (
                    f"agente 03 classificou o tópico como "
                    f"{registro['classificacao']}"
                ),
                "forca": "medida",
            }
        )

    if registro.get("esquecido"):
        sinais.append(
            {
                "tipo": "memorizacao",
                "causa": "conteúdo estudado e não retido",
                "evidencia": "tópico marcado como esquecido pelos agentes 03/12",
                "forca": "medida",
            }
        )

    taxa = registro.get("taxa_acerto")
    if taxa is not None and taxa >= LIMIAR_ACERTO_ALTO:
        sinais.append(
            {
                "tipo": "atencao",
                "causa": "erro isolado em tópico de acerto alto",
                "evidencia": (
                    f"{taxa:.0%} de acerto histórico no tópico "
                    f"(limite: {LIMIAR_ACERTO_ALTO:.0%})"
                ),
                "forca": "medida",
            }
        )

    inferido = TIPO_POR_CATEGORIA.get(como_texto(erro.get("categoria") or ""))
    if inferido:
        sinais.append(
            {
                "tipo": inferido,
                "causa": f"a questão cobrava {erro['categoria']}",
                "evidencia": "categoria da questão na taxonomia do agente 09",
                "forca": "inferida",
            }
        )

    return sinais


def _classificar(erro: dict, contexto: dict[str, dict]) -> dict:
    """Tipo, causa e evidências — ou `indeterminado` e o que falta para saber."""
    sinais = _sinais(erro, contexto)
    if not sinais:
        return {
            "tipo": "indeterminado",
            "causa_provavel": None,
            "evidencias": [],
            "contradicoes": [],
            "falta_para_determinar": [
                "tipo do erro declarado pelo estudante",
                "tempo gasto na questão",
                "domínio medido no tópico (agente 03)",
                "categoria da questão (agente 09)",
            ],
        }

    escolhido = sinais[0]
    return {
        "tipo": escolhido["tipo"],
        "causa_provavel": escolhido["causa"],
        "evidencias": [
            {"evidencia": s["evidencia"], "aponta_para": s["tipo"], "forca": s["forca"]}
            for s in sinais
        ],
        "contradicoes": [
            f"{s['evidencia']} aponta para {s['tipo']}"
            for s in sinais[1:]
            if s["tipo"] != escolhido["tipo"]
        ],
        "falta_para_determinar": [],
    }


# --------------------------------------------------------------------------- #
# Frequência, gravidade e impacto
# --------------------------------------------------------------------------- #


def _chave(erro: dict) -> str:
    return f"{como_texto(erro.get('topico') or 'sem topico')}|{erro['tipo']}"


def _gravidade(
    erro: dict, frequencia: int, pesos: dict[str, float], contexto: dict[str, dict],
    regressao: bool,
) -> dict:
    """Score explicado — cada multiplicador entra com o fator que o justifica."""
    fatores: list[str] = []
    score = 1.0

    if frequencia >= MINIMO_PARA_RECORRENCIA:
        score *= 1 + 0.3 * (frequencia - 1)
        fatores.append(f"{frequencia} ocorrências do mesmo tipo no tópico")

    peso = pesos.get(como_texto(erro.get("disciplina") or ""))
    if peso:
        score *= 1 + peso
        fatores.append(f"disciplina com {peso:.0%} do edital")

    registro = contexto.get(como_texto(erro.get("topico") or ""), {})
    bloqueados = registro.get("conteudos_bloqueados", 0)
    if bloqueados:
        score *= 1 + 0.1 * bloqueados
        fatores.append(f"tópico é pré-requisito de {bloqueados} conteúdo(s)")

    if regressao:
        score *= 1.4
        fatores.append("erro já considerado resolvido voltou a ocorrer")

    score = round(score, 3)
    nivel = "critica"
    for limite, nome in FAIXAS_DE_GRAVIDADE:
        if score < limite:
            nivel = nome
            break
    return {"nivel": nivel, "score": score, "fatores": fatores}


def _pesos_por_disciplina(mapa_estrategico: dict) -> dict[str, float]:
    pesos = {
        como_texto(d["nome"]): float(d.get("questoes") or d.get("peso") or 0)
        for d in mapa_estrategico.get("disciplinas", [])
    }
    total = sum(pesos.values())
    return {nome: valor / total for nome, valor in pesos.items()} if total else {}


def _impacto(erro: dict, pontos_totais: float) -> dict:
    """Fração da pontuação que este erro custou, quando há pontuação."""
    if not pontos_totais:
        return {
            "pontos_perdidos": None,
            "fracao_da_pontuacao": None,
            "base": "nenhuma pontuação registrada; impacto não calculado",
        }
    perdidos = float(erro.get("peso") or 1)
    return {
        "pontos_perdidos": perdidos,
        "fracao_da_pontuacao": round(perdidos / pontos_totais, 4),
        "base": f"peso da questão sobre {pontos_totais:g} pontos do simulado",
    }


# --------------------------------------------------------------------------- #
# Evolução e indicadores
# --------------------------------------------------------------------------- #


def _historico(campos: dict) -> list[dict]:
    """Respostas agregadas ao longo do tempo, para medir evolução."""
    registros: list[dict] = []
    for chave in ("historico_respostas", "resultados_exercicios", "historico"):
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
                        "erros": total - acertos,
                    }
                )
    return sorted(registros, key=lambda r: r["data"])


def _evolucao(historico: list[dict]) -> dict:
    """Taxa de erro da janela inicial contra a recente, separadas **por data**.

    O corte é temporal, nunca por posição na lista: registros do mesmo dia
    descrevem o mesmo momento do estudante, e dividi-los em "antes" e "depois"
    compararia tópicos diferentes fingindo comparar épocas diferentes.
    """
    indeterminada = {
        "disponivel": False,
        "tendencia": "indeterminada",
        "taxa_inicial": None,
        "taxa_recente": None,
    }
    total = sum(r["total"] for r in historico)
    if total < MINIMO_PARA_TENDENCIA * 2:
        return {
            **indeterminada,
            "base": (
                f"{int(total)} resposta(s) registradas; são necessárias "
                f"{MINIMO_PARA_TENDENCIA * 2} para comparar duas janelas"
            ),
        }

    datas = sorted({r["data"] for r in historico})
    if len(datas) < 2:
        return {
            **indeterminada,
            "base": (
                "todo o histórico tem a mesma data; não há duas épocas para comparar"
            ),
        }

    #: primeira data que deixa metade do volume para trás e ainda sobra amostra
    #: suficiente dos dois lados.
    corte = None
    for data in datas[:-1]:
        anteriores = sum(r["total"] for r in historico if r["data"] <= data)
        if anteriores >= total / 2 or anteriores >= MINIMO_PARA_TENDENCIA:
            if total - anteriores >= MINIMO_PARA_TENDENCIA:
                corte = data
                break

    if corte is None:
        return {
            **indeterminada,
            "base": (
                f"nenhum corte temporal deixa {MINIMO_PARA_TENDENCIA} respostas "
                "de cada lado"
            ),
        }

    inicio = [r for r in historico if r["data"] <= corte]
    recente = [r for r in historico if r["data"] > corte]

    taxa_inicial = sum(r["erros"] for r in inicio) / sum(r["total"] for r in inicio)
    taxa_recente = sum(r["erros"] for r in recente) / sum(r["total"] for r in recente)
    variacao = taxa_recente - taxa_inicial
    return {
        "disponivel": True,
        "tendencia": (
            "melhora" if variacao <= -0.05
            else "piora" if variacao >= 0.05
            else "estavel"
        ),
        "taxa_inicial": round(taxa_inicial, 4),
        "taxa_recente": round(taxa_recente, 4),
        "variacao": round(variacao, 4),
        "corte": corte.isoformat(),
        "base": (
            f"{int(sum(r['total'] for r in inicio))} respostas até {corte.isoformat()} "
            f"contra {int(sum(r['total'] for r in recente))} depois"
        ),
    }


def _praticados_depois(historico: list[dict], desde: date | None) -> set[str]:
    """Tópicos com prática registrada depois do relatório anterior."""
    return {
        como_texto(r["topico"])
        for r in historico
        if preenchido(r.get("topico")) and (desde is None or r["data"] > desde)
    }


def _indicadores(
    erros: list[dict], anterior: dict, historico: list[dict]
) -> dict:
    """Recorrentes, resolvidos, novos — e o que não dá para afirmar."""
    atuais = {f"{como_texto(e['topico'] or '')}|{e['tipo']}": e for e in erros}
    anteriores = {
        f"{como_texto(e.get('topico') or '')}|{como_texto(e.get('tipo') or '')}": e
        for e in anterior.get("erros", [])
    }
    emitido_em = como_data(anterior.get("emitido_em"))
    praticados = _praticados_depois(historico, emitido_em)

    resolvidos: list[dict] = []
    sem_evidencia: list[dict] = []
    for chave, erro in anteriores.items():
        if chave in atuais:
            continue
        alvo = resolvidos if como_texto(erro.get("topico") or "") in praticados else sem_evidencia
        alvo.append(
            {
                "topico": erro.get("topico"),
                "tipo": erro.get("tipo"),
                "base": (
                    "não reapareceu e houve prática nova no tópico"
                    if alvo is resolvidos
                    else "não reapareceu, mas não houve prática nova no tópico"
                ),
            }
        )

    # Um padrão recorrente é uma linha, não uma linha por ocorrência: as três
    # questões de Conjuntos erradas pelo mesmo motivo são um problema só.
    recorrentes = {
        chave: {
            "topico": erro["topico"],
            "tipo": erro["tipo"],
            "frequencia": erro["frequencia"],
            "gravidade": erro["gravidade"]["nivel"],
            "questoes": [
                e["questao"] for e in erros
                if f"{como_texto(e['topico'] or '')}|{e['tipo']}" == chave and e["questao"]
            ],
        }
        for chave, erro in atuais.items()
        if erro["frequencia"] >= MINIMO_PARA_RECORRENCIA
    }

    return {
        "erros_recorrentes": sorted(
            recorrentes.values(), key=lambda r: -r["frequencia"]
        ),
        "erros_resolvidos": resolvidos,
        "sem_nova_evidencia": sem_evidencia,
        "novos_erros": [
            {"topico": e["topico"], "tipo": e["tipo"]}
            for chave, e in atuais.items()
            if anteriores and chave not in anteriores
        ],
        "base_da_comparacao": (
            f"relatório anterior de {anterior.get('emitido_em')}"
            if anteriores
            else "nenhum relatório anterior informado"
        ),
    }


def _recomendacoes(erros: list[dict], revisoes: dict) -> list[dict]:
    """Uma recomendação por tipo predominante, da maior gravidade para a menor."""
    agendados = {
        como_texto(conteudo.get("topico") or "")
        for sessao in revisoes.get("sessoes", [])
        for conteudo in sessao.get("conteudos", [])
    }

    por_tipo: dict[str, list[dict]] = {}
    for erro in erros:
        if erro["tipo"] in INTERVENCAO_POR_TIPO:
            por_tipo.setdefault(erro["tipo"], []).append(erro)

    recomendacoes: list[dict] = []
    for tipo, do_tipo in por_tipo.items():
        alvo = max(do_tipo, key=lambda e: e["gravidade"]["score"])
        recomendacoes.append(
            {
                "tipo_de_erro": tipo,
                "ocorrencias": len(do_tipo),
                "conteudo_prioritario": alvo["topico"],
                **INTERVENCAO_POR_TIPO[tipo],
                "ja_agendado_para_revisao": como_texto(alvo["topico"] or "") in agendados,
                "gravidade_maxima": alvo["gravidade"]["nivel"],
                "score": alvo["gravidade"]["score"],
            }
        )
    return sorted(recomendacoes, key=lambda r: (-r["score"], -r["ocorrencias"]))


# --------------------------------------------------------------------------- #
# Entrada principal
# --------------------------------------------------------------------------- #

CONSUMIDORES = ["12", "18", "19", "21", "22", "23", "24"]


def _observacoes(
    erros: list[dict], medidos: int, declarados: int, evolucao: dict, respostas: dict
) -> list[str]:
    observacoes: list[str] = []

    if not erros:
        observacoes.append(
            "Nenhum erro registrado: sem respostas conferidas contra gabarito e sem "
            "erro informado pelo estudante. O relatório não deduz erro de taxa de acerto."
        )
        return observacoes

    indeterminados = [e for e in erros if e["tipo"] == "indeterminado"]
    if indeterminados:
        observacoes.append(
            f"{len(indeterminados)} erro(s) sem causa determinável: nenhuma evidência "
            "disponível apontou um tipo, e a causa não foi presumida."
        )
    contraditorios = [e for e in erros if e["contradicoes"]]
    if contraditorios:
        observacoes.append(
            f"{len(contraditorios)} erro(s) com sinais divergentes; a causa escolhida é "
            "a de evidência mais forte e as demais ficam registradas em `contradicoes`."
        )
    if declarados and not medidos:
        observacoes.append(
            "Todos os erros vieram de relato do estudante: sem respostas do simulado, "
            "a classificação não pôde ser conferida contra o gabarito."
        )
    if respostas and not medidos:
        observacoes.append(
            "Respostas informadas não casaram com nenhum id do gabarito do agente 16."
        )
    if not evolucao["disponivel"]:
        observacoes.append(f"Tendência não declarada: {evolucao['base']}.")
    return observacoes


def analisar(entradas: dict[str, Any], hoje: date | None = None) -> dict[str, Any]:
    """Constrói o Relatório Inteligente de Erros."""
    hoje = hoje or date.today()
    dados = entradas.get("dados_usuario", {}) or {}
    campos = {k: v for k, v in dados.items() if k != "perfil"}
    if isinstance(dados.get("perfil"), dict):
        campos = {**campos, **dados["perfil"]}

    anteriores = entradas.get("saidas_anteriores", {})
    mapa_estrategico = anteriores.get("02", {}) or {}
    mapa_conhecimento = anteriores.get("03", {}) or {}
    grafo = anteriores.get("05", {}) or {}
    relatorio = anteriores.get("12", {}) or {}
    revisoes = anteriores.get("15", {}) or {}
    simulado = anteriores.get("16", {}) or {}

    respostas = _respostas(campos)
    medidos = _erros_do_simulado(simulado, respostas)
    declarados = _erros_declarados(campos)
    contexto = _contexto_por_topico(mapa_conhecimento, relatorio, grafo)
    pesos = _pesos_por_disciplina(mapa_estrategico)
    historico = _historico(campos)
    anterior = campos.get("relatorio_de_erros_anterior") or {}

    classificados = [{**erro, **_classificar(erro, contexto)} for erro in medidos + declarados]

    frequencias: dict[str, int] = {}
    for erro in classificados:
        frequencias[_chave(erro)] = frequencias.get(_chave(erro), 0) + 1

    resolvidos_antes = {
        f"{como_texto(e.get('topico') or '')}|{como_texto(e.get('tipo') or '')}"
        for e in anterior.get("indicadores", {}).get("erros_resolvidos", [])
    }
    pontos_totais = sum(float(e.get("peso") or 1) for e in medidos) or 0.0
    maxima = (simulado.get("criterios_de_correcao") or {}).get("pontuacao_maxima") or pontos_totais

    detalhados: list[dict] = []
    for indice, erro in enumerate(classificados, start=1):
        frequencia = frequencias[_chave(erro)]
        gravidade = _gravidade(
            erro, frequencia, pesos, contexto, _chave(erro) in resolvidos_antes
        )
        detalhados.append(
            {
                "id": f"e{indice:03d}",
                "disciplina": erro.get("disciplina"),
                "topico": erro.get("topico"),
                "questao": erro.get("questao"),
                "tipo": erro["tipo"],
                # A competência vem do agente 16 e é o que o agente 18 agrega
                # para achar as competências mais comprometidas.
                "competencia_avaliada": erro.get("competencia"),
                "causa_provavel": erro["causa_provavel"],
                "evidencias": erro["evidencias"],
                "contradicoes": erro["contradicoes"],
                "falta_para_determinar": erro["falta_para_determinar"],
                "frequencia": frequencia,
                "recorrente": frequencia >= MINIMO_PARA_RECORRENCIA,
                "gravidade": gravidade,
                "impacto_no_desempenho": _impacto(erro, maxima),
                "conteudo_relacionado": {
                    "topico": erro.get("topico"),
                    "disciplina": erro.get("disciplina"),
                    "pre_requisitos": contexto.get(
                        como_texto(erro.get("topico") or ""), {}
                    ).get("pre_requisitos", []),
                    "dominio_medido": contexto.get(
                        como_texto(erro.get("topico") or ""), {}
                    ).get("classificacao", "indeterminado"),
                },
                "tipo_de_dificuldade_no_agente_12": EQUIVALENCIA_NO_AGENTE_12.get(
                    erro["tipo"]
                ),
                "origem": erro["origem"],
                "data": erro["data"].isoformat() if erro.get("data") else None,
            }
        )

    ordenados = sorted(detalhados, key=lambda e: -e["gravidade"]["score"])
    for posicao, erro in enumerate(ordenados, start=1):
        erro["prioridade_de_correcao"] = posicao

    contagem_por_tipo: dict[str, int] = {}
    for erro in detalhados:
        contagem_por_tipo[erro["tipo"]] = contagem_por_tipo.get(erro["tipo"], 0) + 1

    respondidas = len(respostas) or sum(r["total"] for r in historico)
    evolucao = _evolucao(historico)

    return {
        "emitido_em": hoje.isoformat(),
        "resumo_geral": {
            "total_de_erros": len(detalhados),
            "erros_medidos": len(medidos),
            "erros_relatados": len(declarados),
            "respostas_analisadas": int(respondidas),
            "taxa_de_erro": (
                round(len(detalhados) / respondidas, 4) if respondidas else None
            ),
            "base_da_taxa": (
                "erros sobre respostas conferidas contra gabarito"
                if respostas
                else "erros sobre respostas do histórico informado"
                if respondidas
                else "sem respostas registradas; taxa não calculada"
            ),
            "evolucao_da_taxa_de_erro": evolucao,
            "tipos_predominantes": sorted(
                contagem_por_tipo, key=lambda t: -contagem_por_tipo[t]
            )[:3],
            "contagem_por_tipo": contagem_por_tipo,
        },
        "erros": ordenados,
        "indicadores": {
            **_indicadores(detalhados, anterior, historico),
            "tendencia_de_melhoria": evolucao["tendencia"],
            "recomendacoes_de_intervencao": _recomendacoes(detalhados, revisoes),
        },
        "consumido_por": CONSUMIDORES,
        "observacoes": _observacoes(
            detalhados, len(medidos), len(declarados), evolucao, respostas
        ),
        "lacunas": (
            []
            if detalhados
            else ["respostas_do_simulado", "erros_registrados"]
        ),
        "confiabilidade": (
            "alta" if medidos and not any(e["tipo"] == "indeterminado" for e in detalhados)
            else "media" if detalhados
            else "baixa"
        ),
        "constantes_aplicadas": {
            "tipos_de_erro": TIPOS_DE_ERRO,
            "tipo_por_categoria": TIPO_POR_CATEGORIA,
            "equivalencia_no_agente_12": EQUIVALENCIA_NO_AGENTE_12,
            "limiar_acerto_alto": LIMIAR_ACERTO_ALTO,
            "fator_tempo_excessivo": FATOR_TEMPO_EXCESSIVO,
            "minimo_para_recorrencia": MINIMO_PARA_RECORRENCIA,
            "minimo_para_tendencia": MINIMO_PARA_TENDENCIA,
            "faixas_de_gravidade": {nome: limite for limite, nome in FAIXAS_DE_GRAVIDADE},
        },
    }


__all__ = [
    "EQUIVALENCIA_NO_AGENTE_12",
    "FATOR_TEMPO_EXCESSIVO",
    "LIMIAR_ACERTO_ALTO",
    "MINIMO_PARA_RECORRENCIA",
    "MINIMO_PARA_TENDENCIA",
    "TIPOS_DE_ERRO",
    "TIPO_POR_CATEGORIA",
    "analisar",
]
