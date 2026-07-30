from datetime import date

import pytest

from app.studyos.agentes.conhecimento import analisar as analisar_conhecimento
from app.studyos.agentes.curriculo import construir as construir_curriculo
from app.studyos.agentes.dependencias import mapear
from app.studyos.agentes.objetivo import analisar as analisar_objetivo
from app.studyos.agentes.perfil import analisar as analisar_perfil
from app.studyos.agentes.roadmap import (
    PROPORCAO_CONTEUDO,
    PROPORCAO_EXERCICIOS,
    PROPORCAO_REVISAO,
    SIMULADO_A_CADA_DIAS_DE_ESTUDO,
    construir,
)
from app.studyos.orchestrator import MasterOrchestrator

HOJE = date(2026, 1, 5)  # segunda-feira

EDITAL = {
    "Estatística": {
        "questoes": 10,
        "topicos": ["Conjuntos", "Probabilidade", "Distribuições"],
    },
    "Português": {"questoes": 20, "topicos": ["Crase", "Sintaxe"]},
}

PRE = {"Probabilidade": ["Conjuntos"], "Distribuições": ["Probabilidade"]}


def cadeia(dados=None, edital=EDITAL):
    """Roda 01–05 de verdade e devolve as entradas prontas para o 06."""
    base = {
        "objetivo": "Passar no concurso fiscal",
        "edital": edital,
        "escolaridade": "Superior completo",
        "profissao": "Analista",
        "rotina": "Estudo em casa",
        "horas_por_dia": 4,
        "dias_por_semana": 5,
        "idade": 30,
        "experiencia_anterior": "nenhuma",
        "preferencia_estudo": "questões",
        "data_prova": "2026-03-01",
        "pre_requisitos": PRE,
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
    return {
        "solicitacao": "",
        "dados_usuario": base,
        "saidas_anteriores": {"01": m1, "02": m2, "03": m3, "04": m4, "05": m5},
    }


def sessoes_de_conteudo(plano):
    return [
        s
        for dia in plano["cronograma"]
        for s in dia["sessoes"]
        if s["tipo"] == "conteudo"
    ]


def primeira_ocorrencia(plano, nome):
    for indice, dia in enumerate(plano["cronograma"]):
        for sessao in dia["sessoes"]:
            if sessao["conteudo"] == nome:
                return indice
    return None


# --------------------------------------------------------------------------- #
# Resumo e estrutura do cronograma
# --------------------------------------------------------------------------- #


def test_resumo_geral_usa_o_perfil_cognitivo():
    plano = construir(cadeia(), hoje=HOJE)
    resumo = plano["resumo_geral"]

    assert resumo["data_inicio"] == "2026-01-05"
    assert resumo["data_da_prova"] == "2026-03-01"
    assert resumo["total_horas_diarias"] == 3.4  # 4h × fator 0.85
    assert resumo["dias_de_estudo_por_semana"] == [
        "segunda",
        "terca",
        "quarta",
        "quinta",
        "sexta",
    ]


def test_cronograma_so_ocupa_os_dias_de_estudo():
    plano = construir(cadeia(), hoje=HOJE)
    dias = {dia["dia_semana"] for dia in plano["cronograma"]}

    assert dias <= {"segunda", "terca", "quarta", "quinta", "sexta"}
    assert "sabado" not in dias


def test_dias_da_semana_nomeados_sao_respeitados():
    plano = construir(
        cadeia({"dias_da_semana": ["sabado", "domingo"]}), hoje=HOJE
    )
    assert {dia["dia_semana"] for dia in plano["cronograma"]} == {"sabado", "domingo"}


def test_todo_dia_tem_conteudo_exercicios_e_revisao():
    plano = construir(cadeia(), hoje=HOJE)

    for dia in plano["cronograma"]:
        tipos = {s["tipo"] for s in dia["sessoes"]}
        assert "conteudo" in tipos
        assert tipos & {"exercicios", "simulado"}
        assert "revisao" in tipos


def test_carga_diaria_nao_ultrapassa_o_teto_do_perfil():
    plano = construir(cadeia(), hoje=HOJE)
    teto = plano["resumo_geral"]["total_horas_diarias"]

    assert all(dia["tempo_total_h"] <= teto + 0.01 for dia in plano["cronograma"])


def test_proporcoes_do_dia_seguem_as_constantes():
    plano = construir(cadeia(), hoje=HOJE)
    dia = plano["cronograma"][0]
    teto = plano["resumo_geral"]["total_horas_diarias"]

    por_tipo = {}
    for sessao in dia["sessoes"]:
        por_tipo[sessao["tipo"]] = por_tipo.get(sessao["tipo"], 0) + sessao["tempo_estimado_h"]

    assert por_tipo["conteudo"] == pytest.approx(teto * PROPORCAO_CONTEUDO, abs=0.05)
    assert por_tipo["exercicios"] == pytest.approx(teto * PROPORCAO_EXERCICIOS, abs=0.01)
    assert por_tipo["revisao"] == pytest.approx(teto * PROPORCAO_REVISAO, abs=0.01)


EDITAL_GRANDE = {
    f"Disciplina {i}": {"topicos": [f"Tópico {i}.{j}" for j in range(6)]}
    for i in range(4)
}


def test_simulado_entra_periodicamente():
    plano = construir(
        cadeia({"data_prova": "2026-06-01"}, edital=EDITAL_GRANDE), hoje=HOJE
    )
    simulados = [
        dia
        for dia in plano["cronograma"]
        if any(s["tipo"] == "simulado" for s in dia["sessoes"])
    ]
    assert simulados
    indice = plano["cronograma"].index(simulados[0]) + 1
    assert indice == SIMULADO_A_CADA_DIAS_DE_ESTUDO


# --------------------------------------------------------------------------- #
# Dependências e escopo
# --------------------------------------------------------------------------- #


def test_dependencia_do_agente_05_nunca_e_violada():
    plano = construir(cadeia(), hoje=HOJE)

    conjuntos = primeira_ocorrencia(plano, "Conjuntos")
    probabilidade = primeira_ocorrencia(plano, "Probabilidade")
    distribuicoes = primeira_ocorrencia(plano, "Distribuições")

    assert conjuntos < probabilidade < distribuicoes


def test_pre_requisito_so_libera_depois_de_totalmente_alocado():
    # Capacidade pequena obriga a partir o tópico em várias sessões.
    plano = construir(cadeia({"horas_por_dia": 1}), hoje=HOJE)
    dias_de_conjuntos = [
        indice
        for indice, dia in enumerate(plano["cronograma"])
        for s in dia["sessoes"]
        if s["conteudo"] == "Conjuntos"
    ]
    assert len(dias_de_conjuntos) > 1  # partido
    assert max(dias_de_conjuntos) < primeira_ocorrencia(plano, "Probabilidade")


def test_apenas_folhas_entram_na_agenda():
    plano = construir(cadeia({"subtopicos": {"Crase": ["Regra geral", "Casos especiais"]}}), hoje=HOJE)
    conteudos = {s["conteudo"] for s in sessoes_de_conteudo(plano)}

    assert "Regra geral" in conteudos
    assert "Crase" not in conteudos  # virou pai, não folha
    assert "Português" not in conteudos


def test_conteudo_dominado_nao_entra_no_cronograma():
    dados = {
        "resultados_exercicios": [
            {"disciplina": "Português", "topico": "Crase", "acertos": 10, "total": 10}
        ]
    }
    plano = construir(cadeia(dados), hoje=HOJE)
    assert "Crase" not in {s["conteudo"] for s in sessoes_de_conteudo(plano)}


def test_topico_grande_e_partido_em_sessoes_numeradas():
    plano = construir(cadeia({"horas_por_dia": 1}), hoje=HOJE)
    partes = [
        s
        for s in sessoes_de_conteudo(plano)
        if s["conteudo"] == "Conjuntos" and s["parte"]
    ]
    assert [p["parte"] for p in partes][:2] == ["parte 1", "parte 2"]


# --------------------------------------------------------------------------- #
# Fadiga e alternância
# --------------------------------------------------------------------------- #


def test_dia_alterna_disciplinas_quando_ha_alternativa():
    plano = construir(cadeia({"horas_por_dia": 8}), hoje=HOJE)
    primeiro_dia = [
        s["disciplina"] for s in plano["cronograma"][0]["sessoes"] if s["tipo"] == "conteudo"
    ]
    assert len(primeiro_dia) >= 2
    assert primeiro_dia[0] != primeiro_dia[1]


# --------------------------------------------------------------------------- #
# Metas e indicadores
# --------------------------------------------------------------------------- #


def test_metas_diaria_semanal_e_mensal():
    plano = construir(cadeia(), hoje=HOJE)
    metas = plano["metas"]

    assert metas["diaria"]["horas"] == plano["resumo_geral"]["total_horas_diarias"]
    assert metas["semanal"][0]["semana"].startswith("2026-S")
    assert metas["semanal"][0]["dias"] <= 5
    assert metas["mensal"][0]["mes"] == "2026-01"
    assert metas["mensal"][0]["disciplinas"]


def test_indicadores_de_cobertura_e_risco_baixo():
    plano = construir(cadeia(), hoje=HOJE)
    indicadores = plano["indicadores"]

    assert indicadores["percentual_planejado"] == 1.0
    assert indicadores["horas_restantes"] == 0.0
    assert indicadores["risco_de_atraso"] == "baixo"
    assert plano["conteudos_nao_alocados"] == []


def test_conteudo_que_nao_cabe_no_prazo_nao_desaparece():
    plano = construir(
        cadeia({"data_prova": "2026-01-07", "horas_por_dia": 1}), hoje=HOJE
    )

    assert plano["conteudos_nao_alocados"]
    assert plano["indicadores"]["risco_de_atraso"] == "alto"
    assert plano["indicadores"]["horas_restantes"] > 0
    assert any(
        r["risco"] == "conteudo_sem_espaco_no_prazo" for r in plano["riscos"]
    )
    assert any("não descartado" in o for o in plano["observacoes"])


def test_percentual_concluido_reflete_o_grafo():
    dados = {
        "resultados_exercicios": [
            {"disciplina": "Português", "topico": "Crase", "acertos": 10, "total": 10}
        ]
    }
    plano = construir(cadeia(dados), hoje=HOJE)
    assert plano["indicadores"]["percentual_concluido"] > 0


# --------------------------------------------------------------------------- #
# Replanejamento
# --------------------------------------------------------------------------- #


def test_faltas_sao_puladas_e_viram_gatilho():
    plano = construir(
        cadeia({"faltas": ["2026-01-05", "2026-01-06"]}), hoje=HOJE
    )
    datas = {dia["data"] for dia in plano["cronograma"]}

    assert "2026-01-05" not in datas
    assert "2026-01-06" not in datas
    assert "faltas informadas" in plano["replanejamento"]["gatilhos_detectados"]
    assert any(r["risco"] == "faltas_registradas" for r in plano["riscos"])


def test_progresso_informado_sai_do_cronograma():
    plano = construir(cadeia({"progresso": ["Conjuntos"]}), hoje=HOJE)
    assert "Conjuntos" not in {s["conteudo"] for s in sessoes_de_conteudo(plano)}
    assert "progresso informado" in plano["replanejamento"]["gatilhos_detectados"]


def test_mudanca_de_data_encurta_o_plano():
    curto = construir(
        cadeia({"data_prova": "2026-01-20"}, edital=EDITAL_GRANDE), hoje=HOJE
    )
    longo = construir(
        cadeia({"data_prova": "2026-06-01"}, edital=EDITAL_GRANDE), hoje=HOJE
    )

    assert len(curto["cronograma"]) < len(longo["cronograma"])
    assert curto["resumo_geral"]["data_da_prova"] == "2026-01-20"


def test_replanejamento_e_sempre_automatico():
    plano = construir(cadeia(), hoje=HOJE)
    assert plano["replanejamento"]["automatico"] is True


# --------------------------------------------------------------------------- #
# Limites
# --------------------------------------------------------------------------- #


def test_sem_grafo_nao_ha_cronograma():
    plano = construir({"dados_usuario": {}, "saidas_anteriores": {}}, hoje=HOJE)

    assert plano["cronograma"] == []
    assert plano["confiabilidade"] == "baixa"
    assert "grafo_de_aprendizagem_do_agente_05" in plano["lacunas"]


def test_sem_carga_diaria_o_plano_declara_o_impedimento():
    entradas = cadeia()
    entradas["saidas_anteriores"]["01"]["carga_maxima_diaria"] = {"horas": None}
    plano = construir(entradas, hoje=HOJE)

    assert plano["cronograma"] == []
    assert any("Carga máxima diária indisponível" in o for o in plano["observacoes"])


def test_saida_nao_ensina_nem_gera_conteudo():
    plano = construir(cadeia(), hoje=HOJE)
    proibidos = {"aulas", "exercicios_gerados", "questoes", "resumos", "explicacoes"}
    assert proibidos.isdisjoint(plano)


def test_revisao_declara_que_e_provisoria_ate_o_agente_14():
    plano = construir(cadeia(), hoje=HOJE)
    revisao = next(
        s for s in plano["cronograma"][0]["sessoes"] if s["tipo"] == "revisao"
    )
    assert "agente 14" in revisao["origem"]


def test_saida_declara_os_agentes_consumidores():
    plano = construir(cadeia(), hoje=HOJE)
    assert plano["consumido_por"] == [
        "07", "09", "10", "11", "14", "15", "16", "19", "20", "21", "22", "23", "24"
    ]


# --------------------------------------------------------------------------- #
# Integração
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_agente_06_no_fluxo_completo():
    resultado = await MasterOrchestrator().orquestrar(
        "Monte um cronograma para o concurso",
        dados_usuario={
            "objetivo": "Passar no concurso fiscal",
            "edital": EDITAL,
            "pre_requisitos": PRE,
            "escolaridade": "Superior completo",
            "horas_por_dia": 3,
            "dias_por_semana": 5,
            "data_prova": "2027-01-01",
            "profissao": "Analista",
            "rotina": "Trabalho durante o dia",
            "experiencia_anterior": "nenhuma",
            "preferencia_estudo": "questões",
            "idade": 30,
        },
    )
    plano = resultado.saidas["06"].conteudo

    assert plano["cronograma"]
    assert plano["indicadores"]["risco_de_atraso"] == "baixo"
    assert plano["resumo_geral"]["data_conclusao_prevista"] is not None
    assert resultado.validacao.aprovado is True


@pytest.mark.asyncio
async def test_agente_06_roda_depois_do_grafo():
    resultado = await MasterOrchestrator().orquestrar("Monte um cronograma")
    ondas = {
        agente.split()[0]: onda["onda"]
        for onda in resultado.ordem_execucao
        for agente in onda["agentes"]
    }
    assert ondas["05"] < ondas["06"]
