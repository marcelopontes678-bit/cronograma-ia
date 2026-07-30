from datetime import date

import pytest

from app.studyos.agentes.aula import gerar as gerar_aula
from app.studyos.agentes.conhecimento import analisar as analisar_conhecimento
from app.studyos.agentes.curriculo import construir as construir_curriculo
from app.studyos.agentes.dependencias import mapear
from app.studyos.agentes.exemplos import gerar as gerar_exemplos
from app.studyos.agentes.exercicios import gerar as gerar_exercicios
from app.studyos.agentes.flashcards import gerar as gerar_flashcards
from app.studyos.agentes.objetivo import analisar as analisar_objetivo
from app.studyos.agentes.perfil import analisar as analisar_perfil
from app.studyos.agentes.resumos import (
    CHAVES_DE_SECAO,
    LIMITES_DE_PALAVRAS,
    PALAVRAS_POR_MINUTO,
    ConteudoNaoEstudado,
    gerar,
    montar,
    montar_briefing,
)
from app.studyos.agentes.roadmap import construir as construir_roadmap
from app.studyos.orchestrator import MasterOrchestrator
from app.studyos.runner import RunnerEstrutural

HOJE = date(2026, 1, 5)

EDITAL = {
    "Estatística": {"questoes": 10, "topicos": ["Conjuntos", "Probabilidade"]},
    "Português": {"questoes": 20, "topicos": ["Crase"]},
}

PRE = {"Probabilidade": ["Conjuntos"]}
PONTOS = ["regra geral", "casos proibidos"]


def redator_de_aula_com(pontos):
    def redator(briefing):
        return {
            secao["chave"]: (
                list(pontos)
                if secao["chave"] == "pontos_chave"
                else f"texto de {secao['chave']}"
            )
            for secao in briefing["secoes"]
        }

    return redator


redator_de_aula = redator_de_aula_com(PONTOS)


def redator_de_exemplos(briefing):
    return {
        slot["chave"]: {"enunciado": f"ex de {slot['chave']}", "por_que_funciona": "pq"}
        for slot in briefing["slots"]
        if slot["aplicavel"]
    }


def redator_de_questoes(briefing):
    return {
        slot["numero"]: {
            "enunciado": f"Q{slot['numero']}",
            "resposta": "r",
            "explicacao": "e",
        }
        for slot in briefing["slots"]
    }


def redator_de_cartoes(briefing):
    return {
        slot["numero"]: {
            "pergunta": f"O que é {slot['conceito']}?"
            if slot["tipo"] not in ("cloze",)
            else f"{slot['conceito']} é ___ .",
            "resposta": "curta",
        }
        for slot in briefing["slots"]
    }


def redator_de_resumos(briefing, palavras=None):
    """Resumo de teste: contém todos os conceitos e respeita a progressão."""
    conceitos = " ".join(briefing["conceitos_chave"])
    tamanhos = palavras or {"resumo_1min": 30, "resumo_5min": 120, "resumo_completo": 300}
    saida = {}
    for secao in briefing["secoes"]:
        if not secao["aplicavel"]:
            continue
        chave = secao["chave"]
        if chave in tamanhos:
            enchimento = " ".join(["palavra"] * tamanhos[chave])
            saida[chave] = f"{conceitos} {enchimento}"
        else:
            saida[chave] = f"texto de {chave} com {conceitos}"
    return saida


