from datetime import date

import pytest

from app.studyos.agentes.aula import gerar as gerar_aula
from app.studyos.agentes.conhecimento import analisar as analisar_conhecimento
from app.studyos.agentes.curriculo import construir as construir_curriculo
from app.studyos.agentes.dependencias import mapear
from app.studyos.agentes.dificuldade import detectar
from app.studyos.agentes.exemplos import gerar as gerar_exemplos
from app.studyos.agentes.exercicios import gerar as gerar_exercicios
from app.studyos.agentes.objetivo import analisar as analisar_objetivo
from app.studyos.agentes.perfil import analisar as analisar_perfil
from app.studyos.agentes.roadmap import construir as construir_roadmap
from app.studyos.agentes.simulado import (
    FORMATO_DIAGNOSTICO,
    MISTURA_POR_FORMATO,
    PENALIDADE_PADRAO,
    PESO_POR_DIFICULDADE,
    QUESTOES_POR_FORMATO,
    ConteudoNaoEstudado,
    gerar,
    montar,
    montar_briefing,
)
from app.studyos.orchestrator import MasterOrchestrator

HOJE = date(2026, 1, 5)

EDITAL = {
    "Estatística": {"questoes": 10, "topicos": ["Conjuntos", "Probabilidade"]},
    "Português": {"questoes": 20, "topicos": ["Crase", "Sintaxe"]},
}


def redator_de_questoes(briefing):
    return {
        slot["numero"]: {
            "enunciado": f"Enunciado {slot['numero']} sobre {slot['topico']}",
            "alternativas": ["A", "B", "C", "D"],
            "resposta": "A",
            "explicacao": f"porque {slot['topico']}",
        }
        for slot in briefing["slots"]
    }


def cadeia(dados=None, com_exercicios=False):
    """Roda 01–06 e 12 de verdade e devolve as entradas prontas para o 16."""
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
    anteriores = {**ant, "12": m12}

    if com_exercicios:
        redator_aula = lambda b: {  # noqa: E731
            s["chave"]: (["conceito A"] if s["chave"] == "pontos_chave" else "texto")
            for s in b["secoes"]
        }
        m7 = gerar_aula(
            {"dados_usuario": {**base, "conteudo_solicitado": "Crase"},
             "saidas_anteriores": ant},
            redator=redator_aula,
        )
        m8 = gerar_exemplos(
            {"dados_usuario": base, "saidas_anteriores": {**ant, "07": m7}},
            redator=lambda b: {
                s["chave"]: {"enunciado": "ex", "por_que_funciona": "pq"}
                for s in b["slots"] if s["aplicavel"]
            },
        )
        m9 = gerar_exercicios(
            {"dados_usuario": base, "saidas_anteriores": {**ant, "07": m7, "08": m8}},
            redator=lambda b: {
                s["numero"]: {
                    "enunciado": f"Questão do banco {s['numero']}",
                    "resposta": "banco",
                    "explicacao": "do banco",
                }
                for s in b["slots"]
            },
        )
        anteriores["09"] = m9

    return {"solicitacao": "", "dados_usuario": base, "saidas_anteriores": anteriores}


def acertos(topico, certos, total, disciplina="Português"):
    return {
        "disciplina": disciplina,
        "topico": topico,
        "acertos": certos,
        "total": total,
        "data": HOJE.isoformat(),
    }


ESTUDADO = {
    "resultados_exercicios": [
        acertos("Crase", 8, 10),
        acertos("Sintaxe", 5, 10),
        acertos("Conjuntos", 3, 10, disciplina="Estatística"),
        acertos("Probabilidade", 7, 10, disciplina="Estatística"),
    ]
}


# --------------------------------------------------------------------------- #
# Escopo: a exceção do diagnóstico
# --------------------------------------------------------------------------- #


