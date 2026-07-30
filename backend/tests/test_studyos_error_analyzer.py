from datetime import date

import pytest

from app.studyos.agentes.conhecimento import analisar as analisar_conhecimento
from app.studyos.agentes.curriculo import construir as construir_curriculo
from app.studyos.agentes.dependencias import mapear
from app.studyos.agentes.dificuldade import detectar
from app.studyos.agentes.erros import (
    EQUIVALENCIA_NO_AGENTE_12,
    FATOR_TEMPO_EXCESSIVO,
    LIMIAR_ACERTO_ALTO,
    MINIMO_PARA_RECORRENCIA,
    MINIMO_PARA_TENDENCIA,
    TIPOS_DE_ERRO,
    analisar,
)
from app.studyos.agentes.objetivo import analisar as analisar_objetivo
from app.studyos.agentes.perfil import analisar as analisar_perfil
from app.studyos.agentes.roadmap import construir as construir_roadmap
from app.studyos.agentes.simulado import gerar as gerar_simulado
from app.studyos.orchestrator import MasterOrchestrator

HOJE = date(2026, 1, 5)

EDITAL = {
    "Estatística": {"questoes": 10, "topicos": ["Conjuntos", "Probabilidade"]},
    "Português": {"questoes": 20, "topicos": ["Crase", "Sintaxe"]},
}


def acertos(topico, certos, total, disciplina="Português", quando=HOJE):
    return {
        "disciplina": disciplina,
        "topico": topico,
        "acertos": certos,
        "total": total,
        "data": quando.isoformat(),
    }


#: Crase dominada, Conjuntos não — a diferença é o que separa erro de atenção
#: de erro conceitual.
HISTORICO = {
    "resultados_exercicios": [
        acertos("Crase", 19, 20),
        acertos("Sintaxe", 6, 10),
        acertos("Conjuntos", 3, 10, disciplina="Estatística"),
        acertos("Probabilidade", 7, 10, disciplina="Estatística"),
    ]
}


def redator_de_questoes(briefing):
    return {
        slot["numero"]: {
            "enunciado": f"Enunciado {slot['numero']} sobre {slot['topico']}",
            "alternativas": ["A", "B", "C", "D"],
            "resposta": "A",
            "explicacao": f"porque {slot['topico']}",
        }
        for slot in briefing["slots"]
    }


def cadeia(dados=None, com_simulado=True):
    """Roda 01–06, 12 e 16 de verdade e devolve as entradas prontas para o 17."""
    base = {
        "objetivo": "Passar no concurso fiscal",
        "edital": EDITAL,
        "escolaridade": "Superior completo",
        "horas_por_dia": 4,
        "dias_por_semana": 5,
        "data_prova": "2026-06-01",
        **HISTORICO,
        **(dados or {}),
    }
    m1 = analisar_perfil({"dados_usuario": base}, hoje=HOJE)
    m2 = analisar_objetivo({"dados_usuario": base, "solicitacao": ""}, hoje=HOJE)
    m3 = analisar_conhecimento(
        {"dados_usuario": base, "saidas_anteriores": {"01": m1, "02": m2}}, hoje=HOJE
    )
    m4 = construir_curriculo(
        {"dados_usuario": base, "saidas_anteriores": {"02": m2, "03": m3}}
    )
    m5 = mapear({"dados_usuario": base, "saidas_anteriores": {"03": m3, "04": m4}})
    m6 = construir_roadmap(
        {"dados_usuario": base, "saidas_anteriores": {"01": m1, "02": m2, "05": m5}},
        hoje=HOJE,
    )
    ant = {"01": m1, "02": m2, "03": m3, "04": m4, "05": m5, "06": m6}
    ant["12"] = detectar({"dados_usuario": base, "saidas_anteriores": ant}, hoje=HOJE)

    if com_simulado:
        ant["16"] = gerar_simulado(
            {"dados_usuario": base, "saidas_anteriores": ant},
            redator=redator_de_questoes,
            hoje=HOJE,
        )

    return {"solicitacao": "", "dados_usuario": base, "saidas_anteriores": ant}


