from datetime import date, timedelta

import pytest

from app.studyos.agentes.conhecimento import analisar as analisar_conhecimento
from app.studyos.agentes.curriculo import construir as construir_curriculo
from app.studyos.agentes.dependencias import mapear
from app.studyos.agentes.dificuldade import detectar
from app.studyos.agentes.memoria import (
    INTERVALOS_BASE,
    MEIA_VIDA_BASE_DIAS,
    MINUTOS_POR_METODO,
    RETENCAO_ALVO,
    agendar,
)
from app.studyos.agentes.objetivo import analisar as analisar_objetivo
from app.studyos.agentes.perfil import analisar as analisar_perfil
from app.studyos.agentes.roadmap import construir as construir_roadmap
from app.studyos.orchestrator import MasterOrchestrator

HOJE = date(2026, 1, 5)

EDITAL = {
    "Estatística": {"questoes": 10, "topicos": ["Conjuntos", "Probabilidade"]},
    "Português": {"questoes": 20, "topicos": ["Crase"]},
}


def cadeia(dados=None, extras=None):
    """Roda 01–06 e 12 de verdade e devolve as entradas prontas para o 14."""
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
    m12 = detectar(
        {
            "dados_usuario": base,
            "saidas_anteriores": {"01": m1, "02": m2, "03": m3, "04": m4, "05": m5, "06": m6},
        },
        hoje=HOJE,
    )
    anteriores = {
        "01": m1, "02": m2, "03": m3, "04": m4, "05": m5, "06": m6, "12": m12,
        **(extras or {}),
    }
    return {"solicitacao": "", "dados_usuario": base, "saidas_anteriores": anteriores}


def acertos(topico, certos, total, disciplina="Português", data=None):
    return {
        "disciplina": disciplina,
        "topico": topico,
        "acertos": certos,
        "total": total,
        "data": (data or HOJE).isoformat(),
    }


def conteudo_de(plano, topico):
    return next(c for c in plano["conteudos"] if c["topico"] == topico)


# --------------------------------------------------------------------------- #
# Elegibilidade
# --------------------------------------------------------------------------- #


def test_conteudo_nao_estudado_nao_entra_no_plano():
    plano = agendar(cadeia(), hoje=HOJE)

    assert plano["conteudos"] == []
    assert len(plano["nao_elegiveis"]) == 3
    assert all("não estudado" in n["motivo"] for n in plano["nao_elegiveis"])
    assert any("revisão de conteúdo novo não existe" in o for o in plano["observacoes"])


def test_conteudo_com_medicao_e_elegivel():
    plano = agendar(
        cadeia({"resultados_exercicios": [acertos("Crase", 8, 10)]}), hoje=HOJE
    )

    assert [c["topico"] for c in plano["conteudos"]] == ["Crase"]
    assert conteudo_de(plano, "Crase")["disciplina"] == "Português"


def test_conteudo_com_historico_de_revisao_e_elegivel():
    dados = {
        "historico_revisoes": [
            {"conteudo": "Crase", "data": "2026-01-01", "resultado": "acerto"}
        ]
    }
    plano = agendar(cadeia(dados), hoje=HOJE)
    assert conteudo_de(plano, "Crase")["revisoes_realizadas"] == 1


# --------------------------------------------------------------------------- #
# Retenção e meia-vida
# --------------------------------------------------------------------------- #


def test_meia_vida_cresce_com_o_dominio():
    fraco = agendar(
        cadeia({"resultados_exercicios": [acertos("Crase", 1, 10)]}), hoje=HOJE
    )
    forte = agendar(
        cadeia({"resultados_exercicios": [acertos("Crase", 10, 10)]}), hoje=HOJE
    )

    assert (
        conteudo_de(forte, "Crase")["meia_vida"]["dias"]
        > conteudo_de(fraco, "Crase")["meia_vida"]["dias"]
    )
    assert str(MEIA_VIDA_BASE_DIAS) in conteudo_de(forte, "Crase")["meia_vida"]["base"]


def test_retencao_cai_com_o_tempo_sem_contato():
    recente = agendar(
        cadeia(
            {
                "resultados_exercicios": [acertos("Crase", 8, 10)],
                "historico_revisoes": [
                    {"conteudo": "Crase", "data": HOJE.isoformat(), "resultado": "acerto"}
                ],
            }
        ),
        hoje=HOJE,
    )
    antigo = agendar(
        cadeia(
            {
                "resultados_exercicios": [acertos("Crase", 8, 10)],
                "historico_revisoes": [
                    {
                        "conteudo": "Crase",
                        "data": (HOJE - timedelta(days=60)).isoformat(),
                        "resultado": "acerto",
                    }
                ],
            }
        ),
        hoje=HOJE,
    )

    assert conteudo_de(recente, "Crase")["nivel_de_retencao"] == 1.0
    assert conteudo_de(antigo, "Crase")["nivel_de_retencao"] < 0.5