def test_sem_conteudo_estudado_o_simulado_comum_e_bloqueado():
    briefing = montar_briefing(
        cadeia({"tipo_de_simulado": "parcial"}), hoje=HOJE
    )
    simulado = montar(briefing)

    assert simulado["gerado"] is False
    assert simulado["bloqueio"]["motivo"] == "sem_conteudo_elegivel"
    assert "diagnóstico" in simulado["bloqueio"]["acao"]


def test_diagnostico_pode_cobrir_conteudo_nao_estudado():
    briefing = montar_briefing(
        cadeia({"tipo_de_simulado": "diagnostico"}), hoje=HOJE
    )

    assert briefing["bloqueio"] is None
    assert briefing["slots"]
    assert any(not s["estudado"] for s in briefing["slots"])


def test_diagnostico_declara_a_excecao_na_saida():
    simulado = gerar(
        cadeia({"tipo_de_simulado": "diagnostico"}), redator=redator_de_questoes, hoje=HOJE
    )
    assert any(
        "exceção prevista na spec" in o for o in simulado["observacoes"]
    )


def test_formato_nao_diagnostico_exclui_o_nao_estudado():
    dados = {**ESTUDADO, "tipo_de_simulado": "parcial"}
    dados["resultados_exercicios"] = [acertos("Crase", 8, 10)]
    briefing = montar_briefing(cadeia(dados), hoje=HOJE)

    assert [s["topico"] for s in briefing["slots"]] == ["Crase"] * len(briefing["slots"])
    assert briefing["excluidos"]
    assert all("não estudado" in e["motivo"] for e in briefing["excluidos"])


def test_montar_recusa_simulado_bloqueado_mesmo_com_questoes():
    briefing = montar_briefing(cadeia({"tipo_de_simulado": "parcial"}), hoje=HOJE)

    with pytest.raises(ConteudoNaoEstudado):
        montar(briefing, {1: {"enunciado": "x", "resposta": "y"}})


# --------------------------------------------------------------------------- #
# Formato
# --------------------------------------------------------------------------- #


def test_formato_informado_tem_precedencia():
    briefing = montar_briefing(
        cadeia({**ESTUDADO, "tipo_de_simulado": "completo"}), hoje=HOJE
    )
    assert briefing["formato"]["formato"] == "completo"
    assert briefing["formato"]["base"] == "informado pelo usuário"


def test_reta_final_vira_revisao_final():
    briefing = montar_briefing(
        cadeia({**ESTUDADO, "data_prova": "2026-01-20"}), hoje=HOJE
    )
    assert briefing["formato"]["formato"] == "revisao_final"
    assert "reta final" in briefing["formato"]["base"]


def test_sem_medicao_o_formato_padrao_e_diagnostico():
    briefing = montar_briefing(cadeia(), hoje=HOJE)

    assert briefing["formato"]["formato"] == FORMATO_DIAGNOSTICO
    assert "agente 03" in briefing["formato"]["base"]


def test_disciplina_alvo_restringe_o_escopo():
    briefing = montar_briefing(
        cadeia({**ESTUDADO, "disciplina_alvo": "Estatística"}), hoje=HOJE
    )
    assert briefing["formato"]["formato"] == "disciplina"
    assert {s["disciplina"] for s in briefing["slots"]} == {"Estatística"}


# --------------------------------------------------------------------------- #
# Dimensionamento e distribuição
# --------------------------------------------------------------------------- #


def test_quantidade_padrao_por_formato():
    briefing = montar_briefing(
        cadeia({**ESTUDADO, "tipo_de_simulado": "parcial"}), hoje=HOJE
    )
    assert len(briefing["slots"]) == QUESTOES_POR_FORMATO["parcial"]


def test_simulado_completo_usa_o_total_do_edital():
    briefing = montar_briefing(
        cadeia({**ESTUDADO, "tipo_de_simulado": "completo"}), hoje=HOJE
    )
    assert len(briefing["slots"]) == 30  # 10 de Estatística + 20 de Português
    assert "edital" in briefing["quantidade"]["base"]