def questoes_de(entradas, topico=None):
    """Questões do simulado, opcionalmente filtradas por tópico."""
    return [
        q
        for q in entradas["saidas_anteriores"]["16"]["questoes"]
        if topico is None or q["topico"] == topico
    ]


def responder(entradas, erradas=(), **extras):
    """Gabarito do estudante: acerta tudo, menos os ids listados."""
    correta = {g["id"]: g["resposta_correta"] for g in entradas["saidas_anteriores"]["16"]["gabarito"]}
    return [
        {
            "id": identificador,
            "resposta": "ZZZ" if identificador in erradas else resposta,
            **(extras.get(identificador) or {}),
        }
        for identificador, resposta in correta.items()
    ]


def rodar(entradas, respostas=None, **campos):
    dados = {**entradas["dados_usuario"], **campos}
    if respostas is not None:
        dados["respostas"] = respostas
    return analisar({**entradas, "dados_usuario": dados}, hoje=HOJE)


# --------------------------------------------------------------------------- #
# Coleta: o erro é medido, não deduzido
# --------------------------------------------------------------------------- #


def test_sem_respostas_e_sem_relato_nao_ha_erro():
    """Taxa de acerto baixa não vira lista de erros: erro precisa ser observado."""
    relatorio = rodar(cadeia())

    assert relatorio["resumo_geral"]["total_de_erros"] == 0
    assert relatorio["erros"] == []
    assert relatorio["confiabilidade"] == "baixa"
    assert "não deduz erro de taxa de acerto" in relatorio["observacoes"][0]
    assert relatorio["lacunas"] == ["respostas_do_simulado", "erros_registrados"]


def test_erro_sai_da_comparacao_com_o_gabarito():
    entradas = cadeia()
    alvo = questoes_de(entradas)[0]["id"]
    relatorio = rodar(entradas, responder(entradas, erradas={alvo}))

    assert relatorio["resumo_geral"]["total_de_erros"] == 1
    erro = relatorio["erros"][0]
    assert erro["questao"] == alvo
    assert erro["origem"] == "resposta conferida contra o gabarito do agente 16"


def test_resposta_certa_nao_vira_erro():
    entradas = cadeia()
    relatorio = rodar(entradas, responder(entradas))

    assert relatorio["resumo_geral"]["total_de_erros"] == 0
    assert relatorio["resumo_geral"]["taxa_de_erro"] == 0.0


def test_questao_nao_respondida_nao_entra_como_erro():
    """O que o estudante não chegou a fazer não é erro dele."""
    entradas = cadeia()
    ids = [q["id"] for q in questoes_de(entradas)]
    relatorio = rodar(entradas, responder(entradas, erradas=set(ids[:1]))[:1])

    assert relatorio["resumo_geral"]["respostas_analisadas"] == 1


def test_erro_relatado_pelo_estudante_e_aceito_sem_simulado():
    entradas = cadeia(com_simulado=False)
    relatorio = rodar(
        entradas,
        erros=[{"topico": "Crase", "disciplina": "Português", "tipo": "atencao"}],
    )

    assert relatorio["resumo_geral"]["erros_relatados"] == 1
    assert relatorio["erros"][0]["origem"] == "erro registrado pelo estudante"
    assert any("relato do estudante" in o for o in relatorio["observacoes"])


def test_taxa_de_erro_declara_a_base():
    entradas = cadeia()
    ids = [q["id"] for q in questoes_de(entradas)][:2]
    relatorio = rodar(entradas, responder(entradas, erradas=set(ids)))
    resumo = relatorio["resumo_geral"]

    assert resumo["taxa_de_erro"] == round(2 / resumo["respostas_analisadas"], 4)
    assert "conferidas contra gabarito" in resumo["base_da_taxa"]


# --------------------------------------------------------------------------- #
# Classificação: nenhuma causa sem evidência
# --------------------------------------------------------------------------- #


def test_erro_sem_nenhuma_evidencia_fica_indeterminado():
    entradas = cadeia(com_simulado=False)
    relatorio = rodar(entradas, erros=[{"topico": "Tópico fora do edital"}])
    erro = relatorio["erros"][0]

    assert erro["tipo"] == "indeterminado"
    assert erro["causa_provavel"] is None
    assert erro["evidencias"] == []
    assert erro["falta_para_determinar"]
    assert any("não foi presumida" in o for o in relatorio["observacoes"])


