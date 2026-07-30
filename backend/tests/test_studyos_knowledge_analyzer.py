from datetime import date, timedelta

import pytest

from app.studyos.agentes.conhecimento import (
    MINIMO_QUESTOES_POR_TOPICO,
    RETENCAO_MEIA_VIDA_DIAS,
    analisar,
)
from app.studyos.agentes.objetivo import analisar as analisar_objetivo
from app.studyos.orchestrator import MasterOrchestrator

HOJE = date(2026, 1, 1)

EDITAL = {
    "Português": {"topicos": ["Crase", "Sintaxe", "Interpretação"], "questoes": 20},
    "Estatística": {"topicos": ["Probabilidade", "Distribuições"], "questoes": 10},
}


def mapa_estrategico(edital=EDITAL, **extras):
    dados = {"objetivo": "Passar no concurso fiscal", "edital": edital, **extras}
    return analisar_objetivo({"dados_usuario": dados, "solicitacao": ""}, hoje=HOJE)


def entradas(dados=None, com_mapa=True, mapa=None):
    anteriores = {}
    if com_mapa:
        anteriores["02"] = mapa or mapa_estrategico()
    return {
        "solicitacao": "",
        "dados_usuario": dados or {},
        "saidas_anteriores": anteriores,
    }


def acertos(disciplina, topico, acertos_, total, tipo="exercicio", data=None):
    return {
        "disciplina": disciplina,
        "topico": topico,
        "acertos": acertos_,
        "total": total,
        "tipo": tipo,
        "data": (data or HOJE).isoformat(),
    }


# --------------------------------------------------------------------------- #
# Regra central: sem evidência, sem classificação
# --------------------------------------------------------------------------- #


def test_sem_evidencia_nenhum_topico_e_classificado():
    resultado = analisar(entradas(), hoje=HOJE)

    for disciplina in resultado["disciplinas"]:
        assert disciplina["percentual_dominio"] is None
        assert disciplina["topicos_dominados"] == []
        assert len(disciplina["topicos_sem_evidencia"]) == len(disciplina["topicos"])

    assert resultado["indice_geral_de_conhecimento"]["valor"] is None
    assert resultado["avaliacao_diagnostica"]["necessaria"] is True


def test_percepcao_do_estudante_nao_prova_dominio():
    resultado = analisar(
        entradas(
            {
                "disciplinas_favoritas": ["Português"],
                "disciplinas_dificuldade": ["Estatística"],
                "historico": "Estudei Português por dois anos",
            }
        ),
        hoje=HOJE,
    )
    portugues = next(
        d for d in resultado["disciplinas"] if d["disciplina"] == "Português"
    )

    assert portugues["percentual_dominio"] is None
    assert portugues["topicos_dominados"] == []
    assert any("Percepção do estudante" in o for o in resultado["observacoes"])


def test_dificuldade_declarada_pesa_na_dificuldade_mas_nao_no_dominio():
    dados = {
        "disciplinas_dificuldade": ["Estatística"],
        "resultados_exercicios": [
            acertos("Estatística", "Probabilidade", 6, 10),
            acertos("Estatística", "Distribuições", 6, 10),
        ],
    }
    resultado = analisar(entradas(dados), hoje=HOJE)
    estatistica = next(
        d for d in resultado["disciplinas"] if d["disciplina"] == "Estatística"
    )

    assert estatistica["percentual_dominio"] == 0.6  # só das questões
    assert estatistica["grau_dificuldade"]["percepcao_de_dificuldade"] is True
    assert "dificuldade declarada" in estatistica["grau_dificuldade"]["base"]


def test_amostra_pequena_nao_classifica():
    resultado = analisar(
        entradas({"resultados_exercicios": [acertos("Português", "Crase", 3, 3)]}),
        hoje=HOJE,
    )
    crase = next(
        t
        for d in resultado["disciplinas"]
        for t in d["topicos"]
        if t["topico"] == "Crase"
    )

    assert crase["classificacao"] == "indeterminado"
    assert str(MINIMO_QUESTOES_POR_TOPICO) in crase["base"]
    assert crase["confianca"] == "baixa"