def test_quantidade_informada_tem_precedencia():
    briefing = montar_briefing(
        cadeia({**ESTUDADO, "numero_de_questoes": 12}), hoje=HOJE
    )
    assert len(briefing["slots"]) == 12


def test_dificuldade_sempre_varia():
    simulado = gerar(cadeia(ESTUDADO), redator=redator_de_questoes, hoje=HOJE)
    distribuicao = simulado["resumo_geral"]["distribuicao_por_dificuldade"]

    assert set(distribuicao) == {"facil", "medio", "dificil"}
    assert all(quantidade > 0 for quantidade in distribuicao.values())


def test_mistura_segue_a_tabela_do_formato():
    simulado = gerar(
        cadeia({**ESTUDADO, "tipo_de_simulado": "completo"}),
        redator=redator_de_questoes,
        hoje=HOJE,
    )
    distribuicao = simulado["resumo_geral"]["distribuicao_por_dificuldade"]
    total = sum(distribuicao.values())

    for dificuldade, fracao in MISTURA_POR_FORMATO["completo"].items():
        assert abs(distribuicao[dificuldade] / total - fracao) < 0.1


def test_conteudo_mais_dificil_aparece_mais_vezes():
    dados = {
        **ESTUDADO,
        "erros": [
            {"topico": "Conjuntos", "categoria": "aplicacao"},
            {"topico": "Conjuntos", "categoria": "aplicacao"},
        ],
    }
    briefing = montar_briefing(cadeia(dados), hoje=HOJE)
    contagem: dict[str, int] = {}
    for slot in briefing["slots"]:
        contagem[slot["topico"]] = contagem.get(slot["topico"], 0) + 1

    assert contagem["Conjuntos"] >= max(contagem.values())
    assert briefing["slots"][0]["prioridade"]["fatores"]


# --------------------------------------------------------------------------- #
# Caderno, gabarito e correção
# --------------------------------------------------------------------------- #


def test_caderno_do_estudante_nao_tem_resposta():
    simulado = gerar(cadeia(ESTUDADO), redator=redator_de_questoes, hoje=HOJE)

    for questao in simulado["caderno_de_questoes"]:
        assert "resposta" not in questao
        assert "resposta_correta" not in questao
        assert "explicacao" not in questao
    assert any("não contém respostas" in o for o in simulado["observacoes"])


def test_gabarito_tem_uma_entrada_por_questao():
    simulado = gerar(cadeia(ESTUDADO), redator=redator_de_questoes, hoje=HOJE)

    assert len(simulado["gabarito"]) == len(simulado["caderno_de_questoes"])
    ids_caderno = [q["id"] for q in simulado["caderno_de_questoes"]]
    ids_gabarito = [g["id"] for g in simulado["gabarito"]]
    assert sorted(ids_caderno) == sorted(ids_gabarito)


def test_peso_acompanha_a_dificuldade():
    simulado = gerar(cadeia(ESTUDADO), redator=redator_de_questoes, hoje=HOJE)

    for questao in simulado["questoes"]:
        assert questao["peso"] == PESO_POR_DIFICULDADE[questao["grau_de_dificuldade"]]
    assert simulado["criterios_de_correcao"]["pontuacao_maxima"] == sum(
        q["peso"] for q in simulado["questoes"]
    )


def test_penalidade_por_erro_entra_nos_criterios():
    simulado = gerar(
        cadeia({**ESTUDADO, "penalidade_por_erro": 0.25}),
        redator=redator_de_questoes,
        hoje=HOJE,
    )
    criterios = simulado["criterios_de_correcao"]

    assert criterios["penalidade_por_erro"] == 0.25
    assert "desconta 0.25" in criterios["regra"]
    assert criterios["origem_da_penalidade"] == "informado pelo usuário"


