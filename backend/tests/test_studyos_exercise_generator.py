from datetime import date

import pytest

from app.studyos.agentes.aula import gerar as gerar_aula
from app.studyos.agentes.conhecimento import analisar as analisar_conhecimento
from app.studyos.agentes.curriculo import construir as construir_curriculo
from app.studyos.agentes.dependencias import mapear
from app.studyos.agentes.exemplos import gerar as gerar_exemplos
from app.studyos.agentes.exercicios import (
    CATEGORIAS,
    CUSTO_MINUTOS,
    ConteudoNaoEstudado,
    gerar,
    montar,
    montar_briefing,
)
from app.studyos.agentes.objetivo import analisar as analisar_objetivo
from app.studyos.agentes.perfil import analisar as analisar_perfil
from app.studyos.agentes.roadmap import construir as construir_roadmap
from app.studyos.orchestrator import MasterOrchestrator
from app.studyos.runner import RunnerEstrutural

HOJE = date(2026, 1, 5)

EDITAL = {
    "Estatística": {"questoes": 10, "topicos": ["Conjuntos", "Probabilidade"]},
    "Português": {"questoes": 20, "topicos": ["Crase"]},
}

PRE = {"Probabilidade": ["Conjuntos"]}


def redator_de_aula(briefing):
    return {
        secao["chave"]: (
            ["regra geral da crase", "casos de exceção"]
            if secao["chave"] == "pontos_chave"
            else f"texto de {secao['chave']}"
        )
        for secao in briefing["secoes"]
    }


def redator_de_exemplos(briefing):
    return {
        slot["chave"]: {"enunciado": f"ex de {slot['chave']}", "por_que_funciona": "porque"}
        for slot in briefing["slots"]
        if slot["aplicavel"]
    }


def redator_de_questoes(briefing):
    return {
        slot["numero"]: {
            "enunciado": f"Questão {slot['numero']} sobre {slot['conceito_alvo']}",
            "resposta": f"resposta {slot['numero']}",
            "explicacao": f"explicação {slot['numero']}",
        }
        for slot in briefing["slots"]
    }


