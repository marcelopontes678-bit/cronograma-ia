from datetime import date

import pytest

from app.studyos.agentes.aula import (
    CHAVES_DE_SECAO,
    AulaBloqueada,
    gerar,
    montar,
    montar_briefing,
)
from app.studyos.agentes.conhecimento import analisar as analisar_conhecimento
from app.studyos.agentes.curriculo import construir as construir_curriculo
from app.studyos.agentes.dependencias import mapear
from app.studyos.agentes.objetivo import analisar as analisar_objetivo
from app.studyos.agentes.perfil import analisar as analisar_perfil
from app.studyos.agentes.roadmap import construir as construir_roadmap
from app.studyos.orchestrator import MasterOrchestrator

HOJE = date(2026, 1, 5)

EDITAL = {
    "Estatística": {
        "questoes": 10,
        "topicos": ["Conjuntos", "Probabilidade", "Distribuições"],
    },
    "Português": {"questoes": 20, "topicos": ["Crase"]},
}

PRE = {"Probabilidade": ["Conjuntos"], "Distribuições": ["Probabilidade"]}


def cadeia(dados=None, edital=EDITAL):
    """Roda 01–06 de verdade e devolve as entradas prontas para o 07."""
    base = {
        "objetivo": "Passar no concurso fiscal",
        "edital": edital,
        "pre_requisitos": PRE,
        "escolaridade": "Superior completo",
        "profissao": "Analista",
        "rotina": "Estudo em casa",
        "horas_por_dia": 4,
        "dias_por_semana": 5,
        "idade": 30,
        "experiencia_anterior": "nenhuma",
        "preferencia_estudo": "videoaula e mapa mental",
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
    return {
        "solicitacao": "",
        "dados_usuario": base,
        "saidas_anteriores": {"01": m1, "03": m3, "04": m4, "05": m5, "06": m6},
    }


def redator_falso(briefing):
    """Redator de teste: devolve todas as seções pedidas."""
    return {
        secao["chave"]: (
            ["ponto A", "ponto B"]
            if secao["chave"] == "pontos_chave"
            else f"texto de {secao['chave']}"
        )
        for secao in briefing["secoes"]
    }


# --------------------------------------------------------------------------- #
# Portão de pré-requisitos — a regra que não pode depender do modelo
# --------------------------------------------------------------------------- #


def test_conteudo_bloqueado_nao_vira_aula():
    aula = gerar(cadeia({"conteudo_solicitado": "Probabilidade"}))

    assert aula["gerada"] is False
    assert aula["status"] == "bloqueada_por_pre_requisito"
    assert aula["bloqueio"]["pre_requisitos_pendentes"] == ["Conjuntos"]
    assert all(aula[chave] is None for chave in CHAVES_DE_SECAO)


def test_redator_nao_e_chamado_para_conteudo_bloqueado():
    chamadas = []

    def redator(briefing):
        chamadas.append(briefing)
        return redator_falso(briefing)

    aula = gerar(cadeia({"conteudo_solicitado": "Distribuições"}), redator=redator)

    assert chamadas == []
    assert aula["status"] == "bloqueada_por_pre_requisito"


def test_montar_recusa_aula_bloqueada_mesmo_com_texto_pronto():
    briefing = montar_briefing(cadeia({"conteudo_solicitado": "Probabilidade"}))

    with pytest.raises(AulaBloqueada, match="Conjuntos"):
        montar(briefing, redator_falso(briefing))


def test_pre_requisito_concluido_libera_a_aula():
    dados = {
        "conteudo_solicitado": "Probabilidade",
        "resultados_exercicios": [
            {
                "disciplina": "Estatística",
                "topico": "Conjuntos",
                "acertos": 10,
                "total": 10,
            }
        ],
    }
    aula = gerar(cadeia(dados), redator=redator_falso)

    assert aula["bloqueio"] is None
    assert aula["gerada"] is True
    assert aula["pre_requisitos"] == ["Conjuntos"]


def test_bloqueio_por_ancestral_tambem_impede():
    dados = {
        "conteudo_solicitado": "Regra geral",
        "subtopicos": {"Probabilidade": ["Regra geral"]},
    }
    aula = gerar(cadeia(dados))

    assert aula["status"] == "bloqueada_por_pre_requisito"
    assert aula["bloqueio"]["pendentes_por_ancestral"] == ["Conjuntos"]


# --------------------------------------------------------------------------- #
# Sem redator: pendente, nunca inventada
# --------------------------------------------------------------------------- #


def test_sem_redator_as_secoes_ficam_pendentes():
    aula = gerar(cadeia({"conteudo_solicitado": "Crase"}))

    assert aula["gerada"] is False
    assert aula["status"] == "pendente_de_redacao"
    assert aula["secoes_pendentes"] == list(CHAVES_DE_SECAO)
    assert all(aula[chave] is None for chave in CHAVES_DE_SECAO)
    assert any("nada foi preenchido por invenção" in o for o in aula["observacoes"])


def test_estrutura_deterministica_existe_mesmo_sem_redacao():
    aula = gerar(cadeia({"conteudo_solicitado": "Crase"}))

    assert aula["titulo"] == "Crase — Português"
    assert aula["objetivo"]
    assert aula["tempo_estimado_h"] == 2.5
    assert aula["nivel_dificuldade"] == "medio"
    assert aula["proximo_conteudo_recomendado"] is not None


def test_briefing_traz_as_oito_secoes_na_ordem_da_spec():
    briefing = montar_briefing(cadeia({"conteudo_solicitado": "Crase"}))
    chaves = [s["chave"] for s in briefing["secoes"]]

    assert chaves == list(CHAVES_DE_SECAO)
    assert chaves[0] == "introducao"
    assert chaves[-1] == "pontos_chave"
    assert "Contextualização" in briefing["secoes"][0]["etapa"]


# --------------------------------------------------------------------------- #
# Adaptação ao estudante
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "acertos,total,esperado",
    [
        (1, 10, "iniciante"),
        (4, 10, "basico"),
        (7, 10, "intermediario"),
        (10, 10, "avancado"),
    ],
)
def test_nivel_da_linguagem_vem_do_dominio_medido(acertos, total, esperado):
    dados = {
        "conteudo_solicitado": "Crase",
        "resultados_exercicios": [
            {
                "disciplina": "Português",
                "topico": "Crase",
                "acertos": acertos,
                "total": total,
            }
        ],
    }
    aula = gerar(cadeia(dados))
    assert aula["nivel_do_estudante"]["nivel"] == esperado
    assert "domínio medido" in aula["nivel_do_estudante"]["base"]