@pytest.mark.parametrize("resposta", [True, "sim", "tem"])
def test_penalidade_confirmada_sem_valor_cai_no_padrao(resposta):
    """Quem responde "sim" está dizendo que há desconto, não que não há."""
    simulado = gerar(
        cadeia({**ESTUDADO, "penalidade_por_erro": resposta}),
        redator=redator_de_questoes,
        hoje=HOJE,
    )
    criterios = simulado["criterios_de_correcao"]

    assert criterios["penalidade_por_erro"] == PENALIDADE_PADRAO
    assert "sem informar o valor" in criterios["origem_da_penalidade"]


def test_sem_penalidade_informada_nao_ha_desconto():
    simulado = gerar(cadeia(ESTUDADO), redator=redator_de_questoes, hoje=HOJE)
    criterios = simulado["criterios_de_correcao"]

    assert criterios["penalidade_por_erro"] == 0.0
    assert criterios["origem_da_penalidade"] == "nenhum desconto informado"
    assert "Sem desconto" in criterios["regra"]


def test_nota_de_corte_informada_entra_nos_criterios():
    simulado = gerar(
        cadeia({**ESTUDADO, "nota_corte": 60}), redator=redator_de_questoes, hoje=HOJE
    )
    assert simulado["criterios_de_correcao"]["nota_de_corte"] == 60.0


def test_constantes_sao_declaradas_na_saida():
    simulado = gerar(cadeia(ESTUDADO), redator=redator_de_questoes, hoje=HOJE)
    constantes = simulado["constantes_aplicadas"]

    assert constantes["peso_por_dificuldade"] == PESO_POR_DIFICULDADE
    assert constantes["questoes_por_formato"] == QUESTOES_POR_FORMATO
    assert constantes["penalidade_padrao"] == PENALIDADE_PADRAO


def test_questao_sem_resposta_e_recusada():
    def sem_resposta(briefing):
        questoes = redator_de_questoes(briefing)
        del questoes[1]["resposta"]
        return questoes

    simulado = gerar(cadeia(ESTUDADO), redator=sem_resposta, hoje=HOJE)

    assert simulado["questoes_invalidas"][0]["motivo"] == "sem resposta correta"
    assert simulado["gerado"] is False


# --------------------------------------------------------------------------- #
# Embaralhamento reproduzível
# --------------------------------------------------------------------------- #


def test_embaralhamento_e_reproduzivel_com_a_mesma_semente():
    um = gerar(
        cadeia({**ESTUDADO, "semente": 42}), redator=redator_de_questoes, hoje=HOJE
    )
    outro = gerar(
        cadeia({**ESTUDADO, "semente": 42}), redator=redator_de_questoes, hoje=HOJE
    )

    assert [q["enunciado"] for q in um["caderno_de_questoes"]] == [
        q["enunciado"] for q in outro["caderno_de_questoes"]
    ]


def test_sementes_diferentes_produzem_ordens_diferentes():
    um = gerar(
        cadeia({**ESTUDADO, "semente": 1}), redator=redator_de_questoes, hoje=HOJE
    )
    outro = gerar(
        cadeia({**ESTUDADO, "semente": 999}), redator=redator_de_questoes, hoje=HOJE
    )

    assert [q["enunciado"] for q in um["caderno_de_questoes"]] != [
        q["enunciado"] for q in outro["caderno_de_questoes"]
    ]


def test_alternativas_tambem_sao_embaralhadas():
    simulado = gerar(
        cadeia({**ESTUDADO, "semente": 7}), redator=redator_de_questoes, hoje=HOJE
    )
    ordens = {
        tuple(q["alternativas"]) for q in simulado["caderno_de_questoes"] if q["alternativas"]
    }
    assert len(ordens) > 1


# --------------------------------------------------------------------------- #
# Banco do agente 09
# --------------------------------------------------------------------------- #


def test_questao_do_banco_e_reaproveitada():
    simulado = gerar(cadeia(ESTUDADO, com_exercicios=True), hoje=HOJE)
    reaproveitadas = [
        q for q in simulado["questoes"] if q["origem"] == "banco do agente 09"
    ]

    assert reaproveitadas
    assert any("reaproveitada" in o for o in simulado["observacoes"])


