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
from app.studyos.agentes.otimizacao import (
    ALAVANCA_POR_CATEGORIA,
    CATEGORIAS,
    ESTRATEGIA_POR_TIPO_DE_ERRO,
    LIMIAR_DE_ADERENCIA,
    LIMIAR_DE_RETENCAO,
    MINIMO_DE_ERROS_DO_TIPO,
    ORDEM_DE_PRIORIDADE,
    PESOS_DA_EFICIENCIA,
    otimizar,
)
from app.studyos.agentes.perfil import analisar as analisar_perfil
from app.studyos.agentes.performance import analisar as analisar_performance
from app.studyos.agentes.previsao import prever
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


def cadeia(dados=None, frequencia=None, erros=None):
    """Roda a cadeia real até o 22 e devolve as entradas prontas para o 23."""
    base = {
        "objetivo": "Passar no concurso fiscal",
        "edital": EDITAL,
        "escolaridade": "Superior completo",
        "horas_por_dia": 2,
        "dias_por_semana": 5,
        "data_prova": "2026-09-01",
        "nota_corte": 70,
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

    if frequencia is not None:
        base = {**base, "historico_frequencia": frequencia}
    if erros is not None:
        base = {**base, "erros": erros}

    entradas = {"solicitacao": "", "dados_usuario": base, "saidas_anteriores": ant}
    ant["12"] = detectar(entradas, hoje=HOJE)
    ant["17"] = analisar_erros(entradas, hoje=HOJE)
    ant["18"] = mapear_fraquezas(entradas, hoje=HOJE)
    ant["19"] = acompanhar(entradas, hoje=HOJE)
    ant["20"] = construir_habitos(entradas, hoje=HOJE)
    ant["21"] = analisar_performance(entradas, hoje=HOJE)
    ant["22"] = prever(entradas, hoje=HOJE)
    return entradas


def planejados(entradas):
    return [
        date.fromisoformat(d["data"])
        for d in entradas["saidas_anteriores"]["06"]["cronograma"]
        if date.fromisoformat(d["data"]) <= HOJE
    ]


def sessoes(datas, minutos=90):
    return [{"data": d.isoformat(), "minutos": minutos} for d in datas]


def rodar(entradas):
    return otimizar(entradas, hoje=HOJE)


def de_categoria(plano, categoria):
    return [o for o in plano["otimizacoes_recomendadas"] if o["categoria"] == categoria]


# --------------------------------------------------------------------------- #
# Nunca modificar, sempre pedir
# --------------------------------------------------------------------------- #


def test_toda_otimizacao_exige_aprovacao():
    """A saída é um pedido, não um ato."""
    entradas = cadeia()
    plano = rodar(entradas)

    assert plano["otimizacoes_recomendadas"]
    for otimizacao in plano["otimizacoes_recomendadas"]:
        assert otimizacao["aprovacao_necessaria"] is True


def test_cada_otimizacao_vira_solicitacao_ao_orquestrador():
    plano = rodar(cadeia())
    solicitacoes = plano["solicitacoes_de_atualizacao"]

    assert len(solicitacoes) == len(plano["otimizacoes_recomendadas"])
    for solicitacao in solicitacoes:
        assert solicitacao["destinatario"] == "Master Orchestrator"
        assert solicitacao["status"] == "aguardando_aprovacao"
        assert solicitacao["agentes_a_reexecutar"]
        assert "não modifica nenhum outro" in solicitacao["base"]


def test_saida_nao_carrega_estrutura_executavel():
    """Nenhum cronograma, nenhuma árvore, nenhuma sessão."""
    plano = rodar(cadeia())

    proibidos = (
        "cronograma", "arvore", "disciplinas", "sessoes", "exercicios", "aula",
        "plano_de_estudos", "nos",
    )
    assert not set(plano) & set(proibidos)


def test_observacao_declara_que_nada_foi_aplicado():
    plano = rodar(cadeia())

    assert any("Nenhuma alteração foi aplicada" in o for o in plano["observacoes"])
    assert plano["consumido_por"] == ["24", "Master Orchestrator"]


# --------------------------------------------------------------------------- #
# Sem evidência não há otimização
# --------------------------------------------------------------------------- #


def test_sem_dado_nenhuma_otimizacao_e_proposta():
    """Ausência de proposta não é ausência de problema — é ausência de dado."""
    plano = otimizar({"dados_usuario": {}, "saidas_anteriores": {}}, hoje=HOJE)

    assert plano["otimizacoes_recomendadas"] == []
    assert plano["solicitacoes_de_atualizacao"] == []
    assert plano["resumo_geral"]["indice_geral_de_eficiencia"]["valor"] is None
    assert any("ausência de dado que o comprove" in o for o in plano["observacoes"])
    assert plano["lacunas"] == [
        "painel_de_performance_do_agente_21",
        "relatorio_de_previsao_do_agente_22",
    ]


def test_toda_otimizacao_lista_evidencias_com_origem():
    plano = rodar(cadeia())

    for otimizacao in plano["otimizacoes_recomendadas"]:
        assert otimizacao["evidencias"]
        for evidencia in otimizacao["evidencias"]:
            assert set(evidencia) == {"indicador", "valor", "origem"}
            assert evidencia["valor"] not in (None, "", [], {})
            assert evidencia["origem"]


def test_categoria_e_gravidade_saem_do_vocabulario_declarado():
    plano = rodar(cadeia())

    for otimizacao in plano["otimizacoes_recomendadas"]:
        assert otimizacao["categoria"] in CATEGORIAS
        assert otimizacao["gravidade"] in ORDEM_DE_PRIORIDADE


# --------------------------------------------------------------------------- #
# Detectores
# --------------------------------------------------------------------------- #


def test_aderencia_baixa_vira_otimizacao_de_cronograma():
    entradas = cadeia()
    dias = planejados(entradas)
    entradas = cadeia(frequencia=sessoes(dias[:2]))
    plano = rodar(entradas)
    achados = de_categoria(plano, "cronograma")

    assert achados
    aderencia = entradas["saidas_anteriores"]["21"]["desvio_do_planejado"][
        "aderencia_aos_dias"
    ]
    assert aderencia < LIMIAR_DE_ADERENCIA
    assert "06" in achados[0]["agentes_afetados"]
    assert "20" in achados[0]["agentes_afetados"]


def test_aderencia_boa_nao_gera_otimizacao_de_cronograma():
    entradas = cadeia()
    plano = rodar(cadeia(frequencia=sessoes(planejados(entradas))))

    assert de_categoria(plano, "cronograma") == []


def test_retencao_baixa_sem_revisao_vira_otimizacao():
    entradas = cadeia(
        {
            "resultados_exercicios": [
                acertos("Crase", 19, 20, quando=date(2025, 9, 1)),
                acertos("Sintaxe", 6, 10),
            ]
        }
    )
    plano = rodar(entradas)
    achados = de_categoria(plano, "baixa_retencao")

    assert achados
    retencao = next(
        e["valor"] for e in achados[0]["evidencias"] if e["indicador"] == "retencao_estimada"
    )
    assert retencao < LIMIAR_DE_RETENCAO
    assert achados[0]["agentes_afetados"] == ["14", "15"]


def test_conteudo_ja_agendado_para_revisao_nao_vira_otimizacao():
    entradas = cadeia(
        {
            "resultados_exercicios": [
                acertos("Crase", 19, 20, quando=date(2025, 9, 1)),
                acertos("Sintaxe", 6, 10),
            ]
        }
    )
    entradas["saidas_anteriores"]["15"] = {
        "sessoes": [{"conteudos": [{"topico": "Crase"}]}]
    }
    plano = rodar(entradas)

    assert not any(
        "Crase" in o["problema"] for o in de_categoria(plano, "baixa_retencao")
    )


def test_erro_recorrente_do_mesmo_tipo_muda_a_estrategia_didatica():
    erros = [
        {"topico": "Sintaxe", "disciplina": "Português", "tipo": "calculo"}
        for _ in range(MINIMO_DE_ERROS_DO_TIPO)
    ]
    plano = rodar(cadeia(erros=erros))
    achados = de_categoria(plano, "estrategia_didatica")

    assert achados
    assert achados[0]["acao"] == ESTRATEGIA_POR_TIPO_DE_ERRO["calculo"]["acao"]
    assert achados[0]["agentes_afetados"] == [
        ESTRATEGIA_POR_TIPO_DE_ERRO["calculo"]["agente"]
    ]


def test_poucos_erros_nao_mudam_a_estrategia():
    erros = [{"topico": "Sintaxe", "tipo": "calculo"}] * (MINIMO_DE_ERROS_DO_TIPO - 1)
    plano = rodar(cadeia(erros=erros))

    assert de_categoria(plano, "estrategia_didatica") == []


def test_gargalo_do_grafo_tem_gravidade_critica():
    entradas = cadeia({"pre_requisitos": {"Probabilidade": ["Conjuntos"]}})
    plano = rodar(entradas)
    achados = de_categoria(plano, "gargalo")

    assert achados
    assert achados[0]["gravidade"] == "critica"
    assert "Conjuntos" in achados[0]["problema"]
    assert plano["resumo_geral"]["gargalos_identificados"]


def test_revisao_nao_alocada_vira_otimizacao():
    entradas = cadeia()
    entradas["saidas_anteriores"]["15"] = {
        "conteudos_nao_alocados": [{"topico": "Sintaxe"}],
        "indicadores": {"cobertura_das_revisoes": 0.5},
    }
    plano = rodar(entradas)
    achados = de_categoria(plano, "revisao")

    assert achados
    assert "sem sessão" in achados[0]["problema"]
    assert "15" in achados[0]["agentes_afetados"]


def test_conteudo_pronto_para_avancar_vira_aceleracao():
    plano = rodar(cadeia())
    achados = de_categoria(plano, "aceleracao")

    assert achados
    assert any("avançar" in o["problema"] for o in achados)


# --------------------------------------------------------------------------- #
# O ganho vem do agente 22
# --------------------------------------------------------------------------- #


def test_ganho_estimado_e_o_numero_do_agente_22():
    """Dois agentes prometendo ganhos diferentes seria pior que nenhum número."""
    entradas = cadeia()
    entradas = cadeia(frequencia=sessoes(planejados(entradas)[:2]))
    plano = rodar(entradas)
    cronograma = de_categoria(plano, "cronograma")[0]
    simulacoes = entradas["saidas_anteriores"]["22"]["simulacoes"]
    alavanca = next(
        s for s in simulacoes if s["acao"] == ALAVANCA_POR_CATEGORIA["cronograma"]
    )

    assert cronograma["impacto_esperado"]["origem"] == "agente 22"
    assert cronograma["impacto_esperado"]["ganho_na_probabilidade"] == (
        alavanca["impacto_na_probabilidade"]
    )


def test_categoria_sem_alavanca_nao_inventa_ganho():
    plano = rodar(cadeia())
    aceleracao = de_categoria(plano, "aceleracao")

    assert aceleracao
    assert aceleracao[0]["impacto_esperado"] is None


def test_ganho_potencial_nao_soma_alavancas():
    entradas = cadeia()
    plano = rodar(cadeia(frequencia=sessoes(planejados(entradas)[:2])))
    ganho = plano["resumo_geral"]["ganho_potencial_estimado"]
    individuais = [
        (o["impacto_esperado"] or {}).get("ganho_na_probabilidade")
        for o in plano["otimizacoes_recomendadas"]
    ]
    medidos = [g for g in individuais if g is not None]

    assert ganho["estimativa"] == round(max(medidos), 4)
    assert "não são somados" in ganho["base"]


def test_sem_o_agente_22_o_impacto_nao_e_estimado():
    entradas = cadeia()
    entradas["saidas_anteriores"].pop("22")
    plano = rodar(entradas)

    for otimizacao in plano["otimizacoes_recomendadas"]:
        assert otimizacao["impacto_esperado"] is None
    assert any("não estimou impacto por conta própria" in o for o in plano["observacoes"])


# --------------------------------------------------------------------------- #
# Índice Geral de Eficiência
# --------------------------------------------------------------------------- #


def test_eficiencia_declara_componentes_e_origem():
    entradas = cadeia()
    plano = rodar(cadeia(frequencia=sessoes(planejados(entradas))))
    eficiencia = plano["resumo_geral"]["indice_geral_de_eficiencia"]

    assert eficiencia["componentes"]
    for nome, componente in eficiencia["componentes"].items():
        assert nome in PESOS_DA_EFICIENCIA
        assert componente["base"] and componente["origem"]


def test_componente_ausente_redistribui_o_peso():
    entradas = cadeia()
    plano = rodar(cadeia(frequencia=sessoes(planejados(entradas))))
    eficiencia = plano["resumo_geral"]["indice_geral_de_eficiencia"]
    componentes = eficiencia["componentes"]

    esperado = sum(
        PESOS_DA_EFICIENCIA[c] * d["valor"] for c, d in componentes.items()
    ) / sum(PESOS_DA_EFICIENCIA[c] for c in componentes)
    assert eficiencia["valor"] == round(esperado, 4)


def test_mais_horas_cumpridas_produzem_eficiencia_maior():
    entradas = cadeia()
    dias = planejados(entradas)
    pouco = rodar(cadeia(frequencia=sessoes(dias[:2])))
    muito = rodar(cadeia(frequencia=sessoes(dias)))

    assert (
        muito["resumo_geral"]["indice_geral_de_eficiencia"]["valor"]
        > pouco["resumo_geral"]["indice_geral_de_eficiencia"]["valor"]
    )


# --------------------------------------------------------------------------- #
# Priorização e plano de execução
# --------------------------------------------------------------------------- #


def test_otimizacoes_ordenam_por_gravidade():
    entradas = cadeia({"pre_requisitos": {"Probabilidade": ["Conjuntos"]}})
    plano = rodar(entradas)
    ordem = {nome: indice for indice, nome in enumerate(ORDEM_DE_PRIORIDADE)}
    graus = [ordem[o["gravidade"]] for o in plano["otimizacoes_recomendadas"]]

    assert graus == sorted(graus)
    assert [o["prioridade"] for o in plano["otimizacoes_recomendadas"]] == list(
        range(1, len(plano["otimizacoes_recomendadas"]) + 1)
    )


def test_cada_passo_tem_criterio_de_sucesso_e_metrica():
    plano = rodar(cadeia())

    for passo in plano["plano_de_execucao"]["passos"]:
        assert passo["criterio_de_sucesso"]
        assert passo["metrica_de_validacao"]["metrica"]
        assert passo["metrica_de_validacao"]["medida_por"]


def test_otimizacoes_no_mesmo_agente_sao_encadeadas():
    """Duas mudanças no mesmo agente não são independentes."""
    entradas = cadeia({"pre_requisitos": {"Probabilidade": ["Conjuntos"]}})
    plano = rodar(entradas)
    passos = plano["plano_de_execucao"]["passos"]

    for indice, passo in enumerate(passos):
        for anterior in passos[:indice]:
            if set(anterior["agentes_afetados"]) & set(passo["agentes_afetados"]):
                assert anterior["id"] in passo["depende_de"]


def test_analise_de_impacto_declara_a_base_de_cada_numero():
    plano = rodar(cadeia())
    impacto = plano["analise_de_impacto"]

    for chave in (
        "ganho_na_probabilidade",
        "reducao_no_tempo_de_estudo",
        "aumento_da_retencao",
        "melhoria_no_desempenho",
        "reducao_de_riscos",
    ):
        assert impacto[chave]["base"]


def test_constantes_sao_declaradas():
    constantes = rodar(cadeia())["constantes_aplicadas"]

    assert constantes["pesos_da_eficiencia"] == PESOS_DA_EFICIENCIA
    assert constantes["limiar_de_retencao"] == LIMIAR_DE_RETENCAO
    assert constantes["alavanca_por_categoria"] == ALAVANCA_POR_CATEGORIA
    assert constantes["categorias"] == CATEGORIAS


# --------------------------------------------------------------------------- #
# Orquestrador
# --------------------------------------------------------------------------- #


async def test_orquestrador_executa_o_23_depois_do_22():
    resultado = await MasterOrchestrator().orquestrar(
        "como posso otimizar meus estudos",
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

    assert posicao["23"] > posicao["22"] > posicao["21"]
    plano = resultado.saidas["23"].conteudo
    for solicitacao in plano["solicitacoes_de_atualizacao"]:
        assert solicitacao["status"] == "aguardando_aprovacao"