# --------------------------------------------------------------------------- #
# Classificação por evidência prática
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "acertos_,total,esperado",
    [
        (10, 10, "avancado"),
        (9, 10, "avancado"),
        (7, 10, "intermediario"),
        (4, 10, "basico"),
        (2, 10, "nao_conhece"),
    ],
)
def test_faixas_de_classificacao(acertos_, total, esperado):
    resultado = analisar(
        entradas(
            {"resultados_exercicios": [acertos("Português", "Crase", acertos_, total)]}
        ),
        hoje=HOJE,
    )
    crase = next(
        t
        for d in resultado["disciplinas"]
        for t in d["topicos"]
        if t["topico"] == "Crase"
    )
    assert crase["classificacao"] == esperado


def test_simulado_pesa_mais_que_exercicio():
    resultado = analisar(
        entradas(
            {
                "resultados_exercicios": [acertos("Português", "Crase", 10, 10)],
                "resultados_simulados": [
                    acertos("Português", "Crase", 0, 10, tipo="simulado")
                ],
            }
        ),
        hoje=HOJE,
    )
    crase = next(
        t
        for d in resultado["disciplinas"]
        for t in d["topicos"]
        if t["topico"] == "Crase"
    )
    # Média ponderada puxada para baixo pelo simulado (peso 1.0 vs 0.8).
    assert crase["taxa_acerto"] < 0.5
    assert crase["amostra"] == 20


def test_percentual_da_disciplina_usa_apenas_topicos_medidos():
    resultado = analisar(
        entradas(
            {
                "resultados_exercicios": [
                    acertos("Português", "Crase", 10, 10),
                    acertos("Português", "Sintaxe", 3, 10),
                ]
            }
        ),
        hoje=HOJE,
    )
    portugues = next(
        d for d in resultado["disciplinas"] if d["disciplina"] == "Português"
    )

    assert portugues["percentual_dominio"] == 0.5  # (1.0 + 0.0) / 2
    assert portugues["cobertura_diagnostica"] == pytest.approx(2 / 3, rel=1e-2)
    assert portugues["topicos_sem_evidencia"] == ["Interpretação"]


def test_cobertura_baixa_marca_percentual_como_nao_confiavel():
    resultado = analisar(
        entradas({"resultados_exercicios": [acertos("Português", "Crase", 9, 10)]}),
        hoje=HOJE,
    )
    portugues = next(
        d for d in resultado["disciplinas"] if d["disciplina"] == "Português"
    )

    assert portugues["confiavel"] is False
    assert "abaixo do mínimo confiável" in portugues["base_do_percentual"]


def test_evidencia_sem_topico_vale_no_nivel_da_disciplina():
    resultado = analisar(
        entradas(
            {
                "resultados_simulados": [
                    {
                        "disciplina": "Português",
                        "acertos": 16,
                        "total": 20,
                        "tipo": "simulado",
                    }
                ]
            }
        ),
        hoje=HOJE,
    )
    portugues = next(
        d for d in resultado["disciplinas"] if d["disciplina"] == "Português"
    )

    assert portugues["percentual_dominio"] == pytest.approx(0.8)
    assert "evidência agregada da disciplina" in portugues["base_do_percentual"]


# --------------------------------------------------------------------------- #
# Esquecimento
# --------------------------------------------------------------------------- #


def test_topico_sem_contato_recente_e_rebaixado():
    antigo = HOJE - timedelta(days=4 * RETENCAO_MEIA_VIDA_DIAS)
    resultado = analisar(
        entradas(
            {"resultados_exercicios": [acertos("Português", "Crase", 10, 10, data=antigo)]}
        ),
        hoje=HOJE,
    )
    crase = next(
        t
        for d in resultado["disciplinas"]
        for t in d["topicos"]
        if t["topico"] == "Crase"
    )

    assert crase["esquecido"] is True
    assert crase["classificacao"] == "intermediario"  # rebaixado de avancado
    assert "rebaixado" in crase["base"]
    assert crase["retencao_estimada"] < 0.5


def test_contato_recente_preserva_a_classificacao():
    resultado = analisar(
        entradas(
            {
                "resultados_exercicios": [acertos("Português", "Crase", 10, 10)],
                "ultimo_contato": {"Crase": HOJE.isoformat()},
            }
        ),
        hoje=HOJE,
    )
    crase = next(
        t
        for d in resultado["disciplinas"]
        for t in d["topicos"]
        if t["topico"] == "Crase"
    )
    assert crase["esquecido"] is False
    assert crase["classificacao"] == "avancado"


