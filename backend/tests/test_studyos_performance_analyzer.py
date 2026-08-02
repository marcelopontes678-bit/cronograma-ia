from datetime import date, timedelta

from app.studyos.agentes.coach import acompanhar
from app.studyos.agentes.conhecimento import analisar as analisar_conhecimento
from app.studyos.agentes.curriculo import construir as construir_curriculo
from app.studyos.agentes.dependencias import mapear as mapear_dependencias
from app.studyos.agentes.dificuldade import detectar
from app.studyos.agentes.erros import analisar as analisar_erros
from app.studyos.agentes.fraquezas import mapear as mapear_fraquezas
from app.studyos.agentes.habitos import construir as construir_habitos
from app.studyos.agentes.objetivo import analisar as analisar_objetivo
from app.studyos.agentes.perfil import analisar as analisar_perfil
from app.studyos.agentes.performance import (
    ATRASO_RELEVANTE,
    FAIXAS_DO_IGP,
    JANELA_MENSAL,
    JANELA_SEMANAL,
    MINIMO_DE_QUESTOES,
    NIVEL_MAXIMO_DO_IGP,
    PESOS_DO_IGP,
    TIPOS_DE_ALERTA,
    VALOR_POR_CLASSIFICACAO,
    VARIACAO_RELEVANTE,
    analisar,
)
from app.studyos.agentes.roadmap import construir as construir_roadmap
from app.studyos.orchestrator import MasterOrchestrator

INICIO_DO_PLANO = date(2026, 3, 2)
HOJE = INICIO_DO_PLANO + timedelta(days=12)

EDITAL = {
    "Estatística": {"questoes": 10, "topicos": ["Conjuntos", "Probabilidade"]},
    "Português": {"questoes": 20, "topicos": ["Crase", "Sintaxe", "Ortografia", "Verbos"]},
}


def acertos(topico, certos, total, disciplina="Português", quando=None, minutos=None):
    registro = {
        "disciplina": disciplina,
        "topico": topico,
        "acertos": certos,
        "total": total,
        "data": (quando or HOJE).isoformat(),
    }
    if minutos is not None:
        registro["tempo_min"] = minutos
    return registro


HISTORICO = {
    "resultados_exercicios": [
        acertos("Crase", 19, 20),
        acertos("Sintaxe", 6, 10),
        acertos("Conjuntos", 3, 10, disciplina="Estatística"),
        acertos("Probabilidade", 7, 10, disciplina="Estatística"),
    ]
}


def cadeia(dados=None, com_acompanhamento=True):
    """Roda a cadeia real até o 20 e devolve as entradas prontas para o 21."""
    base = {
        "objetivo": "Passar no concurso fiscal",
        "edital": EDITAL,
        "escolaridade": "Superior completo",
        "horas_por_dia": 2,
        "dias_por_semana": 5,
        "data_prova": "2026-09-01",
        **HISTORICO,
        **(dados or {}),
    }
    m1 = analisar_perfil({"dados_usuario": base}, hoje=INICIO_DO_PLANO)
    m2 = analisar_objetivo({"dados_usuario": base, "solicitacao": ""}, hoje=INICIO_DO_PLANO)
    m3 = analisar_conhecimento(
        {"dados_usuario": base, "saidas_anteriores": {"01": m1, "02": m2}},
        hoje=INICIO_DO_PLANO,
    )
    m4 = construir_curriculo(
        {"dados_usuario": base, "saidas_anteriores": {"02": m2, "03": m3}}
    )
    m5 = mapear_dependencias(
        {"dados_usuario": base, "saidas_anteriores": {"03": m3, "04": m4}}
    )
    m6 = construir_roadmap(
        {"dados_usuario": base, "saidas_anteriores": {"01": m1, "02": m2, "05": m5}},
        hoje=INICIO_DO_PLANO,
    )
    ant = {"01": m1, "02": m2, "03": m3, "04": m4, "05": m5, "06": m6}
    ant["12"] = detectar({"dados_usuario": base, "saidas_anteriores": ant}, hoje=HOJE)
    ant["17"] = analisar_erros({"dados_usuario": base, "saidas_anteriores": ant}, hoje=HOJE)
    entradas = {"solicitacao": "", "dados_usuario": base, "saidas_anteriores": ant}
    ant["18"] = mapear_fraquezas(entradas, hoje=HOJE)

    if com_acompanhamento:
        ant["19"] = acompanhar(entradas, hoje=HOJE)
        ant["20"] = construir_habitos(entradas, hoje=HOJE)
    return entradas