def test_toda_causa_declarada_vem_com_evidencia():
    entradas = cadeia()
    ids = {q["id"] for q in questoes_de(entradas)[:5]}
    relatorio = rodar(entradas, responder(entradas, erradas=ids))

    for erro in relatorio["erros"]:
        if erro["causa_provavel"] is not None:
            assert erro["evidencias"], erro
            assert all(e["evidencia"] for e in erro["evidencias"])


def test_dominio_insuficiente_classifica_como_conceitual():
    entradas = cadeia()
    alvo = questoes_de(entradas, "Conjuntos")[0]["id"]
    relatorio = rodar(entradas, responder(entradas, erradas={alvo}))
    erro = next(e for e in relatorio["erros"] if e["questao"] == alvo)

    assert erro["tipo"] == "conceitual"
    assert "domínio insuficiente" in erro["causa_provavel"]
    assert any("agente 03" in e["evidencia"] for e in erro["evidencias"])


def test_acerto_alto_no_topico_classifica_como_atencao():
    """19/20 em Crase: errar uma questão ali é escorregão, não desconhecimento."""
    entradas = cadeia()
    alvo = questoes_de(entradas, "Crase")[0]["id"]
    relatorio = rodar(entradas, responder(entradas, erradas={alvo}))
    erro = next(e for e in relatorio["erros"] if e["questao"] == alvo)

    assert erro["tipo"] == "atencao"
    assert f"{LIMIAR_ACERTO_ALTO:.0%}" in erro["evidencias"][0]["evidencia"]


def test_questao_em_branco_vira_gestao_do_tempo():
    entradas = cadeia()
    alvo = questoes_de(entradas, "Conjuntos")[0]["id"]
    respostas = [
        {**r, "resposta": None} if r["id"] == alvo else r
        for r in responder(entradas)
    ]
    relatorio = rodar(entradas, respostas)
    erro = next(e for e in relatorio["erros"] if e["questao"] == alvo)

    assert erro["tipo"] == "gestao_do_tempo"
    assert erro["causa_provavel"] == "questão não respondida"


def test_tempo_muito_acima_do_previsto_vira_gestao_do_tempo():
    entradas = cadeia()
    questao = questoes_de(entradas, "Conjuntos")[0]
    estourado = questao["minutos_previstos"] * FATOR_TEMPO_EXCESSIVO + 1
    relatorio = rodar(
        entradas,
        responder(
            entradas,
            erradas={questao["id"]},
            **{questao["id"]: {"tempo_min": estourado}},
        ),
    )
    erro = next(e for e in relatorio["erros"] if e["questao"] == questao["id"])

    assert erro["tipo"] == "gestao_do_tempo"
    assert "min previstos" in erro["evidencias"][0]["evidencia"]


def test_tempo_dentro_do_previsto_nao_gera_sinal_de_tempo():
    entradas = cadeia()
    questao = questoes_de(entradas, "Conjuntos")[0]
    relatorio = rodar(
        entradas,
        responder(
            entradas,
            erradas={questao["id"]},
            **{questao["id"]: {"tempo_min": questao["minutos_previstos"]}},
        ),
    )
    erro = next(e for e in relatorio["erros"] if e["questao"] == questao["id"])

    assert erro["tipo"] != "gestao_do_tempo"


def test_tipo_declarado_pelo_estudante_tem_precedencia():
    entradas = cadeia()
    alvo = questoes_de(entradas, "Conjuntos")[0]["id"]
    relatorio = rodar(
        entradas,
        responder(entradas, erradas={alvo}, **{alvo: {"tipo": "calculo"}}),
    )
    erro = next(e for e in relatorio["erros"] if e["questao"] == alvo)

    assert erro["tipo"] == "calculo"
    assert erro["evidencias"][0]["forca"] == "declarada"


