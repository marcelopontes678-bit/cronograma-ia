from datetime import date, timedelta

import pytest

from app.studyos.agentes.conhecimento import analisar as analisar_conhecimento
from app.studyos.agentes.curriculo import construir as construir_curriculo
from app.studyos.agentes.dependencias import mapear as mapear_dependencias
from app.studyos.agentes.dificuldade import detectar
from app.studyos.agentes.erros import analisar as analisar_erros
from app.studyos.agentes.fraquezas import mapear as mapear_fraquezas
from app.studyos.agentes.objetivo import analisar as analisar_objetivo
from app.studyos.agentes.perfil import analisar as analisar_perfil
from app.studyos.agentes.performance import analisar as analisar_performance
from app.studyos.agentes.previsao import (
    ALAVANCAS,
    AVISO,
    CENARIOS,
    DELTA_POR_CENARIO,
    FAIXAS_DA_PAO,
    GANHO_MAXIMO_EXTRAPOLADO,
    LARGURA_DO_INTERVALO,
    MINIMO_DE_COMPONENTES,
    PAO_MAXIMA,
    PESOS_DA_PAO,
    TERMOS_DE_CERTEZA,
    PrevisaoComoCerteza,
    _validar_texto,
    prever,
)
from app.studyos.agentes.roadmap import construir as construir_roadmap
from app.studyos.orchestrator import MasterOrchestrator

INICIO_DO_PLANO = date(2026, 3, 2)
HOJE = INICIO_DO_PLANO + timedelta(days=12)

EDITAL = {
    "Estatística": {"questoes": 10, "topicos": ["Conjuntos", "Probabilidade"]},
    "Português": {"questoes": 20, "topicos": ["Crase", "Sintaxe", "Ortografia", "Verbos"]},
}


def acertos(topico, certos, total, disciplina="Português", quando=None):
    return {
        "disciplina": disciplina,
        "topico": topico,
        "acertos": certos,
        "total": total,
        "data": (quando or HOJE).isoformat(),
    }


HISTORICO = [
    acertos("Crase", 19, 20),
    acertos("Sintaxe", 6, 10),
    acertos("Conjuntos", 3, 10, disciplina="Estatística"),
    acertos("Probabilidade", 7, 10, disciplina="Estatística"),
]