def planejados(entradas):
    return [
        date.fromisoformat(d["data"])
        for d in entradas["saidas_anteriores"]["06"]["cronograma"]
        if date.fromisoformat(d["data"]) <= HOJE
    ]


def frequencia(datas, minutos=90):
    return [{"data": d.isoformat(), "minutos": minutos, "hora": "07:00"} for d in datas]


def rodar(entradas, **campos):
    dados = {**entradas["dados_usuario"], **campos}
    return analisar({**entradas, "dados_usuario": dados}, hoje=HOJE)


def com_acompanhamento(entradas, registros):
    """Recomputa 19 e 20 com a frequência informada, como no fluxo real."""
    dados = {**entradas["dados_usuario"], "historico_frequencia": registros}
    contexto = {**entradas, "dados_usuario": dados}
    contexto["saidas_anteriores"]["19"] = acompanhar(contexto, hoje=HOJE)
    contexto["saidas_anteriores"]["20"] = construir_habitos(contexto, hoje=HOJE)
    return contexto


# --------------------------------------------------------------------------- #
# Nunca preencher lacuna com zero
# --------------------------------------------------------------------------- #


def test_sem_dado_nenhum_o_igp_nao_e_calculado():
    """Zero é uma afirmação sobre o estudante; ausência de dado não é."""
    painel = analisar({"dados_usuario": {}, "saidas_anteriores": {}}, hoje=HOJE)
    igp = painel["resumo_geral"]["indice_geral_de_performance"]

    assert igp["valor"] is None
    assert igp["nivel"] == "indeterminado"
    assert igp["componentes"] == {}
    assert painel["confiabilidade"] == "baixa"
    assert any("não preenche lacuna com zero" in o for o in painel["observacoes"])


def test_componente_ausente_redistribui_o_peso():
    painel = rodar(cadeia())
    igp = painel["resumo_geral"]["indice_geral_de_performance"]
    componentes = igp["componentes"]

    esperado = sum(
        PESOS_DO_IGP[c] * d["valor"] for c, d in componentes.items()
    ) / sum(PESOS_DO_IGP[c] for c in componentes)
    assert igp["valor"] == round(esperado, 4)
    assert len(componentes) < len(PESOS_DO_IGP)
    assert any("redistribuído" in o for o in painel["observacoes"])


def test_indicador_sem_fonte_sai_nulo_com_motivo():
    painel = rodar(cadeia({"resultados_exercicios": []}))
    taxa = painel["indicadores_academicos"]["taxa_de_acertos"]

    assert taxa["valor"] is None
    assert taxa["base"] == "nenhuma questão registrada"
    assert "historico_de_questoes" in painel["lacunas"]


# --------------------------------------------------------------------------- #
# Procedência: todo número diz de onde veio
# --------------------------------------------------------------------------- #


def test_todo_indicador_declara_valor_base_e_origem():
    painel = rodar(cadeia())
    grupos = (
        "indicadores_academicos",
        "indicadores_de_aprendizagem",
        "indicadores_comportamentais",
    )
    for grupo in grupos:
        for nome, indicador in painel[grupo].items():
            assert set(indicador) == {"valor", "base", "origem"}, (grupo, nome)
            assert indicador["base"], (grupo, nome)


def test_indicadores_de_outros_agentes_citam_o_agente():
    entradas = cadeia()
    contexto = com_acompanhamento(entradas, frequencia(planejados(entradas)))
    painel = analisar(contexto, hoje=HOJE)

    assert painel["indicadores_comportamentais"]["engajamento"]["origem"] == "agente 19"
    assert painel["indicadores_comportamentais"]["regularidade"]["origem"] == "agente 20"
    assert painel["indicadores_de_aprendizagem"]["fragilidade_geral"]["origem"] == "agente 18"
    assert painel["indicadores_academicos"]["conteudos_concluidos"]["origem"] == "agente 04"


def test_numeros_dos_outros_agentes_sao_reaproveitados_e_nao_recalculados():
    """Um painel que discorda dos próprios relatórios não é painel, é ruído."""
    entradas = cadeia()
    contexto = com_acompanhamento(entradas, frequencia(planejados(entradas)))
    painel = analisar(contexto, hoje=HOJE)
    anteriores = contexto["saidas_anteriores"]

    assert painel["indicadores_de_aprendizagem"]["consistencia"]["valor"] == (
        anteriores["19"]["resumo_geral"]["indice_de_consistencia"]
    )
    assert painel["indicadores_de_aprendizagem"]["fragilidade_geral"]["valor"] == (
        anteriores["18"]["resumo_geral"]["indice_geral_de_fragilidade"]
    )
    assert painel["indicadores_comportamentais"]["engajamento"]["valor"] == (
        anteriores["19"]["resumo_geral"]["nivel_de_engajamento"]
    )