def test_sinal_divergente_e_registrado_em_vez_de_descartado():
    """O estudante diz "desatenção", o agente 03 diz "não conhece": ambos ficam."""
    entradas = cadeia()
    alvo = questoes_de(entradas, "Conjuntos")[0]["id"]
    relatorio = rodar(
        entradas,
        responder(entradas, erradas={alvo}, **{alvo: {"tipo": "atencao"}}),
    )
    erro = next(e for e in relatorio["erros"] if e["questao"] == alvo)

    assert erro["tipo"] == "atencao"
    assert any("conceitual" in c for c in erro["contradicoes"])
    assert any("sinais divergentes" in o for o in relatorio["observacoes"])


def test_todo_tipo_atribuido_esta_na_taxonomia():
    entradas = cadeia()
    ids = {q["id"] for q in questoes_de(entradas)}
    relatorio = rodar(entradas, responder(entradas, erradas=ids))

    for erro in relatorio["erros"]:
        assert erro["tipo"] in TIPOS_DE_ERRO + ("indeterminado",)


def test_pre_requisito_nao_dominado_aparece_como_causa():
    entradas = cadeia({"pre_requisitos": {"Probabilidade": ["Conjuntos"]}})
    alvo = questoes_de(entradas, "Probabilidade")[0]["id"]
    relatorio = rodar(entradas, responder(entradas, erradas={alvo}))
    erro = next(e for e in relatorio["erros"] if e["questao"] == alvo)

    assert "Conjuntos" in (erro["causa_provavel"] or "")
    assert erro["conteudo_relacionado"]["pre_requisitos"] == ["Conjuntos"]


# --------------------------------------------------------------------------- #
# Frequência, gravidade e impacto
# --------------------------------------------------------------------------- #


def test_repeticao_do_mesmo_par_topico_tipo_e_recorrente():
    entradas = cadeia()
    ids = {q["id"] for q in questoes_de(entradas, "Conjuntos")[:MINIMO_PARA_RECORRENCIA]}
    relatorio = rodar(entradas, responder(entradas, erradas=ids))
    recorrentes = relatorio["indicadores"]["erros_recorrentes"]

    assert recorrentes
    assert recorrentes[0]["frequencia"] >= MINIMO_PARA_RECORRENCIA
    assert all(e["recorrente"] for e in relatorio["erros"] if e["topico"] == "Conjuntos")


def test_padrao_recorrente_aparece_uma_vez_so():
    """Três questões erradas pelo mesmo motivo são um problema, não três."""
    entradas = cadeia()
    ids = {q["id"] for q in questoes_de(entradas, "Conjuntos")[:3]}
    relatorio = rodar(entradas, responder(entradas, erradas=ids))
    recorrentes = relatorio["indicadores"]["erros_recorrentes"]

    assert len(recorrentes) == 1
    assert recorrentes[0]["frequencia"] == 3
    assert sorted(recorrentes[0]["questoes"]) == sorted(ids)


def test_erro_unico_nao_e_recorrente():
    entradas = cadeia()
    alvo = questoes_de(entradas, "Conjuntos")[0]["id"]
    relatorio = rodar(entradas, responder(entradas, erradas={alvo}))

    assert relatorio["erros"][0]["frequencia"] == 1
    assert relatorio["erros"][0]["recorrente"] is False
    assert relatorio["indicadores"]["erros_recorrentes"] == []


def test_gravidade_declara_cada_fator_do_score():
    entradas = cadeia()
    ids = {q["id"] for q in questoes_de(entradas, "Conjuntos")[:3]}
    relatorio = rodar(entradas, responder(entradas, erradas=ids))
    gravidade = relatorio["erros"][0]["gravidade"]

    assert gravidade["nivel"] in ("baixa", "media", "alta", "critica")
    assert gravidade["fatores"]
    assert any("ocorrências" in f for f in gravidade["fatores"])


def test_recorrencia_agrava_o_erro():
    entradas = cadeia()
    um = rodar(
        entradas, responder(entradas, erradas={questoes_de(entradas, "Conjuntos")[0]["id"]})
    )
    varios = rodar(
        entradas,
        responder(entradas, erradas={q["id"] for q in questoes_de(entradas, "Conjuntos")[:4]}),
    )

    assert varios["erros"][0]["gravidade"]["score"] > um["erros"][0]["gravidade"]["score"]