def cadeia(dados=None, aula_redigida=True, conteudo="Crase"):
    """Roda 01–08 de verdade e devolve as entradas prontas para o 09."""
    base = {
        "objetivo": "Passar no concurso fiscal",
        "edital": EDITAL,
        "pre_requisitos": PRE,
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
    m7 = gerar_aula(
        {
            "dados_usuario": base,
            "saidas_anteriores": {"01": m1, "03": m3, "04": m4, "05": m5, "06": m6},
        },
        redator=redator_de_aula if aula_redigida else None,
    )
    m8 = gerar_exemplos(
        {"dados_usuario": base, "saidas_anteriores": {"01": m1, "03": m3, "07": m7}},
        redator=redator_de_exemplos if aula_redigida else None,
    )
    return {
        "solicitacao": "",
        "dados_usuario": base,
        "saidas_anteriores": {
            "01": m1, "03": m3, "04": m4, "05": m5, "06": m6, "07": m7, "08": m8
        },
    }


# --------------------------------------------------------------------------- #
# Portão: só se pratica o que foi estudado
# --------------------------------------------------------------------------- #


def test_conteudo_nao_estudado_nao_recebe_exercicios():
    conjunto = gerar(cadeia(aula_redigida=False))

    assert conjunto["gerado"] is False
    assert conjunto["status"] == "bloqueado"
    assert conjunto["bloqueio"]["motivo"] == "conteudo_nao_estudado"
    assert conjunto["exercicios"] == []


def test_conteudo_bloqueado_por_pre_requisito_e_recusado():
    conjunto = gerar(cadeia(aula_redigida=False, conteudo="Probabilidade"))

    assert conjunto["bloqueio"]["motivo"] == "conteudo_bloqueado"
    assert "Conjuntos" in conjunto["bloqueio"]["detalhe"]


def test_pedido_de_diagnostico_do_agente_03_fica_registrado_na_tensao():
    conjunto = gerar(cadeia(aula_redigida=False))
    pedido = conjunto["bloqueio"]["pedido_de_diagnostico_pendente"]

    assert pedido["origem"] == "03 Knowledge Analyzer"
    assert "proíbe exercitar conteúdo não estudado" in pedido["observacao"]


def test_estudo_anterior_medido_libera_exercicios_sem_aula():
    dados = {
        "resultados_exercicios": [
            {"disciplina": "Português", "topico": "Crase", "acertos": 7, "total": 10}
        ]
    }
    conjunto = gerar(cadeia(dados, aula_redigida=False), redator=redator_de_questoes)

    assert conjunto["bloqueio"] is None
    assert conjunto["exercicios"]


def test_redator_nao_e_chamado_para_conteudo_nao_estudado():
    chamadas = []

    def redator(briefing):
        chamadas.append(briefing)
        return redator_de_questoes(briefing)

    gerar(cadeia(aula_redigida=False), redator=redator)
    assert chamadas == []


def test_montar_recusa_bateria_de_conteudo_nao_estudado():
    briefing = montar_briefing(cadeia(aula_redigida=False))

    with pytest.raises(ConteudoNaoEstudado):
        montar(briefing, {1: {"enunciado": "x", "resposta": "y", "explicacao": "z"}})


# --------------------------------------------------------------------------- #
# Dimensionamento
# --------------------------------------------------------------------------- #


def test_tempo_vem_do_bloco_de_exercicios_do_agente_06():
    briefing = montar_briefing(cadeia())

    assert briefing["origem_do_tempo"] == "bloco de exercícios do agente 06"
    assert briefing["tempo_disponivel_min"] > 0


def test_tempo_informado_pelo_usuario_tem_precedencia():
    briefing = montar_briefing(cadeia({"tempo_disponivel_min": 60}))

    assert briefing["tempo_disponivel_min"] == 60
    assert briefing["origem_do_tempo"] == "informado pelo usuário"


def test_quantidade_de_questoes_acompanha_o_tempo():
    curto = montar_briefing(cadeia({"tempo_disponivel_min": 20}))
    longo = montar_briefing(cadeia({"tempo_disponivel_min": 90}))

    assert len(longo["slots"]) > len(curto["slots"])


def test_iniciante_nao_recebe_desafio():
    dados = {
        "resultados_exercicios": [
            {"disciplina": "Português", "topico": "Crase", "acertos": 1, "total": 10}
        ]
    }
    briefing = montar_briefing(cadeia(dados))
    categorias = {b["categoria"] for b in briefing["distribuicao"]}

    assert "desafio" not in categorias
    assert "fixacao" in categorias


def test_avancado_recebe_desafio_e_pouca_fixacao():
    dados = {
        "resultados_exercicios": [
            {"disciplina": "Português", "topico": "Crase", "acertos": 10, "total": 10}
        ]
    }
    briefing = montar_briefing(cadeia(dados))
    categorias = {b["categoria"] for b in briefing["distribuicao"]}

    assert "desafio" in categorias
    assert "fixacao" not in categorias


def test_slots_vem_em_ordem_crescente_de_dificuldade():
    briefing = montar_briefing(cadeia())
    ordens = [s["ordem_dificuldade"] for s in briefing["slots"]]

    assert ordens == sorted(ordens)
    assert all(s["categoria"] in CATEGORIAS for s in briefing["slots"])


def test_formato_e_coerente_com_a_categoria():
    briefing = montar_briefing(cadeia({"tempo_disponivel_min": 60}))
    por_categoria = {}
    for slot in briefing["slots"]:
        por_categoria.setdefault(slot["categoria"], set()).add(slot["formato"])

    assert por_categoria["fixacao"] <= {
        "completar_lacunas", "verdadeiro_ou_falso", "associacao"
    }
    if "analise" in por_categoria:
        assert por_categoria["analise"] <= {"estudo_de_caso", "questao_discursiva"}


def test_pontuacao_e_tempo_seguem_a_categoria():
    conjunto = gerar(cadeia(), redator=redator_de_questoes)
    fixacao = [e for e in conjunto["exercicios"] if e["categoria"] == "fixacao"]

    assert all(e["pontos"] == 1 for e in fixacao)
    assert all(e["tempo_estimado_min"] == CUSTO_MINUTOS["fixacao"] for e in fixacao)
    assert conjunto["pontuacao_sugerida"] == sum(
        e["pontos"] for e in conjunto["exercicios"]
    )


# --------------------------------------------------------------------------- #
# Gabarito, explicação e integridade
# --------------------------------------------------------------------------- #


def test_questao_sem_gabarito_e_recusada():
    def sem_resposta(briefing):
        questoes = redator_de_questoes(briefing)
        del questoes[1]["resposta"]
        return questoes

    conjunto = gerar(cadeia(), redator=sem_resposta)

    assert conjunto["questoes_invalidas"][0] == {"numero": 1, "motivo": "sem gabarito"}
    assert 1 not in [e["numero"] for e in conjunto["exercicios"]]
    assert conjunto["gerado"] is False


def test_questao_sem_explicacao_e_recusada():
    def sem_explicacao(briefing):
        questoes = redator_de_questoes(briefing)
        questoes[2]["explicacao"] = ""
        return questoes

    conjunto = gerar(cadeia(), redator=sem_explicacao)

    assert conjunto["questoes_invalidas"][0]["motivo"] == "sem explicação da resposta"
    assert any("obrigatórios" in o for o in conjunto["observacoes"])


def test_enunciado_repetido_e_descartado():
    def repetido(briefing):
        questoes = redator_de_questoes(briefing)
        questoes[2]["enunciado"] = questoes[1]["enunciado"]
        return questoes

    conjunto = gerar(cadeia(), redator=repetido)

    assert conjunto["questoes_duplicadas"][0]["igual_a"] == 1
    assert 2 not in [e["numero"] for e in conjunto["exercicios"]]


def test_gabarito_traz_competencia_e_erro_comum():
    conjunto = gerar(cadeia(), redator=redator_de_questoes)
    item = conjunto["gabarito"][0]

    assert item["competencia_avaliada"]
    assert item["erro_comum_associado"] == "texto de erros_comuns"
    assert item["explicacao"]


def test_gabarito_tem_um_item_por_exercicio():
    conjunto = gerar(cadeia(), redator=redator_de_questoes)
    assert [e["numero"] for e in conjunto["exercicios"]] == [
        g["numero"] for g in conjunto["gabarito"]
    ]


# --------------------------------------------------------------------------- #
# Cobertura de conceitos
# --------------------------------------------------------------------------- #


def test_cobertura_dos_pontos_chave_da_aula():
    conjunto = gerar(cadeia(), redator=redator_de_questoes)
    cobertura = conjunto["cobertura_dos_conceitos"]

    assert cobertura["conceitos"] == ["regra geral da crase", "casos de exceção"]
    assert cobertura["completa"] is True


def test_conceito_sem_questao_e_reportado():
    def so_a_primeira(briefing):
        questoes = redator_de_questoes(briefing)
        return {1: questoes[1]}

    conjunto = gerar(cadeia(), redator=so_a_primeira)
    cobertura = conjunto["cobertura_dos_conceitos"]

    assert cobertura["completa"] is False
    assert "casos de exceção" in cobertura["descobertos"]
    assert any("Conceitos sem exercício" in o for o in conjunto["observacoes"])


# --------------------------------------------------------------------------- #
# Referência e limites
# --------------------------------------------------------------------------- #


def test_briefing_ancora_na_aula_e_nos_exemplos():
    briefing = montar_briefing(cadeia())
    referencia = briefing["referencia"]

    assert referencia["aula"]["desenvolvimento"] == "texto de desenvolvimento"
    assert referencia["exemplos"]["exemplo_pratico"]["enunciado"]
    assert "a aula prevalece" in referencia["regra"]


def test_briefing_exige_gabarito_e_explicacao():
    briefing = montar_briefing(cadeia())
    assert briefing["obrigatorio_por_questao"] == ["enunciado", "resposta", "explicacao"]


def test_briefing_lista_as_proibicoes_da_spec():
    briefing = montar_briefing(cadeia())
    texto = " ".join(briefing["proibicoes"])

    for proibido in ("conteúdo novo", "simulado", "cronograma", "desempenho"):
        assert proibido in texto


def test_sem_redator_as_questoes_ficam_pendentes():
    conjunto = gerar(cadeia())

    assert conjunto["status"] == "pendente_de_redacao"
    assert conjunto["exercicios"] == []
    assert conjunto["questoes_pendentes"]
    assert any("não foi preenchido por invenção" in o for o in conjunto["observacoes"])


def test_saida_declara_os_agentes_consumidores():
    conjunto = gerar(cadeia())
    assert conjunto["consumido_por"] == ["10", "11", "13", "16", "17", "18", "21", "24"]


# --------------------------------------------------------------------------- #
# Integração
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_agente_09_no_fluxo_completo_com_redatores():
    orquestrador = MasterOrchestrator(
        RunnerEstrutural(
            redatores={
                "07": redator_de_aula,
                "08": redator_de_exemplos,
                "09": redator_de_questoes,
            }
        )
    )
    resultado = await orquestrador.orquestrar(
        "Quero exercícios do meu edital",
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
    conjunto = resultado.saidas["09"].conteudo

    assert conjunto["status"] == "gerado"
    assert conjunto["exercicios"]
    assert conjunto["gabarito"]
    assert resultado.validacao.aprovado is True


@pytest.mark.asyncio
async def test_agente_09_roda_depois_da_aula_e_dos_exemplos():
    resultado = await MasterOrchestrator().orquestrar("Quero exercícios de logaritmo")
    ondas = {
        agente.split()[0]: onda["onda"]
        for onda in resultado.ordem_execucao
        for agente in onda["agentes"]
    }
    assert ondas["07"] < ondas["09"]
    assert ondas["08"] < ondas["09"]