def test_sem_o_agente_19_a_consistencia_usa_o_mesmo_calculo():
    entradas = cadeia(com_acompanhamento=False)
    registros = frequencia(planejados(entradas))
    painel = rodar(entradas, historico_frequencia=registros)
    consistencia = painel["indicadores_de_aprendizagem"]["consistencia"]

    assert consistencia["valor"] is not None
    assert "mesmo cálculo do agente 19" in consistencia["origem"]


# --------------------------------------------------------------------------- #
# IGP
# --------------------------------------------------------------------------- #


def test_dominio_entra_com_a_escala_declarada():
    painel = rodar(cadeia())
    dominio = painel["resumo_geral"]["indice_geral_de_performance"]["componentes"]["dominio"]

    assert 0 <= dominio["valor"] <= 1
    assert "agente 03" in dominio["origem"]
    assert set(VALOR_POR_CLASSIFICACAO) == {
        "avancado", "intermediario", "basico", "nao_conhece"
    }


def test_nivel_do_igp_sai_das_faixas():
    painel = rodar(cadeia())
    igp = painel["resumo_geral"]["indice_geral_de_performance"]
    nomes = [nome for _, nome in FAIXAS_DO_IGP] + [NIVEL_MAXIMO_DO_IGP]

    assert igp["nivel"] in nomes


def test_desempenho_melhor_produz_igp_maior():
    fraco = rodar(cadeia({"resultados_exercicios": [acertos("Crase", 2, 20)]}))
    forte = rodar(cadeia({"resultados_exercicios": [acertos("Crase", 19, 20)]}))

    assert (
        forte["resumo_geral"]["indice_geral_de_performance"]["valor"]
        > fraco["resumo_geral"]["indice_geral_de_performance"]["valor"]
    )


def test_confianca_acompanha_a_quantidade_de_componentes():
    painel = rodar(cadeia())
    igp = painel["resumo_geral"]["indice_geral_de_performance"]
    quantidade = len(igp["componentes"])

    esperada = "alta" if quantidade >= 4 else "media" if quantidade >= 2 else "baixa"
    assert igp["confianca"] == esperada
    assert painel["confiabilidade"] == igp["confianca"]


# --------------------------------------------------------------------------- #
# Evolução
# --------------------------------------------------------------------------- #


def test_amostra_pequena_nao_declara_evolucao():
    painel = rodar(cadeia({"resultados_exercicios": [acertos("Crase", 3, 5)]}))
    semanal = painel["resumo_geral"]["evolucao_semanal"]

    assert semanal["disponivel"] is False
    assert semanal["tendencia"] == "indeterminada"
    assert str(MINIMO_DE_QUESTOES) in semanal["base"]


def test_queda_entre_janelas_e_detectada():
    registros = [
        acertos("Crase", 18, 20, quando=HOJE - timedelta(days=JANELA_SEMANAL + 2)),
        acertos("Crase", 5, 20, quando=HOJE - timedelta(days=1)),
    ]
    painel = rodar(cadeia({"resultados_exercicios": registros}))
    semanal = painel["resumo_geral"]["evolucao_semanal"]

    assert semanal["disponivel"] is True
    assert semanal["tendencia"] == "queda"
    assert semanal["variacao"] <= -VARIACAO_RELEVANTE


def test_melhora_entre_janelas_e_detectada():
    registros = [
        acertos("Crase", 5, 20, quando=HOJE - timedelta(days=JANELA_SEMANAL + 2)),
        acertos("Crase", 18, 20, quando=HOJE - timedelta(days=1)),
    ]
    painel = rodar(cadeia({"resultados_exercicios": registros}))

    assert painel["resumo_geral"]["evolucao_semanal"]["tendencia"] == "melhora"


def test_tendencia_geral_prefere_a_janela_mensal():
    registros = [
        acertos("Crase", 18, 20, quando=HOJE - timedelta(days=JANELA_MENSAL + 2)),
        acertos("Crase", 4, 20, quando=HOJE - timedelta(days=2)),
    ]
    painel = rodar(cadeia({"resultados_exercicios": registros}))
    resumo = painel["resumo_geral"]

    assert resumo["evolucao_mensal"]["disponivel"] is True
    assert resumo["tendencia_geral"] == resumo["evolucao_mensal"]["tendencia"]