def test_prioridade_de_correcao_segue_a_gravidade():
    entradas = cadeia()
    ids = {q["id"] for q in questoes_de(entradas)[:6]}
    relatorio = rodar(entradas, responder(entradas, erradas=ids))
    scores = [e["gravidade"]["score"] for e in relatorio["erros"]]

    assert scores == sorted(scores, reverse=True)
    assert [e["prioridade_de_correcao"] for e in relatorio["erros"]] == list(
        range(1, len(relatorio["erros"]) + 1)
    )


def test_impacto_sai_do_peso_da_questao():
    entradas = cadeia()
    alvo = questoes_de(entradas, "Conjuntos")[0]
    relatorio = rodar(entradas, responder(entradas, erradas={alvo["id"]}))
    impacto = relatorio["erros"][0]["impacto_no_desempenho"]
    maxima = entradas["saidas_anteriores"]["16"]["criterios_de_correcao"]["pontuacao_maxima"]

    assert impacto["pontos_perdidos"] == alvo["peso"]
    assert impacto["fracao_da_pontuacao"] == round(alvo["peso"] / maxima, 4)
    assert "pontos do simulado" in impacto["base"]


def test_sem_pontuacao_o_impacto_nao_e_inventado():
    entradas = cadeia(com_simulado=False)
    relatorio = rodar(entradas, erros=[{"topico": "Crase", "tipo": "atencao"}])
    impacto = relatorio["erros"][0]["impacto_no_desempenho"]

    assert impacto["fracao_da_pontuacao"] is None
    assert "não calculado" in impacto["base"]


# --------------------------------------------------------------------------- #
# Evolução e indicadores
# --------------------------------------------------------------------------- #


def test_amostra_pequena_nao_declara_tendencia():
    entradas = cadeia({"resultados_exercicios": [acertos("Crase", 4, 5)]})
    relatorio = rodar(entradas, erros=[{"topico": "Crase", "tipo": "atencao"}])
    evolucao = relatorio["resumo_geral"]["evolucao_da_taxa_de_erro"]

    assert evolucao["disponivel"] is False
    assert evolucao["tendencia"] == "indeterminada"
    assert str(MINIMO_PARA_TENDENCIA * 2) in evolucao["base"]


def test_historico_de_um_dia_so_nao_vira_tendencia():
    """Tópicos diferentes na mesma data não são "antes" e "depois"."""
    entradas = cadeia(
        {
            "resultados_exercicios": [
                acertos("Crase", 18, 20),
                acertos("Conjuntos", 3, 20, disciplina="Estatística"),
            ]
        }
    )
    relatorio = rodar(entradas, erros=[{"topico": "Crase", "tipo": "atencao"}])
    evolucao = relatorio["resumo_geral"]["evolucao_da_taxa_de_erro"]

    assert evolucao["disponivel"] is False
    assert "mesma data" in evolucao["base"]


def test_corte_da_tendencia_e_uma_data():
    entradas = cadeia(
        {
            "resultados_exercicios": [
                acertos("Crase", 5, 20, quando=date(2025, 11, 1)),
                acertos("Crase", 18, 20, quando=date(2025, 12, 1)),
            ]
        }
    )
    relatorio = rodar(entradas, erros=[{"topico": "Crase", "tipo": "atencao"}])
    evolucao = relatorio["resumo_geral"]["evolucao_da_taxa_de_erro"]

    assert evolucao["corte"] == "2025-11-01"
    assert "até 2025-11-01" in evolucao["base"]


def test_queda_da_taxa_de_erro_e_lida_como_melhora():
    entradas = cadeia(
        {
            "resultados_exercicios": [
                acertos("Crase", 5, 20, quando=date(2025, 11, 1)),
                acertos("Crase", 18, 20, quando=date(2025, 12, 1)),
            ]
        }
    )
    relatorio = rodar(entradas, erros=[{"topico": "Crase", "tipo": "atencao"}])
    evolucao = relatorio["resumo_geral"]["evolucao_da_taxa_de_erro"]

    assert evolucao["disponivel"] is True
    assert evolucao["tendencia"] == "melhora"
    assert evolucao["taxa_recente"] < evolucao["taxa_inicial"]
    assert relatorio["indicadores"]["tendencia_de_melhoria"] == "melhora"