def test_sem_medicao_o_nivel_cai_para_o_conservador():
    aula = gerar(cadeia({"conteudo_solicitado": "Crase"}))
    nivel = aula["nivel_do_estudante"]

    assert nivel["nivel"] in ("iniciante", "basico")
    assert nivel["confianca"] in ("baixa", "nenhuma")
    assert any("baixa confiança" in o for o in aula["observacoes"])


def test_estilo_de_aprendizagem_vira_diretriz_de_formato():
    briefing = montar_briefing(cadeia({"conteudo_solicitado": "Crase"}))

    assert briefing["estilo_de_aprendizagem"] == "visual"
    assert any("esquemas" in d for d in briefing["diretrizes"])


# --------------------------------------------------------------------------- #
# Fontes e coerência
# --------------------------------------------------------------------------- #


def test_material_oficial_vira_restricao_de_nao_contradicao():
    briefing = montar_briefing(
        cadeia(
            {
                "conteudo_solicitado": "Crase",
                "bibliografia": ["Gramática oficial da banca"],
            }
        )
    )
    assert briefing["fontes"]["materiais_oficiais"] == ["Gramática oficial da banca"]
    assert "Não contradizer" in briefing["fontes"]["restricao"]


def test_ausencia_de_material_oficial_e_declarada():
    aula = gerar(cadeia({"conteudo_solicitado": "Crase"}))

    assert "bibliografia_oficial" in aula["lacunas"]
    assert any("material oficial" in o for o in aula["observacoes"])


def test_coerencia_separa_o_que_pode_e_o_que_nao_pode_pressupor():
    dados = {
        "conteudo_solicitado": "Probabilidade",
        "resultados_exercicios": [
            {
                "disciplina": "Estatística",
                "topico": "Conjuntos",
                "acertos": 10,
                "total": 10,
            }
        ],
    }
    briefing = montar_briefing(cadeia(dados))
    coerencia = briefing["coerencia"]

    assert "Conjuntos" in coerencia["pode_pressupor"]
    assert "Distribuições" in coerencia["nao_pode_pressupor"]


