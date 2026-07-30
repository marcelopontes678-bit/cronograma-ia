from datetime import date

import pytest

from app.studyos.agentes.aula import gerar as gerar_aula
from app.studyos.agentes.conhecimento import analisar as analisar_conhecimento
from app.studyos.agentes.curriculo import construir as construir_curriculo
from app.studyos.agentes.dependencias import mapear
from app.studyos.agentes.exemplos import gerar as gerar_exemplos
from app.studyos.agentes.exercicios import gerar as gerar_exercicios
from app.studyos.agentes.flashcards import (
    MAXIMO_PALAVRAS_RESPOSTA,
    SEGUNDOS_POR_TIPO,
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


PONTOS_CHAVE_PADRAO = ["regra geral", "exceções"]


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


redator_de_aula = redator_de_aula_com(PONTOS_CHAVE_PADRAO)


def redator_de_exemplos(briefing):
    return {
        slot["chave"]: {"enunciado": "ex", "por_que_funciona": "pq"}
        for slot in briefing["slots"]
        if slot["aplicavel"]
    }


def redator_de_questoes(briefing):
    return {
        slot["numero"]: {
            "enunciado": f"Q{slot['numero']} sobre {slot['conceito_alvo']}",
            "resposta": "r",
            "explicacao": "e",
        }
        for slot in briefing["slots"]
    }


def redator_de_cartoes(briefing):
    """Redator de teste: respeita o tipo de cada slot."""
    cartoes = {}
    for slot in briefing["slots"]:
        if slot["tipo"] == "cloze":
            pergunta = f"A regra de {slot['conceito']} diz que ___ ."
        elif slot["tipo"] in ("verdadeiro_ou_falso", "associacao", "sequencia_logica"):
            pergunta = f"Afirmação sobre {slot['conceito']}."
        else:
            pergunta = f"O que é {slot['conceito']}?"
        cartoes[slot["numero"]] = {"pergunta": pergunta, "resposta": "resposta curta"}
    return cartoes


def cadeia(dados=None, aula_redigida=True, conteudo="Crase", pontos_chave=None):
    """Roda 01–09 de verdade e devolve as entradas prontas para o 10."""
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
    anteriores = {"01": m1, "03": m3, "04": m4, "05": m5, "06": m6}
    m7 = gerar_aula(
        {"dados_usuario": base, "saidas_anteriores": anteriores},
        redator=(
            redator_de_aula_com(pontos_chave or PONTOS_CHAVE_PADRAO)
            if aula_redigida
            else None
        ),
    )
    m8 = gerar_exemplos(
        {"dados_usuario": base, "saidas_anteriores": {**anteriores, "07": m7}},
        redator=redator_de_exemplos if aula_redigida else None,
    )
    m9 = gerar_exercicios(
        {"dados_usuario": base, "saidas_anteriores": {**anteriores, "07": m7, "08": m8}},
        redator=redator_de_questoes if aula_redigida else None,
    )
    return {
        "solicitacao": "",
        "dados_usuario": base,
        "saidas_anteriores": {**anteriores, "07": m7, "08": m8, "09": m9},
    }


# --------------------------------------------------------------------------- #
# Portão
# --------------------------------------------------------------------------- #


def test_conteudo_nao_estudado_nao_vira_flashcard():
    baralho = gerar(cadeia(aula_redigida=False))

    assert baralho["gerado"] is False
    assert baralho["status"] == "bloqueado"
    assert baralho["bloqueio"]["motivo"] == "conteudo_nao_estudado"
    assert baralho["flashcards"] == []


def test_conteudo_bloqueado_por_pre_requisito_e_recusado():
    baralho = gerar(cadeia(aula_redigida=False, conteudo="Probabilidade"))
    assert baralho["bloqueio"]["motivo"] == "conteudo_bloqueado"
    assert "Conjuntos" in baralho["bloqueio"]["detalhe"]


def test_montar_recusa_baralho_de_conteudo_nao_estudado():
    briefing = montar_briefing(cadeia(aula_redigida=False))

    with pytest.raises(ConteudoNaoEstudado):
        montar(briefing, {1: {"pergunta": "O que é X?", "resposta": "y"}})


def test_redator_nao_e_chamado_sem_conteudo_estudado():
    chamadas = []

    def redator(briefing):
        chamadas.append(briefing)
        return redator_de_cartoes(briefing)

    gerar(cadeia(aula_redigida=False), redator=redator)
    assert chamadas == []


# --------------------------------------------------------------------------- #
# Uma ideia por cartão
# --------------------------------------------------------------------------- #


def test_resposta_longa_e_recusada():
    def resposta_longa(briefing):
        cartoes = redator_de_cartoes(briefing)
        cartoes[1]["resposta"] = " ".join(["palavra"] * (MAXIMO_PALAVRAS_RESPOSTA + 1))
        return cartoes

    baralho = gerar(cadeia(), redator=resposta_longa)
    recusado = baralho["cartoes_invalidos"][0]

    assert recusado["numero"] == 1
    assert "provável mais de uma ideia" in recusado["motivo"]
    assert baralho["gerado"] is False


def test_resposta_que_enumera_conceitos_e_recusada():
    def enumerando(briefing):
        cartoes = redator_de_cartoes(briefing)
        cartoes[1]["resposta"] = "primeira ideia; segunda ideia"
        return cartoes

    baralho = gerar(cadeia(), redator=enumerando)
    assert "enumera mais de um conceito" in baralho["cartoes_invalidos"][0]["motivo"]


# --------------------------------------------------------------------------- #
# Recuperação ativa
# --------------------------------------------------------------------------- #


def test_frente_que_nao_exige_recall_e_recusada():
    def afirmacao(briefing):
        cartoes = redator_de_cartoes(briefing)
        # slot 1 é conceito_definicao: precisa de pergunta ou lacuna
        cartoes[1]["pergunta"] = "A crase é a fusão da preposição com o artigo."
        return cartoes

    baralho = gerar(cadeia(), redator=afirmacao)
    assert "recuperação ativa" in baralho["cartoes_invalidos"][0]["motivo"]


def test_tipos_variam_conforme_a_quantidade_de_conceitos():
    briefing = montar_briefing(
        cadeia(pontos_chave=["a", "b", "c", "d", "e", "f", "g"])
    )
    tipos = [s["tipo"] for s in briefing["slots"]]

    assert len(set(tipos)) == 7  # os sete formatos da spec
    assert "cloze" in tipos
    assert "sequencia_logica" in tipos


def test_cloze_sem_lacuna_e_recusado():
    entradas = cadeia(pontos_chave=["a", "b", "c"])

    def sem_lacuna(briefing):
        cartoes = redator_de_cartoes(briefing)
        numero = next(s["numero"] for s in briefing["slots"] if s["tipo"] == "cloze")
        cartoes[numero]["pergunta"] = "Uma frase sem lacuna nenhuma?"
        return cartoes

    baralho = gerar(entradas, redator=sem_lacuna)
    assert any("cloze sem lacuna" in c["motivo"] for c in baralho["cartoes_invalidos"])


def test_verdadeiro_ou_falso_nao_precisa_de_interrogacao():
    baralho = gerar(cadeia(), redator=redator_de_cartoes)
    tipos = {c["tipo"] for c in baralho["flashcards"]}

    assert "verdadeiro_ou_falso" in tipos or "conceito_definicao" in tipos
    assert baralho["cartoes_invalidos"] == []


def test_pergunta_repetida_e_descartada():
    def repetida(briefing):
        cartoes = redator_de_cartoes(briefing)
        numeros = sorted(cartoes)
        cartoes[numeros[1]]["pergunta"] = cartoes[numeros[0]]["pergunta"]
        return cartoes

    baralho = gerar(cadeia(), redator=repetida)
    assert baralho["cartoes_duplicados"][0]["igual_a"] == 1


def test_cartao_sem_pergunta_ou_resposta_e_recusado():
    def incompleto(briefing):
        cartoes = redator_de_cartoes(briefing)
        cartoes[1]["resposta"] = ""
        return cartoes

    baralho = gerar(cadeia(), redator=incompleto)
    assert baralho["cartoes_invalidos"][0]["motivo"] == "sem resposta"


# --------------------------------------------------------------------------- #
# Classificação calculada
# --------------------------------------------------------------------------- #


def test_dificuldade_vem_do_dominio_medido():
    facil = montar_briefing(
        cadeia(
            {
                "resultados_exercicios": [
                    {"disciplina": "Português", "topico": "Crase", "acertos": 10, "total": 10}
                ]
            }
        )
    )
    dificil = montar_briefing(
        cadeia(
            {
                "resultados_exercicios": [
                    {"disciplina": "Português", "topico": "Crase", "acertos": 1, "total": 10}
                ]
            }
        )
    )

    assert facil["dificuldade"] == "facil"
    assert dificil["dificuldade"] == "dificil"


def test_prioridade_vem_da_importancia_do_topico():
    briefing = montar_briefing(cadeia())
    assert briefing["prioridade"] == "alta"  # Português é essencial no edital


def test_cartao_dificil_e_marcado_para_revisao_frequente():
    dados = {
        "resultados_exercicios": [
            {"disciplina": "Português", "topico": "Crase", "acertos": 1, "total": 10}
        ]
    }
    baralho = gerar(cadeia(dados), redator=redator_de_cartoes)

    assert all(c["revisao_frequente"] for c in baralho["flashcards"])
    assert baralho["resumo"]["marcados_para_revisao_frequente"] == len(
        baralho["flashcards"]
    )
    assert any("agente 14" in o for o in baralho["observacoes"])


def test_tempo_de_resposta_acompanha_o_tipo():
    baralho = gerar(cadeia(), redator=redator_de_cartoes)
    for cartao in baralho["flashcards"]:
        assert cartao["tempo_medio_resposta_s"] == SEGUNDOS_POR_TIPO[cartao["tipo"]]


def test_localizacao_na_arvore_e_preenchida():
    baralho = gerar(cadeia(), redator=redator_de_cartoes)
    cartao = baralho["flashcards"][0]

    assert cartao["disciplina"] == "Português"
    assert cartao["modulo"]
    assert cartao["topico"] == "Crase"


def test_tags_incluem_localizacao_tipo_e_conceito():
    baralho = gerar(cadeia(), redator=redator_de_cartoes)
    cartao = baralho["flashcards"][0]

    assert "Português" in cartao["tags"]
    assert cartao["tipo"] in cartao["tags"]
    assert cartao["conceito"] in cartao["tags"]


def test_id_unico_por_cartao():
    baralho = gerar(cadeia(), redator=redator_de_cartoes)
    ids = [c["id"] for c in baralho["flashcards"]]

    assert len(ids) == len(set(ids))
    assert ids[0].startswith("fc-")


# --------------------------------------------------------------------------- #
# Conceitos e resumo
# --------------------------------------------------------------------------- #


def test_conceitos_vem_da_aula_e_dos_exercicios():
    briefing = montar_briefing(cadeia())
    assert "regra geral" in briefing["conceitos_essenciais"]
    assert "exceções" in briefing["conceitos_essenciais"]


def test_resumo_final_traz_as_distribuicoes():
    baralho = gerar(cadeia(), redator=redator_de_cartoes)
    resumo = baralho["resumo"]

    assert resumo["total"] == len(baralho["flashcards"])
    assert sum(resumo["distribuicao_por_dificuldade"].values()) == resumo["total"]
    assert resumo["distribuicao_por_disciplina"]["Português"] == resumo["total"]
    assert resumo["conceitos_descobertos"] == []
    assert resumo["tempo_total_estimado_s"] > 0


def test_briefing_declara_as_categorias_a_extrair():
    briefing = montar_briefing(cadeia())
    assert "fórmulas" in briefing["categorias_a_extrair"]
    assert "exceções" in briefing["categorias_a_extrair"]


def test_briefing_proibe_substituir_a_aula():
    briefing = montar_briefing(cadeia())
    assert "não substituir a aula pelo flashcard" in briefing["proibicoes"]
    assert "não substitui a aula" in briefing["referencia"]["regra"]


def test_sem_redator_os_cartoes_ficam_pendentes():
    baralho = gerar(cadeia())

    assert baralho["status"] == "pendente_de_redacao"
    assert baralho["flashcards"] == []
    assert baralho["cartoes_pendentes"]
    assert any("não foram inventados" in o for o in baralho["observacoes"])


def test_saida_declara_os_agentes_consumidores():
    baralho = gerar(cadeia())
    assert baralho["consumido_por"] == ["11", "13", "14", "15", "17", "18", "21", "24"]


# --------------------------------------------------------------------------- #
# Integração
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_agente_10_no_fluxo_completo_com_redatores():
    orquestrador = MasterOrchestrator(
        RunnerEstrutural(
            redatores={
                "07": redator_de_aula,
                "08": redator_de_exemplos,
                "09": redator_de_questoes,
                "10": redator_de_cartoes,
            }
        )
    )
    resultado = await orquestrador.orquestrar(
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
        },
    )
    baralho = resultado.saidas["10"].conteudo

    assert baralho["status"] == "gerado"
    assert baralho["flashcards"]
    assert baralho["resumo"]["total"] > 0
    assert resultado.validacao.aprovado is True


@pytest.mark.asyncio
async def test_agente_10_roda_depois_dos_exercicios():
    resultado = await MasterOrchestrator().orquestrar("Preciso revisar com flashcards")
    ondas = {
        agente.split()[0]: onda["onda"]
        for onda in resultado.ordem_execucao
        for agente in onda["agentes"]
    }
    assert ondas["09"] < ondas["10"]