def test_alta_da_taxa_de_erro_e_lida_como_piora():
    entradas = cadeia(
        {
            "resultados_exercicios": [
                acertos("Crase", 18, 20, quando=date(2025, 11, 1)),
                acertos("Crase", 5, 20, quando=date(2025, 12, 1)),
            ]
        }
    )
    relatorio = rodar(entradas, erros=[{"topico": "Crase", "tipo": "atencao"}])

    assert relatorio["resumo_geral"]["evolucao_da_taxa_de_erro"]["tendencia"] == "piora"


def test_erro_que_sumiu_sem_pratica_nova_nao_conta_como_resolvido():
    """Ausência de erro não é prova de correção."""
    entradas = cadeia(com_simulado=False)
    #: "Ortografia" não aparece em nenhum resultado de exercício do histórico.
    anterior = {
        "emitido_em": "2026-01-04",
        "erros": [{"topico": "Ortografia", "tipo": "conceitual"}],
    }
    relatorio = rodar(
        entradas,
        erros=[{"topico": "Crase", "tipo": "atencao"}],
        relatorio_de_erros_anterior=anterior,
    )
    indicadores = relatorio["indicadores"]

    assert indicadores["erros_resolvidos"] == []
    assert indicadores["sem_nova_evidencia"][0]["topico"] == "Ortografia"
    assert "não houve prática nova" in indicadores["sem_nova_evidencia"][0]["base"]


def test_erro_que_sumiu_com_pratica_nova_conta_como_resolvido():
    entradas = cadeia(
        {"resultados_exercicios": [acertos("Sintaxe", 10, 10, quando=date(2026, 1, 5))]},
        com_simulado=False,
    )
    anterior = {
        "emitido_em": "2026-01-01",
        "erros": [{"topico": "Sintaxe", "tipo": "conceitual"}],
    }
    relatorio = rodar(
        entradas,
        erros=[{"topico": "Crase", "tipo": "atencao"}],
        relatorio_de_erros_anterior=anterior,
    )
    indicadores = relatorio["indicadores"]

    assert indicadores["erros_resolvidos"][0]["topico"] == "Sintaxe"
    assert indicadores["sem_nova_evidencia"] == []


def test_erro_inedito_entra_como_novo():
    entradas = cadeia(com_simulado=False)
    anterior = {
        "emitido_em": "2026-01-01",
        "erros": [{"topico": "Sintaxe", "tipo": "conceitual"}],
    }
    relatorio = rodar(
        entradas,
        erros=[{"topico": "Crase", "tipo": "atencao"}],
        relatorio_de_erros_anterior=anterior,
    )

    assert relatorio["indicadores"]["novos_erros"] == [
        {"topico": "Crase", "tipo": "atencao"}
    ]


def test_regressao_agrava_o_erro():
    entradas = cadeia(com_simulado=False)
    anterior = {
        "emitido_em": "2026-01-01",
        "indicadores": {"erros_resolvidos": [{"topico": "Crase", "tipo": "atencao"}]},
    }
    reincidente = rodar(
        entradas,
        erros=[{"topico": "Crase", "tipo": "atencao"}],
        relatorio_de_erros_anterior=anterior,
    )
    inedito = rodar(entradas, erros=[{"topico": "Crase", "tipo": "atencao"}])

    assert reincidente["erros"][0]["gravidade"]["score"] > inedito["erros"][0]["gravidade"]["score"]
    assert any(
        "voltou a ocorrer" in f for f in reincidente["erros"][0]["gravidade"]["fatores"]
    )


# --------------------------------------------------------------------------- #
# Recomendações e limites do agente
# --------------------------------------------------------------------------- #


def test_recomendacao_aponta_o_agente_responsavel():
    entradas = cadeia()
    ids = {q["id"] for q in questoes_de(entradas, "Conjuntos")[:2]}
    relatorio = rodar(entradas, responder(entradas, erradas=ids))
    recomendacoes = relatorio["indicadores"]["recomendacoes_de_intervencao"]

    assert recomendacoes
    for recomendacao in recomendacoes:
        assert recomendacao["agente_responsavel"]
        assert recomendacao["intervencao"]