@pytest.mark.parametrize(
    "dias,risco_esperado",
    [(0, "baixo"), (15, "medio"), (35, "alto"), (90, "critico")],
)
def test_risco_de_esquecimento_acompanha_a_retencao(dias, risco_esperado):
    dados = {
        "resultados_exercicios": [acertos("Crase", 8, 10)],
        "historico_revisoes": [
            {
                "conteudo": "Crase",
                "data": (HOJE - timedelta(days=dias)).isoformat(),
                "resultado": "acerto",
            }
        ],
    }
    plano = agendar(cadeia(dados), hoje=HOJE)
    assert conteudo_de(plano, "Crase")["risco_de_esquecimento"] == risco_esperado


# --------------------------------------------------------------------------- #
# Escada de repetição espaçada
# --------------------------------------------------------------------------- #


def test_primeira_revisao_comeca_no_primeiro_degrau():
    plano = agendar(
        cadeia({"resultados_exercicios": [acertos("Crase", 8, 10)]}), hoje=HOJE
    )
    intervalo = conteudo_de(plano, "Crase")["intervalo"]

    assert intervalo["degrau"] == 1
    assert intervalo["da_escada"] == INTERVALOS_BASE[0]


def test_acertos_sucessivos_avancam_a_escada():
    dados = {
        "resultados_exercicios": [acertos("Crase", 10, 10)],
        "historico_revisoes": [
            {"conteudo": "Crase", "data": "2026-01-01", "resultado": "acerto"},
            {"conteudo": "Crase", "data": "2026-01-02", "resultado": "acerto"},
            {"conteudo": "Crase", "data": "2026-01-03", "resultado": "acerto"},
        ],
    }
    plano = agendar(cadeia(dados), hoje=HOJE)
    conteudo = conteudo_de(plano, "Crase")

    assert conteudo["intervalo"]["degrau"] == 4
    assert conteudo["acertos_consecutivos"] == 3


def test_erro_reinicia_a_escada():
    dados = {
        "resultados_exercicios": [acertos("Crase", 5, 10)],
        "historico_revisoes": [
            {"conteudo": "Crase", "data": "2026-01-01", "resultado": "acerto"},
            {"conteudo": "Crase", "data": "2026-01-02", "resultado": "acerto"},
            {"conteudo": "Crase", "data": "2026-01-03", "resultado": "erro"},
        ],
    }
    plano = agendar(cadeia(dados), hoje=HOJE)
    assert conteudo_de(plano, "Crase")["intervalo"]["degrau"] == 1


def test_intervalo_e_cortado_quando_a_retencao_cairia_antes():
    dados = {
        "resultados_exercicios": [acertos("Crase", 2, 10)],
        "historico_revisoes": [
            {"conteudo": "Crase", "data": "2026-01-01", "resultado": "acerto"},
            {"conteudo": "Crase", "data": "2026-01-02", "resultado": "acerto"},
            {"conteudo": "Crase", "data": "2026-01-03", "resultado": "acerto"},
            {"conteudo": "Crase", "data": "2026-01-04", "resultado": "acerto"},
        ],
    }
    plano = agendar(cadeia(dados), hoje=HOJE)
    intervalo = conteudo_de(plano, "Crase")["intervalo"]

    assert intervalo["dias"] == intervalo["pelo_esquecimento"]
    assert intervalo["dias"] < intervalo["da_escada"]
    assert f"{RETENCAO_ALVO:.0%}" in intervalo["base"]


def test_revisao_vencida_e_agendada_para_hoje():
    dados = {
        "resultados_exercicios": [acertos("Crase", 8, 10)],
        "historico_revisoes": [
            {
                "conteudo": "Crase",
                "data": (HOJE - timedelta(days=60)).isoformat(),
                "resultado": "acerto",
            }
        ],
    }
    plano = agendar(cadeia(dados), hoje=HOJE)
    conteudo = conteudo_de(plano, "Crase")

    assert conteudo["proxima_revisao"] == HOJE.isoformat()
    assert "vencida" in conteudo["intervalo"]["ajuste"]


# --------------------------------------------------------------------------- #
# Método recomendado
# --------------------------------------------------------------------------- #


def test_retencao_muito_baixa_pede_reestudo():
    dados = {
        "resultados_exercicios": [acertos("Crase", 3, 10)],
        "historico_revisoes": [
            {
                "conteudo": "Crase",
                "data": (HOJE - timedelta(days=120)).isoformat(),
                "resultado": "acerto",
            }
        ],
    }
    plano = agendar(cadeia(dados), hoje=HOJE)
    conteudo = conteudo_de(plano, "Crase")

    assert conteudo["metodo_recomendado"] == "reestudo_da_aula"
    assert "limiar de reestudo" in conteudo["base_do_metodo"]