# --------------------------------------------------------------------------- #
# Progresso e desvio
# --------------------------------------------------------------------------- #


def test_progresso_conta_topicos_da_arvore():
    entradas = cadeia()
    painel = rodar(entradas)
    progresso = painel["resumo_geral"]["percentual_de_progresso"]
    arvore = entradas["saidas_anteriores"]["04"]

    assert progresso["concluidos"] == len(arvore["conteudos_dominados"])
    assert progresso["total"] == arvore["totais"]["topicos"]
    assert progresso["percentual"] == round(
        progresso["concluidos"] / progresso["total"], 4
    )


def test_desvio_compara_planejado_com_realizado():
    entradas = cadeia()
    dias = planejados(entradas)
    painel = rodar(entradas, historico_frequencia=frequencia(dias[: len(dias) - 2]))
    desvio = painel["desvio_do_planejado"]

    assert desvio["disponivel"] is True
    assert desvio["dias_cumpridos"] == len(dias) - 2
    assert desvio["dias_planejados"] == len(dias)
    assert desvio["horas_de_diferenca"] == round(
        desvio["horas_estudadas"] - desvio["horas_planejadas"], 2
    )


def test_sem_dias_planejados_o_desvio_nao_e_medido():
    entradas = cadeia()
    entradas["saidas_anteriores"]["06"] = {"cronograma": []}
    painel = rodar(entradas, historico_frequencia=frequencia([HOJE]))

    assert painel["desvio_do_planejado"]["disponivel"] is False
    assert any("não medido" in o for o in painel["observacoes"])


# --------------------------------------------------------------------------- #
# Alertas
# --------------------------------------------------------------------------- #


def test_todo_alerta_tem_tipo_conhecido_e_base():
    entradas = cadeia()
    painel = rodar(entradas, historico_frequencia=frequencia(planejados(entradas)[:1]))

    for alerta in painel["alertas"]:
        assert alerta["tipo"] in TIPOS_DE_ALERTA
        assert alerta["base"]
        assert alerta["gravidade"] in ("media", "alta")


def test_atraso_no_cronograma_vira_alerta():
    entradas = cadeia()
    dias = planejados(entradas)
    painel = rodar(entradas, historico_frequencia=frequencia(dias[:1]))
    atrasos = [a for a in painel["alertas"] if a["tipo"] == "atraso_no_cronograma"]

    assert atrasos
    assert painel["desvio_do_planejado"]["aderencia_aos_dias"] < 1 - ATRASO_RELEVANTE


def test_cronograma_em_dia_nao_gera_alerta_de_atraso():
    entradas = cadeia()
    painel = rodar(entradas, historico_frequencia=frequencia(planejados(entradas)))

    assert not any(a["tipo"] == "atraso_no_cronograma" for a in painel["alertas"])


def test_conteudo_critico_do_agente_18_vira_alerta():
    painel = rodar(cadeia())
    criticos = [a for a in painel["alertas"] if a["tipo"] == "conteudo_critico"]

    assert criticos
    assert criticos[0]["base"] == "classificação do agente 18"


def test_nota_prevista_abaixo_do_corte_vira_alerta():
    entradas = cadeia()
    entradas["saidas_anteriores"]["16"] = {
        "estatisticas_previstas": {"acerto_previsto": 0.4}
    }
    painel = rodar(entradas, nota_corte=70)
    risco = [a for a in painel["alertas"] if a["tipo"] == "risco_na_nota"]

    assert risco
    assert risco[0]["gravidade"] == "alta"
    assert "agente 22" in risco[0]["base"]


def test_sem_nota_de_corte_nao_ha_alerta_de_nota():
    entradas = cadeia()
    entradas["saidas_anteriores"]["16"] = {
        "estatisticas_previstas": {"acerto_previsto": 0.2}
    }
    painel = rodar(entradas)

    assert not any(a["tipo"] == "risco_na_nota" for a in painel["alertas"])


# --------------------------------------------------------------------------- #
# Desempenho por nível
# --------------------------------------------------------------------------- #