def cadeia(dados=None, com_painel=True):
    """Roda a cadeia real até o 21 e devolve as entradas prontas para o 22."""
    base = {
        "objetivo": "Passar no concurso fiscal",
        "edital": EDITAL,
        "escolaridade": "Superior completo",
        "horas_por_dia": 2,
        "dias_por_semana": 5,
        "data_prova": "2026-09-01",
        "resultados_exercicios": HISTORICO,
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
    if com_painel:
        ant["21"] = analisar_performance(entradas, hoje=HOJE)
    return entradas


def planejados(entradas):
    return [
        date.fromisoformat(d["data"])
        for d in entradas["saidas_anteriores"]["06"]["cronograma"]
        if date.fromisoformat(d["data"]) <= HOJE
    ]


def com_frequencia(entradas, datas, **campos):
    """Recomputa o painel com a frequência informada, como no fluxo real."""
    dados = {
        **entradas["dados_usuario"],
        "historico_frequencia": [
            {"data": d.isoformat(), "minutos": 90} for d in datas
        ],
        **campos,
    }
    contexto = {**entradas, "dados_usuario": dados}
    contexto["saidas_anteriores"]["21"] = analisar_performance(contexto, hoje=HOJE)
    return contexto


def rodar(entradas, **campos):
    dados = {**entradas["dados_usuario"], **campos}
    return prever({**entradas, "dados_usuario": dados}, hoje=HOJE)


# --------------------------------------------------------------------------- #
# Nunca apresentar previsão como certeza
# --------------------------------------------------------------------------- #


def test_toda_projecao_sai_com_intervalo_e_confianca():
    """Nenhuma projeção sai como número solto."""
    relatorio = rodar(cadeia())
    evolucao = relatorio["resumo_geral"]["evolucao_prevista"]

    for chave in ("cobertura_projetada", "acerto_projetado"):
        estimativa = evolucao[chave]
        assert set(estimativa) >= {"estimativa", "intervalo", "confianca", "base", "natureza"}
        assert estimativa["natureza"] == "estimativa"
        if estimativa["estimativa"] is not None:
            inferior, superior = estimativa["intervalo"]
            assert inferior <= estimativa["estimativa"] <= superior


def test_pao_tambem_carrega_intervalo():
    relatorio = rodar(cadeia())
    pao = relatorio["resumo_geral"]["probabilidade_de_atingir_o_objetivo"]

    assert pao["natureza"] == "estimativa"
    assert pao["intervalo"] is not None
    assert pao["nivel"] in [nome for _, nome in FAIXAS_DA_PAO] + [PAO_MAXIMA]


def test_intervalo_alarga_quando_a_confianca_cai():
    relatorio = rodar(cadeia())
    pao = relatorio["resumo_geral"]["probabilidade_de_atingir_o_objetivo"]
    largura = LARGURA_DO_INTERVALO[pao["confianca"]]

    assert pao["intervalo"][1] - pao["intervalo"][0] <= 2 * largura + 1e-9
    assert LARGURA_DO_INTERVALO["baixa"] > LARGURA_DO_INTERVALO["media"]
    assert LARGURA_DO_INTERVALO["media"] > LARGURA_DO_INTERVALO["alta"]


def test_aviso_acompanha_o_relatorio():
    relatorio = rodar(cadeia())

    assert relatorio["aviso"] == AVISO
    assert relatorio["observacoes"][0] == AVISO
    assert "não são garantia de resultado" in AVISO.lower()


@pytest.mark.parametrize("termo", TERMOS_DE_CERTEZA)
def test_texto_que_promete_resultado_e_recusado(termo):
    with pytest.raises(PrevisaoComoCerteza):
        _validar_texto(f"Mantendo o ritmo, {termo}.")


def test_nenhum_texto_emitido_promete_resultado():
    relatorio = rodar(cadeia())

    textos = [relatorio["aviso"]]
    for cenario in relatorio["cenarios"].values():
        textos.extend(cenario["condicoes_necessarias"])
    textos.extend(s["descricao"] for s in relatorio["simulacoes"])

    for texto in textos:
        _validar_texto(texto)
    assert relatorio["textos_recusados"] == []


def test_confianca_nao_depende_do_resultado():
    relatorio = rodar(cadeia())
    resumo = relatorio["resumo_geral"]

    assert "não depende do resultado projetado" in resumo["base_da_confianca"]
    assert resumo["nivel_de_confianca"] == (
        resumo["probabilidade_de_atingir_o_objetivo"]["confianca"]
    )


# --------------------------------------------------------------------------- #
# Nunca utilizar dados inexistentes
# --------------------------------------------------------------------------- #


def test_sem_insumo_a_pao_nao_e_calculada():
    relatorio = prever({"dados_usuario": {}, "saidas_anteriores": {}}, hoje=HOJE)
    pao = relatorio["resumo_geral"]["probabilidade_de_atingir_o_objetivo"]

    assert pao["estimativa"] is None
    assert pao["nivel"] == "indeterminada"
    assert str(MINIMO_DE_COMPONENTES) in pao["base"]
    assert "painel_de_performance_do_agente_21" in relatorio["lacunas"]


def test_componente_ausente_redistribui_o_peso():
    relatorio = rodar(cadeia())
    pao = relatorio["resumo_geral"]["probabilidade_de_atingir_o_objetivo"]
    componentes = pao["componentes"]

    esperado = sum(
        PESOS_DA_PAO[c] * d["valor"] for c, d in componentes.items()
    ) / sum(PESOS_DA_PAO[c] for c in componentes)
    assert pao["estimativa"] == round(esperado, 4)
    assert any("sem dado para" in o for o in relatorio["observacoes"])


def test_sem_data_alvo_a_cobertura_nao_e_projetada():
    entradas = cadeia()
    entradas["saidas_anteriores"]["02"]["prazo_final"] = {}
    relatorio = rodar(entradas, data_prova=None)
    evolucao = relatorio["resumo_geral"]["evolucao_prevista"]

    assert evolucao["cobertura_projetada"]["estimativa"] is None
    assert "não projetada" in evolucao["cobertura_projetada"]["base"]
    assert any("não tem horizonte" in o for o in relatorio["observacoes"])
    assert "data_alvo" in relatorio["lacunas"]


def test_alavanca_sem_dado_declara_que_nao_pode_simular():
    relatorio = rodar(cadeia())
    retencao = next(
        s for s in relatorio["simulacoes"] if s["acao"] == "aumento_da_retencao"
    )

    assert retencao["impacto_na_probabilidade"] is None
    assert "não foi medido" in retencao["base"]


# --------------------------------------------------------------------------- #
# Um modelo só
# --------------------------------------------------------------------------- #


def test_cenarios_saem_do_mesmo_modelo_e_se_ordenam():
    entradas = com_frequencia(cadeia(), planejados(cadeia())[:8], nota_corte=70)
    relatorio = prever(entradas, hoje=HOJE)
    cenarios = relatorio["cenarios"]

    assert set(cenarios) == set(CENARIOS)
    otimista = cenarios["otimista"]["probabilidade"]["estimativa"]
    esperado = cenarios["esperado"]["probabilidade"]["estimativa"]
    pessimista = cenarios["pessimista"]["probabilidade"]["estimativa"]
    assert otimista >= esperado >= pessimista


def test_cenario_esperado_nao_aplica_correcao_nenhuma():
    """O esperado é o estado como está, sem "bom senso" embutido."""
    entradas = com_frequencia(cadeia(), planejados(cadeia())[:8], nota_corte=70)
    relatorio = prever(entradas, hoje=HOJE)

    assert DELTA_POR_CENARIO["esperado"] == {"aderencia": 0.0, "acerto": 0.0}
    assert relatorio["cenarios"]["esperado"]["probabilidade"]["estimativa"] == (
        relatorio["resumo_geral"]["probabilidade_de_atingir_o_objetivo"]["estimativa"]
    )


def test_cada_cenario_declara_o_delta_e_as_condicoes():
    relatorio = rodar(cadeia())

    for nome, cenario in relatorio["cenarios"].items():
        assert cenario["delta_aplicado"] == DELTA_POR_CENARIO[nome]
        assert cenario["condicoes_necessarias"]


def test_condicoes_do_esperado_sao_manter_o_atual():
    relatorio = rodar(cadeia())

    assert relatorio["cenarios"]["esperado"]["condicoes_necessarias"] == [
        "manter o comportamento atual"
    ]


# --------------------------------------------------------------------------- #
# A extrapolação tem teto
# --------------------------------------------------------------------------- #


def test_tendencia_forte_nao_projeta_gabaritar_a_prova():
    """Um modelo que projeta 100% de acerto não está prevendo, está torcendo."""
    registros = [
        acertos("Crase", 8, 20, quando=HOJE - timedelta(days=40)),
        acertos("Crase", 19, 20, quando=HOJE - timedelta(days=3)),
    ]
    entradas = cadeia({"resultados_exercicios": registros})
    relatorio = rodar(entradas)
    acerto = relatorio["resumo_geral"]["evolucao_prevista"]["acerto_projetado"]
    atual = entradas["saidas_anteriores"]["21"]["metricas_para_previsao"]["taxa_de_acertos"]

    assert acerto["estimativa"] <= atual + GANHO_MAXIMO_EXTRAPOLADO + 1e-9
    assert "teto" in acerto["base"]


def test_sem_tendencia_o_acerto_e_mantido_e_nao_extrapolado():
    relatorio = rodar(cadeia())
    acerto = relatorio["resumo_geral"]["evolucao_prevista"]["acerto_projetado"]

    assert "mantido" in acerto["base"]
    assert any("em vez de extrapolado" in o for o in relatorio["observacoes"])


def test_queda_tambem_respeita_o_teto():
    registros = [
        acertos("Crase", 19, 20, quando=HOJE - timedelta(days=40)),
        acertos("Crase", 4, 20, quando=HOJE - timedelta(days=3)),
    ]
    entradas = cadeia({"resultados_exercicios": registros})
    relatorio = rodar(entradas)
    acerto = relatorio["resumo_geral"]["evolucao_prevista"]["acerto_projetado"]
    atual = entradas["saidas_anteriores"]["21"]["metricas_para_previsao"]["taxa_de_acertos"]

    assert acerto["estimativa"] >= atual - GANHO_MAXIMO_EXTRAPOLADO - 1e-9


# --------------------------------------------------------------------------- #
# Alavancas
# --------------------------------------------------------------------------- #


def test_alavancas_usam_o_mesmo_modelo_com_delta_declarado():
    entradas = com_frequencia(cadeia(), planejados(cadeia())[:8], nota_corte=70)
    relatorio = prever(entradas, hoje=HOJE)

    for simulacao in relatorio["simulacoes"]:
        assert simulacao["acao"] in ALAVANCAS
        if simulacao["impacto_na_probabilidade"] is not None:
            assert simulacao["delta_aplicado"] == ALAVANCAS[simulacao["acao"]]["delta"]
            assert "mesma projeção" in simulacao["base"]


def test_melhorar_a_consistencia_aumenta_a_probabilidade():
    entradas = com_frequencia(cadeia(), planejados(cadeia())[:5], nota_corte=70)
    relatorio = prever(entradas, hoje=HOJE)
    consistencia = next(
        s for s in relatorio["simulacoes"] if s["acao"] == "melhora_na_consistencia"
    )

    assert consistencia["impacto_na_probabilidade"] > 0
    assert consistencia["probabilidade_resultante"] > (
        relatorio["resumo_geral"]["probabilidade_de_atingir_o_objetivo"]["estimativa"]
    )


def test_simulacoes_ordenam_por_impacto():
    entradas = com_frequencia(cadeia(), planejados(cadeia())[:5], nota_corte=70)
    relatorio = prever(entradas, hoje=HOJE)
    impactos = [
        s["impacto_na_probabilidade"]
        for s in relatorio["simulacoes"]
        if s["impacto_na_probabilidade"] is not None
    ]

    assert impactos == sorted(impactos, reverse=True)


def test_prioridade_maxima_e_a_alavanca_de_maior_impacto():
    entradas = com_frequencia(cadeia(), planejados(cadeia())[:5], nota_corte=70)
    relatorio = prever(entradas, hoje=HOJE)
    prioridade = relatorio["recomendacoes"]["prioridade_maxima"]
    melhor = next(
        s for s in relatorio["simulacoes"] if s["impacto_na_probabilidade"]
    )

    assert prioridade["acao"] == melhor["acao"]
    assert prioridade["impacto_estimado"] == melhor["impacto_na_probabilidade"]


def test_recomendacao_aponta_o_agente_23_como_executor():
    relatorio = rodar(cadeia())
    recomendacoes = relatorio["recomendacoes"]

    assert recomendacoes["executor"] == "23"
    assert "quem reorganiza o plano é o agente 23" in recomendacoes["base"]


# --------------------------------------------------------------------------- #
# Fatores
# --------------------------------------------------------------------------- #


def test_fatores_de_risco_vem_dos_alertas_do_painel():
    entradas = com_frequencia(cadeia(), planejados(cadeia())[:2])
    relatorio = prever(entradas, hoje=HOJE)
    alertas = entradas["saidas_anteriores"]["21"]["alertas"]

    assert relatorio["fatores_de_risco"]
    detalhes = {r["risco"] for r in relatorio["fatores_de_risco"]}
    assert {a["detalhe"] for a in alertas} <= detalhes


def test_riscos_ordenam_por_gravidade():
    entradas = com_frequencia(cadeia(), planejados(cadeia())[:2])
    relatorio = prever(entradas, hoje=HOJE)
    ordem = {"alta": 0, "media": 1, "baixa": 2}
    graus = [ordem[r["gravidade"]] for r in relatorio["fatores_de_risco"]]

    assert graus == sorted(graus)


def test_todo_fator_declara_a_origem():
    entradas = com_frequencia(cadeia(), planejados(cadeia())[:8])
    relatorio = prever(entradas, hoje=HOJE)

    for fator in relatorio["fatores_positivos"] + relatorio["fatores_de_risco"]:
        assert fator["origem"]
        assert fator["base"]


def test_conteudo_dominado_entra_como_fator_positivo():
    relatorio = rodar(cadeia())
    positivos = [
        f for f in relatorio["fatores_positivos"] if "dominado" in f["fator"]
    ]

    assert positivos
    assert positivos[0]["origem"] == "agente 04"


# --------------------------------------------------------------------------- #
# Recalcular quando chegam dados novos
# --------------------------------------------------------------------------- #


def test_previsao_muda_quando_a_frequencia_muda():
    base = cadeia()
    ruim = prever(com_frequencia(base, planejados(base)[:2], nota_corte=70), hoje=HOJE)
    bom = prever(com_frequencia(cadeia(), planejados(base), nota_corte=70), hoje=HOJE)

    assert (
        bom["resumo_geral"]["probabilidade_de_atingir_o_objetivo"]["estimativa"]
        > ruim["resumo_geral"]["probabilidade_de_atingir_o_objetivo"]["estimativa"]
    )


# --------------------------------------------------------------------------- #
# Limites do agente
# --------------------------------------------------------------------------- #


def test_relatorio_nao_carrega_cronograma_nem_conteudo():
    relatorio = rodar(cadeia())

    proibidos = ("cronograma", "sessoes", "exercicios", "aula", "plano_de_estudos")
    assert not set(relatorio) & set(proibidos)


def test_constantes_sao_declaradas():
    constantes = rodar(cadeia())["constantes_aplicadas"]

    assert constantes["delta_por_cenario"] == DELTA_POR_CENARIO
    assert constantes["pesos_da_pao"] == PESOS_DA_PAO
    assert constantes["ganho_maximo_extrapolado"] == GANHO_MAXIMO_EXTRAPOLADO
    assert constantes["termos_de_certeza"] == TERMOS_DE_CERTEZA


# --------------------------------------------------------------------------- #
# Orquestrador
# --------------------------------------------------------------------------- #


async def test_orquestrador_executa_o_22_depois_do_21():
    resultado = await MasterOrchestrator().orquestrar(
        "qual a chance de eu passar",
        dados_usuario={
            "objetivo": "Passar no concurso fiscal",
            "edital": EDITAL,
            "escolaridade": "Superior completo",
            "horas_por_dia": 2,
            "dias_por_semana": 5,
            "data_prova": "2026-09-01",
            "nota_corte": 70,
            "resultados_exercicios": HISTORICO,
        },
    )
    ordem = [sorted(onda) for onda in resultado.ondas]
    posicao = {agente: indice for indice, onda in enumerate(ordem) for agente in onda}

    assert posicao["22"] > posicao["21"]
    relatorio = resultado.saidas["22"].conteudo
    assert relatorio["aviso"] == AVISO
    assert relatorio["resumo_geral"]["probabilidade_de_atingir_o_objetivo"]["natureza"] == (
        "estimativa"
    )