@pytest.mark.parametrize(
    "categoria,metodo",
    [
        ("fixacao", "flashcards"),
        ("aplicacao", "exercicios"),
        ("analise", "questoes_comentadas"),
    ],
)
def test_metodo_acompanha_o_tipo_de_dificuldade(categoria, metodo):
    dados = {
        "resultados_exercicios": [acertos("Crase", 6, 10)],
        "erros": [{"topico": "Crase", "categoria": categoria}],
    }
    extras = {"10": {"flashcards": [{"id": "fc-1"}]}}
    plano = agendar(cadeia(dados, extras), hoje=HOJE)

    assert conteudo_de(plano, "Crase")["metodo_recomendado"] == metodo
    assert "agente 12" in conteudo_de(plano, "Crase")["base_do_metodo"]


def test_metodo_indisponivel_nao_e_recomendado():
    dados = {"resultados_exercicios": [acertos("Crase", 6, 10)]}
    plano = agendar(cadeia(dados), hoje=HOJE)

    # Sem agente 10 nem 11 na cadeia, flashcards e resumo não existem.
    assert conteudo_de(plano, "Crase")["metodo_recomendado"] not in (
        "flashcards",
        "leitura_do_resumo",
    )
    assert any("Sem flashcards" in o for o in plano["observacoes"])


def test_minutos_acompanham_o_metodo():
    dados = {"resultados_exercicios": [acertos("Crase", 6, 10)]}
    plano = agendar(cadeia(dados), hoje=HOJE)
    conteudo = conteudo_de(plano, "Crase")

    assert conteudo["minutos_estimados"] == MINUTOS_POR_METODO[
        conteudo["metodo_recomendado"]
    ]


# --------------------------------------------------------------------------- #
# Prioridade, calendário e limites
# --------------------------------------------------------------------------- #


def test_prioridade_combina_risco_dificuldade_e_disciplina():
    dados = {
        "resultados_exercicios": [
            acertos("Crase", 1, 10),
            acertos("Conjuntos", 9, 10, disciplina="Estatística"),
        ],
        "historico_revisoes": [
            {
                "conteudo": "Crase",
                "data": (HOJE - timedelta(days=60)).isoformat(),
                "resultado": "acerto",
            }
        ],
    }
    plano = agendar(cadeia(dados), hoje=HOJE)

    assert conteudo_de(plano, "Crase")["prioridade"] == "alta"
    assert conteudo_de(plano, "Crase")["score_de_prioridade"] > conteudo_de(
        plano, "Conjuntos"
    )["score_de_prioridade"]


def test_calendario_agrupa_por_dia_e_disciplina():
    dados = {
        "resultados_exercicios": [
            acertos("Crase", 8, 10),
            acertos("Conjuntos", 8, 10, disciplina="Estatística"),
        ]
    }
    plano = agendar(cadeia(dados), hoje=HOJE)
    dia = plano["calendario"][0]

    assert dia["total_de_revisoes"] >= 1
    assert all("disciplina" in g and "conteudos" in g for g in dia["grupos"])
    assert dia["minutos_estimados"] > 0


def test_excesso_no_dia_e_remanejado_nunca_removido():
    topicos = [f"Tópico {i}" for i in range(12)]
    edital = {"Português": {"questoes": 20, "topicos": topicos}}
    dados = {
        "edital": edital,
        "resultados_exercicios": [acertos(t, 8, 10) for t in topicos],
        "maximo_revisoes_por_dia": 3,
    }
    plano = agendar(cadeia(dados), hoje=HOJE)

    assert len(plano["conteudos"]) == 12  # nenhuma sumiu
    assert plano["remanejadas"]
    assert all(d["total_de_revisoes"] <= 3 for d in plano["calendario"])
    assert any("nenhuma foi removida" in o for o in plano["observacoes"])


def test_teto_diario_vem_do_bloco_de_revisao_do_agente_06():
    dados = {"resultados_exercicios": [acertos("Crase", 8, 10)]}
    plano = agendar(cadeia(dados), hoje=HOJE)
    assert plano["resumo_geral"]["teto_de_revisoes_por_dia"] >= 1


# --------------------------------------------------------------------------- #
# Integração com o agente 13
# --------------------------------------------------------------------------- #


