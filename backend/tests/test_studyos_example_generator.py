from datetime import date

import pytest

from app.studyos.agentes.aula import gerar as gerar_aula
from app.studyos.agentes.conhecimento import analisar as analisar_conhecimento
from app.studyos.agentes.curriculo import construir as construir_curriculo
from app.studyos.agentes.dependencias import mapear
from app.studyos.agentes.exemplos import (
    CHAVES_DE_SLOT,
    CHAVES_OBRIGATORIAS,
    TeoriaAusente,
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
            ["ponto A", "ponto B"]
            if secao["chave"] == "pontos_chave"
            else f"texto de {secao['chave']}"
        )
        for secao in briefing["secoes"]
    }


def redator_de_exemplos(briefing):
    conjunto = {
        slot["chave"]: {
            "enunciado": f"enunciado de {slot['chave']}",
            "por_que_funciona": f"porque {slot['chave']}",
        }
        for slot in briefing["slots"]
        if slot["aplicavel"]
    }
    conjunto["observacoes_importantes"] = ["cuidado com o caso limite"]
    return conjunto


def cadeia(dados=None, aula_redigida=True, conteudo="Crase"):
    """Roda 01–07 de verdade e devolve as entradas prontas para o 08."""
    base = {
        "objetivo": "Passar no concurso fiscal",
        "edital": EDITAL,
        "pre_requisitos": PRE,
        "escolaridade": "Superior completo",
        "profissao": "Analista tributário",
        "rotina": "Estudo em casa",
        "horas_por_dia": 4,
        "dias_por_semana": 5,
        "idade": 30,
        "experiencia_anterior": "nenhuma",
        "preferencia_estudo": "videoaula",
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
    return {
        "solicitacao": "",
        "dados_usuario": base,
        "saidas_anteriores": {"01": m1, "03": m3, "07": m7},
    }


# --------------------------------------------------------------------------- #
# Portão da teoria
# --------------------------------------------------------------------------- #


def test_sem_aula_redigida_nao_ha_exemplos():
    conjunto = gerar(cadeia(aula_redigida=False))

    assert conjunto["gerado"] is False
    assert conjunto["status"] == "bloqueado"
    assert conjunto["bloqueio"]["motivo"] == "teoria_nao_redigida"
    assert all(conjunto[chave] is None for chave in CHAVES_DE_SLOT)


def test_aula_bloqueada_bloqueia_os_exemplos():
    conjunto = gerar(cadeia(aula_redigida=False, conteudo="Probabilidade"))

    assert conjunto["bloqueio"]["motivo"] == "aula_bloqueada_por_pre_requisito"
    assert "Conjuntos" in conjunto["bloqueio"]["detalhe"]


def test_sem_agente_07_nao_ha_exemplos():
    conjunto = gerar({"dados_usuario": {}, "saidas_anteriores": {}})

    assert conjunto["bloqueio"]["motivo"] == "aula_ausente"
    assert "aula_do_agente_07" in conjunto["lacunas"]


def test_redator_nao_e_chamado_sem_teoria():
    chamadas = []

    def redator(briefing):
        chamadas.append(briefing)
        return redator_de_exemplos(briefing)

    gerar(cadeia(aula_redigida=False), redator=redator)
    assert chamadas == []


def test_montar_recusa_exemplos_sem_teoria_mesmo_prontos():
    briefing = montar_briefing(cadeia(aula_redigida=False))

    with pytest.raises(TeoriaAusente):
        montar(briefing, {"exemplo_introdutorio": "qualquer coisa"})


# --------------------------------------------------------------------------- #
# Ancoragem na aula
# --------------------------------------------------------------------------- #


def test_briefing_carrega_a_teoria_como_referencia():
    briefing = montar_briefing(cadeia())
    teoria = briefing["teoria_de_referencia"]

    assert teoria["desenvolvimento"] == "texto de desenvolvimento"
    assert teoria["pontos_chave"] == ["ponto A", "ponto B"]
    assert teoria["erros_comuns"] == "texto de erros_comuns"
    assert "a teoria da aula prevalece" in teoria["regra"]


def test_conceito_abordado_vem_do_objetivo_da_aula():
    conjunto = gerar(cadeia())
    assert conjunto["conceito_abordado"]
    assert conjunto["conteudo"]["nome"] == "Crase"


def test_contraexemplo_e_orientado_pelos_erros_comuns_da_aula():
    briefing = montar_briefing(cadeia())
    assert any("contraexemplo deve atacar os erros comuns" in d for d in briefing["diretrizes"])


def test_contexto_do_estudante_entra_no_briefing():
    briefing = montar_briefing(cadeia())
    contexto = briefing["contexto_do_estudante"]

    assert contexto["profissao"] == "Analista tributário"
    assert contexto["estilo_de_aprendizagem"] == "visual"
    assert "nunca forçando a conexão" in contexto["uso"]


def test_briefing_lista_as_proibicoes_da_spec():
    briefing = montar_briefing(cadeia())
    texto = " ".join(briefing["proibicoes"])

    for proibido in ("aulas", "exercícios", "flashcards", "simulados", "avaliar"):
        assert proibido in texto


# --------------------------------------------------------------------------- #
# Slots condicionais
# --------------------------------------------------------------------------- #


def test_exemplo_avancado_entra_quando_o_estudante_ja_domina():
    dados = {
        "resultados_exercicios": [
            {"disciplina": "Português", "topico": "Crase", "acertos": 10, "total": 10}
        ]
    }
    briefing = montar_briefing(cadeia(dados))
    assert "exemplo_avancado" in briefing["slots_aplicaveis"]


def test_iniciante_nao_recebe_exemplo_avancado_nem_com_conteudo_dificil():
    dados = {
        "resultados_exercicios": [
            {"disciplina": "Português", "topico": "Crase", "acertos": 1, "total": 10}
        ]
    }
    entradas = cadeia(dados)
    aula = entradas["saidas_anteriores"]["07"]

    # O conteúdo é difícil (domínio medido: nao_conhece) e o estudante é iniciante.
    assert aula["nivel_dificuldade"] == "dificil"
    assert aula["nivel_do_estudante"]["nivel"] == "iniciante"

    conjunto = gerar(entradas, redator=redator_de_exemplos)

    assert conjunto["exemplo_avancado"] is None
    assert "exemplo_avancado" in conjunto["slots_nao_aplicaveis"]
    assert conjunto["gerado"] is True  # não bloqueia: é condicional


def test_estudante_com_base_recebe_avancado_em_conteudo_dificil():
    dados = {
        "resultados_exercicios": [
            {"disciplina": "Português", "topico": "Crase", "acertos": 7, "total": 10}
        ]
    }
    briefing = montar_briefing(cadeia(dados))
    assert "exemplo_avancado" in briefing["slots_aplicaveis"]


def test_analogia_e_util_para_quem_esta_comecando():
    dados = {
        "resultados_exercicios": [
            {"disciplina": "Português", "topico": "Crase", "acertos": 1, "total": 10}
        ]
    }
    briefing = montar_briefing(cadeia(dados))
    assert "analogia" in briefing["slots_aplicaveis"]


def test_analogia_declara_onde_deixa_de_valer():
    briefing = montar_briefing(cadeia())
    analogia = next(s for s in briefing["slots"] if s["chave"] == "analogia")
    assert "deixa de valer" in analogia["instrucao"]


# --------------------------------------------------------------------------- #
# Redação e montagem
# --------------------------------------------------------------------------- #


def test_sem_redator_os_slots_ficam_pendentes():
    conjunto = gerar(cadeia())

    assert conjunto["gerado"] is False
    assert conjunto["status"] == "pendente_de_redacao"
    assert set(conjunto["slots_pendentes"]) <= set(CHAVES_OBRIGATORIAS)
    assert any("não foi preenchido por invenção" in o for o in conjunto["observacoes"])


def test_conjunto_completo_traz_enunciado_e_justificativa():
    conjunto = gerar(cadeia(), redator=redator_de_exemplos)

    assert conjunto["gerado"] is True
    assert conjunto["status"] == "gerado"
    assert conjunto["exemplo_introdutorio"]["nivel"] == "basico"
    assert conjunto["exemplo_introdutorio"]["enunciado"] == "enunciado de exemplo_introdutorio"
    assert conjunto["exemplo_introdutorio"]["por_que_funciona"] == "porque exemplo_introdutorio"
    assert conjunto["contraexemplo"]["nivel"] == "diagnostico"
    assert conjunto["observacoes_importantes"] == ["cuidado com o caso limite"]


def test_texto_puro_tambem_e_aceito():
    def texto_puro(briefing):
        return {
            slot["chave"]: f"exemplo de {slot['chave']}"
            for slot in briefing["slots"]
            if slot["aplicavel"]
        }

    conjunto = gerar(cadeia(), redator=texto_puro)

    assert conjunto["exemplo_pratico"]["enunciado"] == "exemplo de exemplo_pratico"
    assert conjunto["exemplo_pratico"]["por_que_funciona"] is None


def test_slot_obrigatorio_faltante_mantem_pendente():
    def incompleto(briefing):
        conjunto = redator_de_exemplos(briefing)
        del conjunto["contraexemplo"]
        return conjunto

    conjunto = gerar(cadeia(), redator=incompleto)

    assert conjunto["gerado"] is False
    assert conjunto["slots_pendentes"] == ["contraexemplo"]


def test_exercicio_ou_flashcard_devolvido_pelo_redator_e_descartado():
    def com_extra(briefing):
        conjunto = redator_de_exemplos(briefing)
        conjunto["exercicios"] = "1) Resolva..."
        conjunto["flashcards"] = [{"frente": "x", "verso": "y"}]
        return conjunto

    conjunto = gerar(cadeia(), redator=com_extra)

    assert conjunto["slots_ignorados"] == ["exercicios", "flashcards"]
    assert "exercicios" not in conjunto
    assert "flashcards" not in conjunto


def test_saida_declara_os_agentes_consumidores():
    conjunto = gerar(cadeia())
    assert conjunto["consumido_por"] == ["09", "10", "11", "13", "24"]


# --------------------------------------------------------------------------- #
# Integração
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_agente_08_no_fluxo_completo_com_redatores():
    orquestrador = MasterOrchestrator(
        RunnerEstrutural(
            redatores={"07": redator_de_aula, "08": redator_de_exemplos}
        )
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
    conjunto = resultado.saidas["08"].conteudo

    assert conjunto["status"] == "gerado"
    assert conjunto["exemplo_aplicado_ao_mundo_real"]["enunciado"]
    assert resultado.validacao.aprovado is True


@pytest.mark.asyncio
async def test_agente_08_sem_redator_fica_bloqueado_pela_teoria():
    resultado = await MasterOrchestrator().orquestrar(
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
    conjunto = resultado.saidas["08"].conteudo
    assert conjunto["bloqueio"]["motivo"] == "teoria_nao_redigida"


@pytest.mark.asyncio
async def test_agente_08_roda_depois_da_aula():
    resultado = await MasterOrchestrator().orquestrar("Explique derivadas")
    ondas = {
        agente.split()[0]: onda["onda"]
        for onda in resultado.ordem_execucao
        for agente in onda["agentes"]
    }
    assert ondas["07"] < ondas["08"]
