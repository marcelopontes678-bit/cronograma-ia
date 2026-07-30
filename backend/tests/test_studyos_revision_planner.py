from datetime import date, timedelta

import pytest

from app.studyos.agentes.conhecimento import analisar as analisar_conhecimento
from app.studyos.agentes.curriculo import construir as construir_curriculo
from app.studyos.agentes.dependencias import mapear
from app.studyos.agentes.dificuldade import detectar
from app.studyos.agentes.memoria import agendar
from app.studyos.agentes.objetivo import analisar as analisar_objetivo
from app.studyos.agentes.perfil import analisar as analisar_perfil
from app.studyos.agentes.revisao import (
    CRITERIO_POR_METODO,
    MAXIMO_CRITICOS_POR_SESSAO,
    MAXIMO_MINUTOS_POR_SESSAO,
    planejar,
)
from app.studyos.agentes.roadmap import construir as construir_roadmap
from app.studyos.orchestrator import MasterOrchestrator

HOJE = date(2026, 1, 5)

EDITAL = {
    "Estatística": {"questoes": 10, "topicos": ["Conjuntos", "Probabilidade"]},
    "Português": {"questoes": 20, "topicos": ["Crase", "Sintaxe"]},
}


def cadeia(dados=None, extras=None):
    """Roda 01–06, 12 e 14 de verdade e devolve as entradas prontas para o 15."""
    base = {
        "objetivo": "Passar no concurso fiscal",
        "edital": EDITAL,
        "escolaridade": "Superior completo",
        "profissao": "Analista",
        "rotina": "Estudo em casa",
        "horas_por_dia": 4,
        "dias_por_semana": 5,
        "idade": 30,
        "experiencia_anterior": "nenhuma",
        "preferencia_estudo": "questões",
        "data_prova": "2026-06-01",
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
    m12 = detectar({"dados_usuario": base, "saidas_anteriores": ant}, hoje=HOJE)
    m14 = agendar(
        {"dados_usuario": base, "saidas_anteriores": {**ant, "12": m12, **(extras or {})}},
        hoje=HOJE,
    )
    return {
        "solicitacao": "",
        "dados_usuario": base,
        "saidas_anteriores": {**ant, "12": m12, "14": m14, **(extras or {})},
    }


def acertos(topico, certos, total, disciplina="Português", data=None):
    return {
        "disciplina": disciplina,
        "topico": topico,
        "acertos": certos,
        "total": total,
        "data": (data or HOJE).isoformat(),
    }


def revisao_em(topico, dias_atras, resultado="acerto"):
    return {
        "conteudo": topico,
        "data": (HOJE - timedelta(days=dias_atras)).isoformat(),
        "resultado": resultado,
    }


TODOS_ESTUDADOS = {
    "resultados_exercicios": [
        acertos("Crase", 9, 10),
        acertos("Sintaxe", 6, 10),
        acertos("Conjuntos", 2, 10, disciplina="Estatística"),
        acertos("Probabilidade", 8, 10, disciplina="Estatística"),
    ],
    "historico_revisoes": [
        revisao_em("Crase", 1),
        revisao_em("Sintaxe", 20),
        revisao_em("Conjuntos", 70),
        revisao_em("Probabilidade", 40),
    ],
}


# --------------------------------------------------------------------------- #
# Estrutura das sessões
# --------------------------------------------------------------------------- #


def test_sem_plano_do_agente_14_nao_ha_sessoes():
    plano = planejar({"dados_usuario": {}, "saidas_anteriores": {}}, hoje=HOJE)

    assert plano["sessoes"] == []
    assert plano["confiabilidade"] == "baixa"
    assert "plano_de_revisoes_do_agente_14" in plano["lacunas"]


def test_conteudo_nao_estudado_nao_chega_a_virar_sessao():
    plano = planejar(cadeia(), hoje=HOJE)

    assert plano["sessoes"] == []
    assert any("não estudado não entra em sessão" in o for o in plano["observacoes"])


def test_sessao_traz_objetivo_metodo_materiais_e_criterio():
    plano = planejar(cadeia(TODOS_ESTUDADOS), hoje=HOJE)
    sessao = plano["sessoes"][0]

    assert sessao["objetivo"]
    assert sessao["metodos_de_revisao"]
    assert sessao["materiais_necessarios"]
    assert sessao["criterios_de_conclusao"]
    assert sessao["meta"]["conteudos_a_revisar"] == len(sessao["conteudos"])
    assert sessao["id"].startswith("sessao-")


def test_criterio_de_conclusao_acompanha_o_metodo():
    plano = planejar(cadeia(TODOS_ESTUDADOS), hoje=HOJE)
    for sessao in plano["sessoes"]:
        for criterio in sessao["criterios_de_conclusao"]:
            assert criterio["criterio"] == CRITERIO_POR_METODO[criterio["metodo"]]


def test_tipo_da_sessao_vem_do_risco_de_esquecimento():
    plano = planejar(cadeia(TODOS_ESTUDADOS), hoje=HOJE)
    tipos = {s["tipo"] for s in plano["sessoes"]}

    assert tipos <= {"rapida", "aprofundada", "critica"}
    criticas = [s for s in plano["sessoes"] if s["tipo"] == "critica"]
    assert criticas
    assert all(
        c["risco_de_esquecimento"] in ("alto", "critico")
        for s in criticas
        for c in s["conteudos"]
    )


def test_sessao_critica_ganha_metodo_de_explicacao_ativa():
    plano = planejar(cadeia(TODOS_ESTUDADOS), hoje=HOJE)
    critica = next(s for s in plano["sessoes"] if s["tipo"] == "critica")

    assert critica["metodo_complementar"] == "explicacao_ativa"
    assert "explicacao_ativa" in critica["metodos_de_revisao"]


def test_sessao_rapida_nao_tem_complemento():
    plano = planejar(cadeia(TODOS_ESTUDADOS), hoje=HOJE)
    rapidas = [s for s in plano["sessoes"] if s["tipo"] == "rapida"]

    assert rapidas
    assert all(s["metodo_complementar"] is None for s in rapidas)


# --------------------------------------------------------------------------- #
# Carga e equilíbrio
# --------------------------------------------------------------------------- #


def test_nenhuma_sessao_passa_do_teto_de_minutos():
    topicos = [f"Tópico {i}" for i in range(20)]
    dados = {
        "edital": {"Português": {"questoes": 20, "topicos": topicos}},
        "resultados_exercicios": [acertos(t, 2, 10) for t in topicos],
        "historico_revisoes": [revisao_em(t, 80) for t in topicos],
        "maximo_revisoes_por_dia": 20,
    }
    plano = planejar(cadeia(dados), hoje=HOJE)

    assert plano["sessoes"]
    assert all(s["duracao_min"] <= MAXIMO_MINUTOS_POR_SESSAO for s in plano["sessoes"])


def test_criticos_por_sessao_tem_teto():
    topicos = [f"Tópico {i}" for i in range(8)]
    dados = {
        "edital": {"Português": {"questoes": 20, "topicos": topicos}},
        "resultados_exercicios": [acertos(t, 1, 10) for t in topicos],
        "historico_revisoes": [revisao_em(t, 90) for t in topicos],
        "maximo_revisoes_por_dia": 8,
    }
    plano = planejar(cadeia(dados), hoje=HOJE)

    for sessao in plano["sessoes"]:
        assert sessao["equilibrio"]["pesados"] <= MAXIMO_CRITICOS_POR_SESSAO


def test_sessao_intercala_pesado_e_leve():
    dados = {
        "resultados_exercicios": [
            acertos("Crase", 2, 10),
            acertos("Sintaxe", 9, 10),
        ],
        "historico_revisoes": [revisao_em("Crase", 80), revisao_em("Sintaxe", 80)],
    }
    plano = planejar(cadeia(dados), hoje=HOJE)
    com_ambos = [
        s
        for s in plano["sessoes"]
        if s["equilibrio"]["pesados"] and s["equilibrio"]["leves"]
    ]

    if com_ambos:
        riscos = [c["risco_de_esquecimento"] for c in com_ambos[0]["conteudos"]]
        assert riscos[0] in ("alto", "critico")


# --------------------------------------------------------------------------- #
# Tempo disponível e prioridade
# --------------------------------------------------------------------------- #


def test_tempo_vem_do_bloco_de_revisao_do_agente_06():
    plano = planejar(cadeia(TODOS_ESTUDADOS), hoje=HOJE)
    assert "agente 06" in plano["resumo_geral"]["origem_do_tempo_disponivel"]


def test_tempo_informado_pelo_usuario_tem_precedencia():
    plano = planejar(
        cadeia({**TODOS_ESTUDADOS, "tempo_revisao_min": 15}), hoje=HOJE
    )
    assert "informado pelo usuário" in plano["resumo_geral"]["origem_do_tempo_disponivel"]

    # Sessões respeitam o limite, salvo o conteúdo cujo método sozinho custa mais
    # que o bloco inteiro — esse entra declarado.
    for sessao in plano["sessoes"]:
        excedentes = [
            c for c in sessao["conteudos"] if c.get("excede_o_bloco_do_dia")
        ]
        assert sessao["duracao_min"] <= 15 or excedentes


def test_o_que_nao_cabe_hoje_e_adiado_nao_descartado():
    plano = planejar(
        cadeia({**TODOS_ESTUDADOS, "tempo_revisao_min": 10}), hoje=HOJE
    )

    assert plano["conteudos_adiados"]
    assert all("tempo de revisão do dia esgotado" in a["motivo"] for a in plano["conteudos_adiados"])
    assert any("adiada(s) para o próximo dia" in o for o in plano["observacoes"])


def test_adiamento_respeita_a_prioridade_do_agente_14():
    plano = planejar(
        cadeia({**TODOS_ESTUDADOS, "tempo_revisao_min": 10}), hoje=HOJE
    )
    primeira_data = plano["sessoes"][0]["data"]
    no_primeiro_dia = [
        c for s in plano["sessoes"] if s["data"] == primeira_data for c in s["conteudos"]
    ]
    adiados = {a["topico"] for a in plano["conteudos_adiados"] if a["de"] == primeira_data}

    # O que ficou no primeiro dia tem prioridade igual ou maior que o adiado.
    if no_primeiro_dia and adiados:
        ordem = {"alta": 0, "media": 1, "baixa": 2}
        pior_mantido = max(ordem[c["prioridade"]] for c in no_primeiro_dia)
        melhor_adiado = min(
            ordem[c["prioridade"]]
            for s in plano["sessoes"]
            for c in s["conteudos"]
            if c["topico"] in adiados
        )
        assert pior_mantido <= melhor_adiado


def test_nenhum_conteudo_do_agente_14_desaparece():
    entradas = cadeia({**TODOS_ESTUDADOS, "tempo_revisao_min": 10})
    monitorados = {c["topico"] for c in entradas["saidas_anteriores"]["14"]["conteudos"]}
    plano = planejar(entradas, hoje=HOJE)

    em_sessao = {c["topico"] for s in plano["sessoes"] for c in s["conteudos"]}
    declarados = {c["topico"] for c in plano["conteudos_nao_alocados"]}

    assert monitorados == em_sessao | declarados


def test_conteudo_que_nunca_cabe_entra_com_o_estouro_declarado():
    # Reestudo custa 25 min + 3 do complemento; o bloco do dia tem 5.
    dados = {
        "resultados_exercicios": [acertos("Crase", 2, 10)],
        "historico_revisoes": [revisao_em("Crase", 120)],
        "tempo_revisao_min": 5,
    }
    plano = planejar(cadeia(dados), hoje=HOJE)
    conteudo = plano["sessoes"][0]["conteudos"][0]

    assert conteudo["excede_o_bloco_do_dia"]["minutos_disponiveis"] == 5
    assert conteudo["excede_o_bloco_do_dia"]["minutos_necessarios"] > 5
    assert "adiar indefinidamente seria pior" in conteudo["excede_o_bloco_do_dia"]["motivo"]


# --------------------------------------------------------------------------- #
# Indicadores
# --------------------------------------------------------------------------- #


def test_indicadores_de_cobertura_e_equilibrio():
    plano = planejar(cadeia(TODOS_ESTUDADOS), hoje=HOJE)
    indicadores = plano["indicadores"]

    assert indicadores["cobertura_das_revisoes"] == 1.0
    assert indicadores["conteudos_monitorados"] == 4
    assert sum(indicadores["distribuicao_por_disciplina"].values()) == 4
    assert indicadores["equilibrio_de_dificuldade"]["pesados"] >= 1
    assert indicadores["tempo_medio_por_sessao_min"] > 0


def test_falta_de_tempo_espalha_as_sessoes_sem_perder_cobertura():
    completo = planejar(cadeia(TODOS_ESTUDADOS), hoje=HOJE)
    apertado = planejar(
        cadeia({**TODOS_ESTUDADOS, "tempo_revisao_min": 10}), hoje=HOJE
    )

    # A cobertura se mantém: o que não cabe é adiado, não cortado.
    assert apertado["indicadores"]["cobertura_das_revisoes"] == 1.0
    assert completo["indicadores"]["cobertura_das_revisoes"] == 1.0
    # Mas o plano fica mais longo e com mais sessões.
    assert len(apertado["sessoes"]) >= len(completo["sessoes"])
    assert apertado["conteudos_adiados"]


def test_resumo_lista_criticos_e_prioritarios():
    plano = planejar(cadeia(TODOS_ESTUDADOS), hoje=HOJE)
    resumo = plano["resumo_geral"]

    assert "Conjuntos" in resumo["conteudos_criticos"]
    assert resumo["numero_total_de_sessoes"] == len(plano["sessoes"])
    assert resumo["tempo_total_de_revisao_min"] > 0
    assert resumo["periodo"]["inicio"]


# --------------------------------------------------------------------------- #
# Replanejamento e escopo
# --------------------------------------------------------------------------- #


def test_replanejamento_compara_com_as_sessoes_anteriores():
    antes = planejar(cadeia(TODOS_ESTUDADOS), hoje=HOJE)
    depois = planejar(
        cadeia({**TODOS_ESTUDADOS, "sessoes_anteriores": antes}), hoje=HOJE
    )

    assert depois["replanejamento"]["houve_replanejamento"] is True
    assert depois["replanejamento"]["sessoes_novas"] == []
    assert depois["replanejamento"]["sessoes_removidas"] == []


def test_sem_sessoes_anteriores_nao_ha_replanejamento():
    plano = planejar(cadeia(TODOS_ESTUDADOS), hoje=HOJE)
    assert plano["replanejamento"]["houve_replanejamento"] is False


def test_plano_nao_altera_cronograma_nem_arvore():
    plano = planejar(cadeia(TODOS_ESTUDADOS), hoje=HOJE)
    proibidos = {"cronograma", "disciplinas", "metas", "exercicios", "nos"}

    assert proibidos.isdisjoint(plano)
    assert any("não altera o Plano de Estudos" in o for o in plano["observacoes"])


def test_saida_declara_os_agentes_consumidores():
    plano = planejar(cadeia(TODOS_ESTUDADOS), hoje=HOJE)
    assert plano["consumido_por"] == ["16", "17", "18", "19", "21", "22", "23", "24"]


# --------------------------------------------------------------------------- #
# Integração
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_agente_15_no_fluxo_completo():
    resultado = await MasterOrchestrator().orquestrar(
        "Preciso revisar com flashcards",
        dados_usuario={
            "objetivo": "Passar no concurso fiscal",
            "edital": EDITAL,
            "escolaridade": "Superior completo",
            "horas_por_dia": 3,
            "dias_por_semana": 5,
            "data_prova": "2027-01-01",
            "profissao": "Analista",
            "rotina": "Estudo em casa",
            "experiencia_anterior": "nenhuma",
            "preferencia_estudo": "questões",
            "idade": 30,
            "resultados_exercicios": [
                {
                    "disciplina": "Português",
                    "topico": "Crase",
                    "acertos": 6,
                    "total": 10,
                    "data": "2025-11-01",
                }
            ],
        },
    )
    plano = resultado.saidas["15"].conteudo

    assert plano["sessoes"]
    assert plano["indicadores"]["cobertura_das_revisoes"] > 0
    assert resultado.validacao.aprovado is True


@pytest.mark.asyncio
async def test_agente_15_roda_depois_do_14():
    resultado = await MasterOrchestrator().orquestrar("Preciso revisar")
    ondas = {
        agente.split()[0]: onda["onda"]
        for onda in resultado.ordem_execucao
        for agente in onda["agentes"]
    }
    assert ondas["14"] < ondas["15"]