def test_desempenho_desce_ate_o_microtopico():
    entradas = cadeia({"subtopicos": {"Crase": ["Crase antes de artigo"]}})
    painel = rodar(entradas)
    disciplinas = painel["desempenho_por_nivel"]["disciplinas"]

    assert disciplinas
    topicos = [t for d in disciplinas for m in d["modulos"] for t in m["topicos"]]
    assert topicos
    assert all("microtopicos" in t for t in topicos)
    assert any(t["microtopicos"] for t in topicos)


def test_taxa_por_topico_vem_do_historico():
    painel = rodar(cadeia())
    topicos = [
        t
        for d in painel["desempenho_por_nivel"]["disciplinas"]
        for m in d["modulos"]
        for t in m["topicos"]
    ]
    crase = next(t for t in topicos if t["nome"] == "Crase")

    assert crase["taxa_de_acertos"] == 0.95
    assert crase["questoes"] == 20
    assert crase["classificacao"] == "avancado"


def test_topico_sem_medicao_fica_indeterminado():
    painel = rodar(cadeia())
    topicos = [
        t
        for d in painel["desempenho_por_nivel"]["disciplinas"]
        for m in d["modulos"]
        for t in m["topicos"]
    ]
    ortografia = next(t for t in topicos if t["nome"] == "Ortografia")

    assert ortografia["classificacao"] == "indeterminado"
    assert ortografia["taxa_de_acertos"] is None


# --------------------------------------------------------------------------- #
# Insumos para o agente 22
# --------------------------------------------------------------------------- #


def test_metricas_para_previsao_sao_insumo_e_nao_previsao():
    painel = rodar(cadeia())
    metricas = painel["metricas_para_previsao"]

    assert metricas["destinatario"] == "22"
    assert "não projeta desempenho futuro" in metricas["base"]
    assert metricas["igp"] == painel["resumo_geral"]["indice_geral_de_performance"]["valor"]
    assert "previsao" not in painel
    assert "probabilidade_de_aprovacao" not in painel


# --------------------------------------------------------------------------- #
# Limites do agente
# --------------------------------------------------------------------------- #


def test_painel_nao_carrega_cronograma_nem_conteudo():
    painel = rodar(cadeia())

    proibidos = ("cronograma", "sessoes", "exercicios", "aula", "plano_de_estudos")
    assert not set(painel) & set(proibidos)


def test_tempo_previsto_do_simulado_e_declarado_como_previsto():
    entradas = cadeia()
    entradas["saidas_anteriores"]["16"] = {
        "resumo_geral": {"tempo_previsto_min": 100, "numero_de_questoes": 40}
    }
    painel = rodar(entradas)
    tempo = painel["indicadores_academicos"]["tempo_medio_por_questao_min"]

    assert tempo["valor"] == 2.5
    assert "não medido" in tempo["base"]
    assert tempo["origem"] == "agente 16"


def test_tempo_real_tem_precedencia_sobre_o_previsto():
    entradas = cadeia({"resultados_exercicios": [acertos("Crase", 8, 10, minutos=30)]})
    entradas["saidas_anteriores"]["16"] = {
        "resumo_geral": {"tempo_previsto_min": 100, "numero_de_questoes": 40}
    }
    painel = rodar(entradas)
    tempo = painel["indicadores_academicos"]["tempo_medio_por_questao_min"]

    assert tempo["valor"] == 3.0
    assert tempo["origem"] == "histórico do estudante"


def test_constantes_sao_declaradas():
    constantes = rodar(cadeia())["constantes_aplicadas"]

    assert constantes["pesos_do_igp"] == PESOS_DO_IGP
    assert constantes["valor_por_classificacao"] == VALOR_POR_CLASSIFICACAO
    assert constantes["minimo_de_questoes"] == MINIMO_DE_QUESTOES


# --------------------------------------------------------------------------- #
# Orquestrador
# --------------------------------------------------------------------------- #


async def test_orquestrador_executa_o_21_depois_do_20():
    resultado = await MasterOrchestrator().orquestrar(
        "como está meu desempenho",
        dados_usuario={
            "objetivo": "Passar no concurso fiscal",
            "edital": EDITAL,
            "escolaridade": "Superior completo",
            "horas_por_dia": 2,
            "dias_por_semana": 5,
            "data_prova": "2026-09-01",
            **HISTORICO,
        },
    )
    ordem = [sorted(onda) for onda in resultado.ondas]
    posicao = {agente: indice for indice, onda in enumerate(ordem) for agente in onda}

    assert posicao["21"] > posicao["20"] > posicao["19"]
    painel = resultado.saidas["21"].conteudo
    assert painel["resumo_geral"]["indice_geral_de_performance"]["valor"] is not None