def test_briefing_lista_as_proibicoes_da_spec():
    briefing = montar_briefing(cadeia({"conteudo_solicitado": "Crase"}))
    texto = " ".join(briefing["proibicoes"])

    for proibido in ("exercícios", "flashcards", "simulados", "cronograma", "desempenho"):
        assert proibido in texto


# --------------------------------------------------------------------------- #
# Montagem com redator
# --------------------------------------------------------------------------- #


def test_aula_completa_preenche_todas_as_secoes():
    aula = gerar(cadeia({"conteudo_solicitado": "Crase"}), redator=redator_falso)

    assert aula["gerada"] is True
    assert aula["status"] == "gerada"
    assert aula["secoes_pendentes"] == []
    assert aula["desenvolvimento"] == "texto de desenvolvimento"
    assert aula["pontos_chave"] == ["ponto A", "ponto B"]


def test_secao_faltante_mantem_a_aula_pendente():
    def incompleto(briefing):
        secoes = redator_falso(briefing)
        del secoes["erros_comuns"]
        return secoes

    aula = gerar(cadeia({"conteudo_solicitado": "Crase"}), redator=incompleto)

    assert aula["gerada"] is False
    assert aula["status"] == "pendente_de_redacao"
    assert aula["secoes_pendentes"] == ["erros_comuns"]


def test_secao_fora_da_estrutura_e_descartada():
    def com_extra(briefing):
        secoes = redator_falso(briefing)
        secoes["exercicios"] = "5 questões inventadas"
        secoes["cronograma"] = "estude terça"
        return secoes

    aula = gerar(cadeia({"conteudo_solicitado": "Crase"}), redator=com_extra)

    assert aula["secoes_ignoradas"] == ["cronograma", "exercicios"]
    assert "exercicios" not in aula
    assert "cronograma" not in aula


# --------------------------------------------------------------------------- #
# Seleção de conteúdo e limites
# --------------------------------------------------------------------------- #


def test_sem_pedido_explicito_usa_o_proximo_conteudo_do_plano():
    aula = gerar(cadeia())
    assert aula["conteudo"]["nome"] == "Conjuntos"


def test_conteudo_inexistente_e_reportado_sem_aula():
    aula = gerar(cadeia({"conteudo_solicitado": "Cálculo Tensorial"}))

    assert aula["gerada"] is False
    assert aula["status"] == "sem_conteudo"
    assert "não encontrado" in aula["erro"]


def test_sem_grafo_nao_ha_aula():
    aula = gerar({"dados_usuario": {}, "saidas_anteriores": {}})
    assert aula["status"] == "sem_conteudo"


def test_saida_declara_os_agentes_consumidores():
    aula = gerar(cadeia({"conteudo_solicitado": "Crase"}))
    assert aula["consumido_por"] == ["08", "09", "10", "11", "13", "16", "24"]


# --------------------------------------------------------------------------- #
# Integração
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_agente_07_no_fluxo_completo():
    resultado = await MasterOrchestrator().orquestrar(
        "Explique o conteúdo do meu edital",
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
    aula = resultado.saidas["07"].conteudo

    assert aula["status"] == "pendente_de_redacao"
    assert aula["briefing"]["secoes"]
    assert resultado.validacao.aprovado is True


@pytest.mark.asyncio
async def test_agente_07_roda_depois_do_plano():
    resultado = await MasterOrchestrator().orquestrar("Explique derivadas")
    ondas = {
        agente.split()[0]: onda["onda"]
        for onda in resultado.ordem_execucao
        for agente in onda["agentes"]
    }
    assert ondas["06"] < ondas["07"]


@pytest.mark.asyncio
async def test_redator_conectado_pelo_runner_produz_aula_completa():
    from app.studyos.runner import RunnerEstrutural

    orquestrador = MasterOrchestrator(
        RunnerEstrutural(redatores={"07": redator_falso})
    )
    resultado = await orquestrador.orquestrar(
        "Explique o conteúdo do meu edital",
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
        },
    )
    aula = resultado.saidas["07"].conteudo

    assert aula["status"] == "gerada"
    assert aula["desenvolvimento"] == "texto de desenvolvimento"
    # Os demais agentes continuam determinísticos.
    assert resultado.saidas["06"].conteudo["cronograma"]