def test_pedido_do_agente_13_encurta_o_intervalo():
    dados = {
        "resultados_exercicios": [acertos("Crase", 8, 10)],
        "historico_revisoes": [
            {"conteudo": "Crase", "data": "2026-01-01", "resultado": "acerto"},
            {"conteudo": "Crase", "data": "2026-01-02", "resultado": "acerto"},
            {"conteudo": "Crase", "data": "2026-01-03", "resultado": "acerto"},
        ],
    }
    sem_pedido = agendar(cadeia(dados), hoje=HOJE)
    com_pedido = agendar(
        cadeia(
            dados,
            {
                "13": {
                    "solicitacoes": [
                        {
                            "agente": "14 Memory Scheduler",
                            "pedido": "encurtar o intervalo de repetição de Crase",
                            "motivo": "dificuldade persistente",
                        }
                    ]
                }
            },
        ),
        hoje=HOJE,
    )

    assert (
        com_pedido["conteudos"][0]["intervalo_atual_dias"]
        < sem_pedido["conteudos"][0]["intervalo_atual_dias"]
    )
    assert "agente 13" in com_pedido["conteudos"][0]["intervalo"]["ajuste"]
    assert any("agente 13" in o for o in com_pedido["observacoes"])


# --------------------------------------------------------------------------- #
# Indicadores e escopo
# --------------------------------------------------------------------------- #


def test_indicadores_separam_dominados_consolidacao_e_criticos():
    dados = {
        "resultados_exercicios": [
            acertos("Crase", 9, 10),
            acertos("Conjuntos", 9, 10, disciplina="Estatística"),
        ],
        "historico_revisoes": [
            {"conteudo": "Crase", "data": HOJE.isoformat(), "resultado": "acerto"},
            {
                "conteudo": "Conjuntos",
                "data": (HOJE - timedelta(days=90)).isoformat(),
                "resultado": "acerto",
            },
        ],
    }
    plano = agendar(cadeia(dados), hoje=HOJE)
    indicadores = plano["indicadores"]

    assert "Crase" in indicadores["conteudos_dominados"]
    assert "Conjuntos" in indicadores["conteudos_criticos"]


def test_tendencia_compara_com_o_plano_anterior():
    dados = {"resultados_exercicios": [acertos("Crase", 8, 10)]}
    antes = agendar(cadeia(dados), hoje=HOJE)
    antes["resumo_geral"]["indice_medio_de_retencao"] = 0.5

    depois = agendar(cadeia({**dados, "plano_anterior": antes}), hoje=HOJE)

    assert depois["indicadores"]["tendencia_de_retencao"] == "melhorando"
    assert depois["indicadores"]["evolucao_da_memoria"]["variacao_do_indice"] > 0


def test_sem_plano_anterior_a_tendencia_e_indeterminada():
    plano = agendar(
        cadeia({"resultados_exercicios": [acertos("Crase", 8, 10)]}), hoje=HOJE
    )
    assert plano["indicadores"]["tendencia_de_retencao"] == "indeterminada"


def test_plano_nao_altera_o_cronograma_principal():
    plano = agendar(
        cadeia({"resultados_exercicios": [acertos("Crase", 8, 10)]}), hoje=HOJE
    )
    proibidos = {"cronograma", "sessoes", "metas", "exercicios"}

    assert proibidos.isdisjoint(plano)
    assert any("não altera o cronograma principal" in o for o in plano["observacoes"])


def test_saida_declara_os_agentes_consumidores():
    plano = agendar(cadeia(), hoje=HOJE)
    assert plano["consumido_por"] == [
        "15", "16", "17", "18", "19", "21", "22", "23", "24"
    ]


# --------------------------------------------------------------------------- #
# Integração
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_agente_14_no_fluxo_completo():
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
                {"disciplina": "Português", "topico": "Crase", "acertos": 8, "total": 10}
            ],
        },
    )
    plano = resultado.saidas["14"].conteudo

    assert plano["conteudos"]
    assert plano["calendario"]
    assert plano["resumo_geral"]["total_de_conteudos_monitorados"] > 0
    assert resultado.validacao.aprovado is True


@pytest.mark.asyncio
async def test_conteudo_sem_data_de_contato_declara_a_retencao_ausente():
    # O resultado do exercício não traz data: dá para saber que foi estudado,
    # mas não há de quando medir o esquecimento.
    resultado = await MasterOrchestrator().orquestrar(
        "Preciso revisar",
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
                {"disciplina": "Português", "topico": "Crase", "acertos": 8, "total": 10}
            ],
        },
    )
    plano = resultado.saidas["14"].conteudo
    conteudo = conteudo_de(plano, "Crase")

    assert conteudo["nivel_de_retencao"] is None
    assert conteudo["risco_de_esquecimento"] == "indeterminado"
    assert plano["resumo_geral"]["indice_medio_de_retencao"] is None
    assert any("sem data de contato" in o for o in plano["observacoes"])


@pytest.mark.asyncio
async def test_agente_14_roda_depois_do_10_e_do_13():
    resultado = await MasterOrchestrator().orquestrar("Preciso revisar")
    ondas = {
        agente.split()[0]: onda["onda"]
        for onda in resultado.ordem_execucao
        for agente in onda["agentes"]
    }
    assert ondas["10"] < ondas["14"]
    assert ondas["13"] < ondas["14"]