def cadeia(dados=None, aula_redigida=True, conteudo="Crase", pontos=None):
    """Roda 01–10 de verdade e devolve as entradas prontas para o 11."""
    base = {
        "objetivo": "Passar no concurso fiscal",
        "edital": EDITAL,
        "pre_requisitos": PRE,
        "subtopicos": {"Crase": ["Regra geral", "Exceções"]},
        "escolaridade": "Superior completo",
        "profissao": "Analista",
        "rotina": "Estudo em casa",
        "horas_por_dia": 4,
        "dias_por_semana": 5,
        "idade": 30,
        "experiencia_anterior": "nenhuma",
        "preferencia_estudo": "questões",
        "data_prova": "2026-06-01",
        "conteudo_solicitado": conteudo,
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
    ant = {"01": m1, "03": m3, "04": m4, "05": m5, "06": m6}
    redator = redator_de_aula_com(pontos or PONTOS) if aula_redigida else None
    m7 = gerar_aula({"dados_usuario": base, "saidas_anteriores": ant}, redator=redator)
    m8 = gerar_exemplos(
        {"dados_usuario": base, "saidas_anteriores": {**ant, "07": m7}},
        redator=redator_de_exemplos if aula_redigida else None,
    )
    m9 = gerar_exercicios(
        {"dados_usuario": base, "saidas_anteriores": {**ant, "07": m7, "08": m8}},
        redator=redator_de_questoes if aula_redigida else None,
    )
    m10 = gerar_flashcards(
        {
            "dados_usuario": base,
            "saidas_anteriores": {**ant, "07": m7, "08": m8, "09": m9},
        },
        redator=redator_de_cartoes if aula_redigida else None,
    )
    return {
        "solicitacao": "",
        "dados_usuario": base,
        "saidas_anteriores": {**ant, "07": m7, "08": m8, "09": m9, "10": m10},
    }


# --------------------------------------------------------------------------- #
# Portão
# --------------------------------------------------------------------------- #


def test_conteudo_nao_estudado_nao_vira_resumo():
    resumo = gerar(cadeia(aula_redigida=False))

    assert resumo["gerado"] is False
    assert resumo["status"] == "bloqueado"
    assert resumo["bloqueio"]["motivo"] == "conteudo_nao_estudado"
    assert all(resumo[chave] is None for chave in CHAVES_DE_SECAO)


def test_montar_recusa_resumo_de_conteudo_nao_estudado():
    briefing = montar_briefing(cadeia(aula_redigida=False))

    with pytest.raises(ConteudoNaoEstudado):
        montar(briefing, {"resumo_1min": "qualquer coisa"})


# --------------------------------------------------------------------------- #
# O tempo prometido é conferido
# --------------------------------------------------------------------------- #


def test_resumo_de_1_minuto_que_nao_cabe_em_1_minuto_e_recusado():
    def longo(briefing):
        return redator_de_resumos(
            briefing, {"resumo_1min": 400, "resumo_5min": 500, "resumo_completo": 600}
        )

    resumo = gerar(cadeia(), redator=longo)
    excedida = next(e for e in resumo["secoes_excedidas"] if e["secao"] == "resumo_1min")

    assert excedida["palavras"] > LIMITES_DE_PALAVRAS["resumo_1min"]
    assert "não cabe no tempo prometido" in excedida["motivo"]
    assert resumo["resumo_1min"] is None
    assert resumo["gerado"] is False


def test_resumo_de_5_minutos_tem_orcamento_proprio():
    def longo(briefing):
        return redator_de_resumos(
            briefing,
            {"resumo_1min": 30, "resumo_5min": 2000, "resumo_completo": 2100},
        )

    resumo = gerar(cadeia(), redator=longo)
    assert [e["secao"] for e in resumo["secoes_excedidas"]] == ["resumo_5min"]
    assert resumo["resumo_1min"] is not None


def test_resumo_completo_nao_tem_teto():
    def enorme(briefing):
        return redator_de_resumos(
            briefing,
            {"resumo_1min": 30, "resumo_5min": 120, "resumo_completo": 5000},
        )

    resumo = gerar(cadeia(), redator=enorme)
    assert resumo["secoes_excedidas"] == []
    assert resumo["gerado"] is True


def test_tempo_de_leitura_e_calculado():
    resumo = gerar(cadeia(), redator=redator_de_resumos)
    tempos = resumo["tempo_estimado_de_leitura_min"]

    assert tempos["resumo_1min"] <= 1.0 * 1.15
    assert tempos["resumo_5min"] < tempos["resumo_completo"]
    assert tempos["resumo_completo"] == pytest.approx(
        len(resumo["resumo_completo"].split()) / PALAVRAS_POR_MINUTO, abs=0.1
    )


def test_progressao_de_tamanho_e_verificada():
    def invertido(briefing):
        return redator_de_resumos(
            briefing,
            {"resumo_1min": 200, "resumo_5min": 100, "resumo_completo": 50},
        )

    resumo = gerar(cadeia(), redator=invertido)

    assert resumo["progressao_de_tamanho_ok"] is False
    assert resumo["gerado"] is False
    assert any("não crescem em tamanho" in o for o in resumo["observacoes"])


# --------------------------------------------------------------------------- #
# Nenhum conceito essencial some
# --------------------------------------------------------------------------- #


def test_conceito_ausente_do_resumo_completo_e_denunciado():
    def sem_conceito(briefing):
        saida = redator_de_resumos(briefing)
        saida["resumo_completo"] = "texto sem nenhum dos conceitos essenciais"
        return saida

    resumo = gerar(cadeia(), redator=sem_conceito)

    assert resumo["conceitos_ausentes_no_resumo"] == PONTOS
    assert resumo["gerado"] is False
    assert any("proíbe removê-los" in o for o in resumo["observacoes"])


def test_resumo_com_todos_os_conceitos_e_aprovado():
    resumo = gerar(cadeia(), redator=redator_de_resumos)

    assert resumo["conceitos_ausentes_no_resumo"] == []
    assert resumo["gerado"] is True
    assert resumo["status"] == "gerado"


def test_conceitos_vem_da_aula_dos_flashcards_e_dos_exercicios():
    briefing = montar_briefing(cadeia())
    assert set(PONTOS).issubset(set(briefing["conceitos_chave"]))


# --------------------------------------------------------------------------- #
# Material derivado, não redigido
# --------------------------------------------------------------------------- #


def test_mapa_mental_vem_da_arvore_curricular():
    resumo = gerar(cadeia(), redator=redator_de_resumos)
    mapa = resumo["mapa_mental_textual"]

    assert "Português" in mapa
    assert "Crase" in mapa
    assert "Regra geral" in mapa  # subtópico informado
    assert "└──" in mapa


def test_checklist_tem_um_item_por_conceito():
    resumo = gerar(cadeia(), redator=redator_de_resumos)
    checklist = resumo["checklist_de_revisao"]

    assert len(checklist) == len(resumo["conceitos_chave"])
    assert checklist[0]["item"].startswith("Consigo explicar")
    assert "revisao_frequente" in checklist[0]


def test_erros_comuns_sao_copiados_e_nao_reescritos():
    resumo = gerar(cadeia(), redator=redator_de_resumos)
    erros = resumo["erros_comuns"]

    assert erros["da_aula"] == "texto de erros_comuns"
    assert erros["contraexemplo"] == "ex de contraexemplo"
    assert "sem reescrita" in erros["origem"]


def test_proximos_conteudos_vem_do_grafo():
    resumo = gerar(cadeia(), redator=redator_de_resumos)
    assert resumo["proximos_conteudos_relacionados"]
    assert all("relacao" in p for p in resumo["proximos_conteudos_relacionados"])


# --------------------------------------------------------------------------- #
# Seções condicionais e limites
# --------------------------------------------------------------------------- #


def test_formulas_entram_quando_o_conteudo_as_tem():
    briefing = montar_briefing(cadeia(pontos=["fórmula de Bayes", "teorema central"]))
    assert "formulas" in briefing["secoes_aplicaveis"]


def test_formulas_ficam_de_fora_quando_nao_ha():
    briefing = montar_briefing(cadeia(pontos=["regra da crase", "uso do acento"]))

    assert "formulas" not in briefing["secoes_aplicaveis"]
    resumo = gerar(
        cadeia(pontos=["regra da crase", "uso do acento"]), redator=redator_de_resumos
    )
    assert resumo["formulas"] is None
    assert "formulas" in resumo["secoes_nao_aplicaveis"]


def test_secao_fora_da_estrutura_e_descartada():
    def com_extra(briefing):
        saida = redator_de_resumos(briefing)
        saida["exercicios"] = "1) resolva"
        saida["cronograma"] = "segunda: revisar"
        return saida

    resumo = gerar(cadeia(), redator=com_extra)

    assert resumo["secoes_ignoradas"] == ["cronograma", "exercicios"]
    assert "exercicios" not in resumo


def test_sem_redator_as_secoes_ficam_pendentes():
    resumo = gerar(cadeia())

    assert resumo["status"] == "pendente_de_redacao"
    assert set(resumo["secoes_pendentes"]) <= set(CHAVES_DE_SECAO)
    assert any("não foi preenchido por invenção" in o for o in resumo["observacoes"])
    # O material derivado existe mesmo sem redator.
    assert resumo["mapa_mental_textual"]
    assert resumo["checklist_de_revisao"]


def test_briefing_proibe_acrescentar_conteudo():
    briefing = montar_briefing(cadeia())

    assert "sintetizar não é acrescentar" in briefing["fonte"]["regra"]
    texto = " ".join(briefing["proibicoes"])
    for proibido in ("conteúdo novo", "exercícios", "cronograma", "simulados", "desempenho"):
        assert proibido in texto


def test_saida_declara_os_agentes_consumidores():
    resumo = gerar(cadeia())
    assert resumo["consumido_por"] == ["13", "14", "15", "16", "17", "18", "21", "24"]


# --------------------------------------------------------------------------- #
# Integração
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_agente_11_no_fluxo_completo_com_redatores():
    orquestrador = MasterOrchestrator(
        RunnerEstrutural(
            redatores={
                "07": redator_de_aula,
                "08": redator_de_exemplos,
                "09": redator_de_questoes,
                "10": redator_de_cartoes,
                "11": redator_de_resumos,
            }
        )
    )
    resultado = await orquestrador.orquestrar(
        "Quero um resumo do conteúdo",
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
    resumo = resultado.saidas["11"].conteudo

    assert resumo["status"] == "gerado"
    assert resumo["resumo_1min"]
    assert resumo["checklist_de_revisao"]
    assert resultado.validacao.aprovado is True


@pytest.mark.asyncio
async def test_agente_11_roda_depois_dos_flashcards():
    resultado = await MasterOrchestrator().orquestrar("Quero um resumo")
    ondas = {
        agente.split()[0]: onda["onda"]
        for onda in resultado.ordem_execucao
        for agente in onda["agentes"]
    }
    assert ondas["10"] < ondas["11"]