def test_esquecimento_vira_risco_e_recomendacao_de_revisao():
    antigo = HOJE - timedelta(days=120)
    resultado = analisar(
        entradas(
            {"resultados_exercicios": [acertos("Português", "Crase", 10, 10, data=antigo)]}
        ),
        hoje=HOJE,
    )
    riscos = {r["risco"] for r in resultado["resumo"]["riscos_de_aprendizagem"]}

    assert "esquecimento" in riscos
    assert any(
        "revisão de recuperação" in r
        for r in resultado["resumo"]["recomendacoes_para_planejamento"]
    )


# --------------------------------------------------------------------------- #
# Pré-requisitos
# --------------------------------------------------------------------------- #


def test_pre_requisito_fraco_e_detectado():
    resultado = analisar(
        entradas(
            {
                "pre_requisitos": {"Distribuições": ["Probabilidade"]},
                "resultados_exercicios": [
                    acertos("Estatística", "Probabilidade", 2, 10),
                    acertos("Estatística", "Distribuições", 8, 10),
                ],
            }
        ),
        hoje=HOJE,
    )
    estatistica = next(
        d for d in resultado["disciplinas"] if d["disciplina"] == "Estatística"
    )
    pendencia = estatistica["pre_requisitos_ausentes"][0]

    assert pendencia["topico"] == "Distribuições"
    assert pendencia["pre_requisito"] == "Probabilidade"
    assert "nao_conhece" in pendencia["situacao"]


def test_pre_requisito_sem_medicao_tambem_e_pendencia():
    resultado = analisar(
        entradas(
            {
                "pre_requisitos": {"Distribuições": ["Probabilidade"]},
                "resultados_exercicios": [acertos("Estatística", "Distribuições", 8, 10)],
            }
        ),
        hoje=HOJE,
    )
    estatistica = next(
        d for d in resultado["disciplinas"] if d["disciplina"] == "Estatística"
    )
    assert "sem evidência medida" in estatistica["pre_requisitos_ausentes"][0]["situacao"]


def test_sem_mapa_de_pre_requisitos_o_agente_nao_inventa():
    resultado = analisar(
        entradas({"resultados_exercicios": [acertos("Português", "Crase", 9, 10)]}),
        hoje=HOJE,
    )
    assert all(d["pre_requisitos_ausentes"] == [] for d in resultado["disciplinas"])
    assert any("Dependency Mapper" in o for o in resultado["observacoes"])


# --------------------------------------------------------------------------- #
# IGC, esforço e diagnóstico solicitado
# --------------------------------------------------------------------------- #


def test_igc_pondera_pela_prioridade_do_agente_02():
    dados = {
        "resultados_exercicios": [
            acertos("Português", t, 10, 10) for t in ("Crase", "Sintaxe", "Interpretação")
        ]
        + [acertos("Estatística", t, 0, 10) for t in ("Probabilidade", "Distribuições")]
    }
    resultado = analisar(entradas(dados), hoje=HOJE)
    igc = resultado["indice_geral_de_conhecimento"]

    assert igc["valor"] is not None
    assert igc["disciplinas_medidas"] == 2
    assert igc["confianca"] == "alta"
    # Português tem prioridade maior no edital, então o IGC fica acima da média simples.
    assert igc["valor"] > 0.5


def test_igc_com_cobertura_parcial_nao_e_confianca_alta():
    resultado = analisar(
        entradas(
            {
                "resultados_exercicios": [
                    acertos("Português", "Crase", 9, 10),
                    acertos("Português", "Sintaxe", 4, 12),
                    acertos("Estatística", "Probabilidade", 3, 10),
                ]
            }
        ),
        hoje=HOJE,
    )
    igc = resultado["indice_geral_de_conhecimento"]

    assert igc["cobertura_diagnostica_media"] < 0.8
    assert igc["confianca"] == "media"
    assert any(
        "provisório" in r
        for r in resultado["resumo"]["recomendacoes_para_planejamento"]
    )