def test_relatorio_nao_carrega_plano_grafo_nem_exercicio():
    """Não ensina, não planeja, não gera questão."""
    entradas = cadeia()
    ids = {q["id"] for q in questoes_de(entradas)[:3]}
    relatorio = rodar(entradas, responder(entradas, erradas=ids))

    proibidos = ("cronograma", "plano_de_estudos", "blocos", "nos", "arestas", "exercicios", "aula")
    assert not set(relatorio) & set(proibidos)
    for erro in relatorio["erros"]:
        assert "enunciado" not in erro
        assert "resposta_correta" not in erro


def test_constantes_sao_declaradas():
    entradas = cadeia(com_simulado=False)
    relatorio = rodar(entradas, erros=[{"topico": "Crase", "tipo": "atencao"}])
    constantes = relatorio["constantes_aplicadas"]

    assert constantes["limiar_acerto_alto"] == LIMIAR_ACERTO_ALTO
    assert constantes["minimo_para_recorrencia"] == MINIMO_PARA_RECORRENCIA
    assert constantes["tipos_de_erro"] == TIPOS_DE_ERRO


# --------------------------------------------------------------------------- #
# Integração com o agente 12
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("tipo", TIPOS_DE_ERRO)
def test_todo_tipo_declara_sua_traducao_para_o_agente_12(tipo):
    assert tipo in EQUIVALENCIA_NO_AGENTE_12


def test_erro_de_execucao_nao_vira_dificuldade_de_conteudo():
    """Desatenção não é dificuldade com o conteúdo — o agente 12 não a soma."""
    entradas = cadeia(com_simulado=False)
    relatorio = rodar(entradas, erros=[{"topico": "Crase", "tipo": "atencao"}])
    assert relatorio["erros"][0]["tipo_de_dificuldade_no_agente_12"] is None

    novo12 = detectar(
        {
            "dados_usuario": entradas["dados_usuario"],
            "saidas_anteriores": {**entradas["saidas_anteriores"], "17": relatorio},
        },
        hoje=HOJE,
    )
    crase = next(t for t in novo12["topicos"] if t["topico"] == "Crase")
    assert crase["tipos_de_dificuldade"]["contagem"] == {}
    assert crase["tipos_de_dificuldade"]["erros_nao_atribuiveis_ao_conteudo"] == 1
    assert crase["tipos_de_dificuldade"]["erros_sem_classificacao"] == 0


def test_erro_conceitual_realimenta_o_agente_12():
    entradas = cadeia(com_simulado=False)
    relatorio = rodar(
        entradas,
        erros=[{"topico": "Conjuntos", "disciplina": "Estatística", "tipo": "conceitual"}],
    )
    novo12 = detectar(
        {
            "dados_usuario": entradas["dados_usuario"],
            "saidas_anteriores": {**entradas["saidas_anteriores"], "17": relatorio},
        },
        hoje=HOJE,
    )
    conjuntos = next(t for t in novo12["topicos"] if t["topico"] == "Conjuntos")

    assert conjuntos["tipos_de_dificuldade"]["predominante"] == "conceitual"


# --------------------------------------------------------------------------- #
# Orquestrador
# --------------------------------------------------------------------------- #


async def test_orquestrador_executa_o_17_depois_do_16():
    resultado = await MasterOrchestrator().orquestrar(
        "quero analisar meus erros do simulado",
        dados_usuario={
            "objetivo": "Passar no concurso fiscal",
            "edital": EDITAL,
            "escolaridade": "Superior completo",
            "horas_por_dia": 4,
            "dias_por_semana": 5,
            "data_prova": "2026-06-01",
            **HISTORICO,
            "erros": [{"topico": "Conjuntos", "tipo": "conceitual"}],
        },
    )
    ordem = [sorted(onda) for onda in resultado.ondas]
    posicao = {agente: indice for indice, onda in enumerate(ordem) for agente in onda}

    assert posicao["17"] > posicao["16"]
    assert resultado.saidas["17"].conteudo["resumo_geral"]["total_de_erros"] == 1