def test_reaproveitamento_respeita_a_dificuldade_da_lista_de_origem():
    """Questão calibrada como fácil não pode ocupar slot difícil."""
    entradas = cadeia(ESTUDADO, com_exercicios=True)
    nivel_da_lista = entradas["saidas_anteriores"]["09"]["nivel_de_dificuldade"]
    simulado = gerar(entradas, hoje=HOJE)

    for questao in simulado["questoes"]:
        if questao["origem"] == "banco do agente 09":
            assert questao["grau_de_dificuldade"] == nivel_da_lista


def test_sem_banco_e_sem_redator_as_questoes_ficam_pendentes():
    simulado = gerar(cadeia(ESTUDADO), hoje=HOJE)

    assert simulado["status"] == "pendente_de_redacao"
    assert simulado["questoes_pendentes"]
    assert simulado["caderno_de_questoes"] == []


# --------------------------------------------------------------------------- #
# Estatísticas e registro
# --------------------------------------------------------------------------- #


def test_estatistica_prevista_vem_do_dominio_medido():
    simulado = gerar(cadeia(ESTUDADO), redator=redator_de_questoes, hoje=HOJE)
    estatisticas = simulado["estatisticas_previstas"]

    assert 0 < estatisticas["acerto_previsto"] < 1
    assert "agente 03" in estatisticas["base"]
    assert estatisticas["pontuacao_maxima"] == simulado["criterios_de_correcao"][
        "pontuacao_maxima"
    ]


def test_registro_para_analise_e_endereçado_aos_agentes_certos():
    simulado = gerar(cadeia(ESTUDADO), redator=redator_de_questoes, hoje=HOJE)
    registro = simulado["registro_para_analise"]

    assert registro["destinatarios"] == ["17", "18", "21"]
    assert len(registro["por_questao"]) == len(simulado["questoes"])
    assert all(
        {"topico", "dificuldade", "competencia", "dominio_medido"} <= set(q)
        for q in registro["por_questao"]
    )


def test_banca_informada_entra_como_instrucao():
    briefing = montar_briefing(
        cadeia({**ESTUDADO, "banca": "FGV"}), hoje=HOJE
    )
    assert briefing["banca"]["nome"] == "FGV"
    assert "FGV" in briefing["banca"]["instrucao"]


def test_simulado_nao_altera_o_plano_de_estudos():
    simulado = gerar(cadeia(ESTUDADO), redator=redator_de_questoes, hoje=HOJE)
    proibidos = {"cronograma", "sessoes", "metas", "disciplinas"}

    assert proibidos.isdisjoint(simulado)


def test_saida_declara_os_agentes_consumidores():
    simulado = gerar(cadeia(ESTUDADO), redator=redator_de_questoes, hoje=HOJE)
    assert simulado["consumido_por"] == ["17", "18", "19", "21", "22", "23", "24"]


# --------------------------------------------------------------------------- #
# Integração
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_agente_16_no_fluxo_completo():
    resultado = await MasterOrchestrator().orquestrar(
        "Faz um simulado pra mim",
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
    simulado = resultado.saidas["16"].conteudo

    # Sem medição, o formato escolhido é o diagnóstico.
    assert simulado["briefing"]["formato"]["formato"] == FORMATO_DIAGNOSTICO
    assert resultado.validacao.aprovado is True


@pytest.mark.asyncio
async def test_agente_16_roda_depois_do_09_e_do_15():
    resultado = await MasterOrchestrator().orquestrar("Faz um simulado")
    ondas = {
        agente.split()[0]: onda["onda"]
        for onda in resultado.ordem_execucao
        for agente in onda["agentes"]
    }
    assert ondas["09"] < ondas["16"]
    assert ondas["15"] < ondas["16"]