def test_esforco_cai_conforme_o_dominio_medido():
    sem_evidencia = analisar(entradas(), hoje=HOJE)["esforco_total_estimado_h"]
    com_dominio = analisar(
        entradas(
            {
                "resultados_exercicios": [
                    acertos("Português", t, 10, 10)
                    for t in ("Crase", "Sintaxe", "Interpretação")
                ]
            }
        ),
        hoje=HOJE,
    )["esforco_total_estimado_h"]

    assert com_dominio < sem_evidencia


def test_diagnostico_solicitado_lista_escopo_sem_gerar_questoes():
    resultado = analisar(
        entradas({"resultados_exercicios": [acertos("Português", "Crase", 9, 10)]}),
        hoje=HOJE,
    )
    diagnostico = resultado["avaliacao_diagnostica"]

    assert diagnostico["necessaria"] is True
    escopo = {e["disciplina"]: e for e in diagnostico["escopo"]}
    assert escopo["Português"]["topicos"] == ["Sintaxe", "Interpretação"]
    assert escopo["Português"]["questoes_sugeridas"] == 10
    assert "09 Exercise Generator" in diagnostico["executor"]
    # O agente 03 não gera questões: só o escopo do que precisa ser medido.
    assert "questoes" not in resultado


def test_diagnostico_desnecessario_quando_tudo_foi_medido():
    todos = [
        acertos("Português", t, 9, 10) for t in ("Crase", "Sintaxe", "Interpretação")
    ] + [acertos("Estatística", t, 9, 10) for t in ("Probabilidade", "Distribuições")]
    resultado = analisar(entradas({"resultados_exercicios": todos}), hoje=HOJE)

    assert resultado["avaliacao_diagnostica"]["necessaria"] is False


def test_evidencia_fora_do_escopo_e_registrada_sem_entrar_no_calculo():
    resultado = analisar(
        entradas({"resultados_exercicios": [acertos("Geografia", "Clima", 9, 10)]}),
        hoje=HOJE,
    )
    fora = resultado["evidencias_consideradas"]["fora_do_escopo"]

    assert fora and fora[0]["disciplina"] == "Geografia"
    assert resultado["indice_geral_de_conhecimento"]["valor"] is None


def test_sem_mapa_do_agente_02_nao_ha_escopo_para_medir():
    resultado = analisar(entradas(com_mapa=False), hoje=HOJE)

    assert resultado["disciplinas"] == []
    assert "mapa_estrategico_do_agente_02" in resultado["lacunas"]
    assert any("Nenhuma disciplina recebida" in o for o in resultado["observacoes"])


def test_saida_declara_os_agentes_consumidores():
    resultado = analisar(entradas(), hoje=HOJE)
    assert resultado["consumido_por"] == [
        "04", "05", "06", "12", "14", "15", "17", "18", "21", "22", "23"
    ]


# --------------------------------------------------------------------------- #
# Integração
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_agente_03_recebe_perfil_e_mapa_estrategico():
    resultado = await MasterOrchestrator().orquestrar(
        "Monte um cronograma para o concurso",
        dados_usuario={
            "objetivo": "Passar no concurso fiscal",
            "edital": EDITAL,
            "escolaridade": "Superior completo",
            "horas_por_dia": 3,
            "dias_por_semana": 5,
            "data_prova": "2027-01-01",
            "profissao": "Analista",
            "rotina": "Trabalho durante o dia",
            "experiencia_anterior": "nenhuma",
            "preferencia_estudo": "questões",
            "idade": 30,
            "resultados_simulados": [
                {
                    "disciplina": "Português",
                    "topico": "Crase",
                    "acertos": 9,
                    "total": 10,
                    "tipo": "simulado",
                }
            ],
        },
    )
    mapa = resultado.saidas["03"].conteudo

    assert [d["disciplina"] for d in mapa["disciplinas"]] == ["Português", "Estatística"]
    assert mapa["avaliacao_diagnostica"]["necessaria"] is True
    assert resultado.validacao.aprovado is True


@pytest.mark.asyncio
async def test_agente_03_roda_depois_do_01_e_do_02():
    resultado = await MasterOrchestrator().orquestrar("Qual é o meu nível?")
    ondas = {
        agente.split()[0]: onda["onda"]
        for onda in resultado.ordem_execucao
        for agente in onda["agentes"]
    }
    assert ondas["01"] < ondas["02"] < ondas["03"]
