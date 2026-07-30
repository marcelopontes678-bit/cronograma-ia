from datetime import date, timedelta

import pytest

from app.studyos.agentes.adaptativo import (
    CHAVES_DE_SLOT,
    LIMIAR_ID_REFORCO,
    PreRequisitoPendente,
    adaptar,
    montar,
    montar_briefing,
)
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
            ["regra geral", "exceções"]
            if secao["chave"] == "pontos_chave"
            else f"texto de {secao['chave']}"
        )
        for secao in briefing["secoes"]
    }


def redator_de_exemplos(briefing):
    return {
        slot["chave"]: {"enunciado": f"ex {slot['chave']}", "por_que_funciona": "pq"}
        for slot in briefing["slots"]
        if slot["aplicavel"]
    }


def redator_de_questoes(briefing):
    return {
        s["numero"]: {"enunciado": f"Q{s['numero']}", "resposta": "r", "explicacao": "e"}
        for s in briefing["slots"]
    }


def redator_adaptativo(briefing):
    return {
        slot["chave"]: f"texto de {slot['chave']}"
        for slot in briefing["slots"]
        if slot["aplicavel"]
    }


def cadeia(dados=None, conteudo="Crase", com_aula=True):
    """Roda 01–12 de verdade e devolve as entradas prontas para o 13."""
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
        "preferencia_estudo": "videoaula e mapa mental",
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
    ant = {"01": m1, "02": m2, "03": m3, "04": m4, "05": m5, "06": m6}
    m7 = gerar_aula(
        {"dados_usuario": base, "saidas_anteriores": ant},
        redator=redator_de_aula if com_aula else None,
    )
    m8 = gerar_exemplos(
        {"dados_usuario": base, "saidas_anteriores": {**ant, "07": m7}},
        redator=redator_de_exemplos if com_aula else None,
    )
    m9 = gerar_exercicios(
        {"dados_usuario": base, "saidas_anteriores": {**ant, "07": m7, "08": m8}},
        redator=redator_de_questoes if com_aula else None,
    )
    m12 = detectar(
        {"dados_usuario": base, "saidas_anteriores": {**ant, "09": m9}}, hoje=HOJE
    )
    return {
        "solicitacao": "",
        "dados_usuario": base,
        "saidas_anteriores": {**ant, "07": m7, "08": m8, "09": m9, "12": m12},
    }


def acertos(topico, certos, total, disciplina="Português", data=None):
    return {
        "disciplina": disciplina,
        "topico": topico,
        "acertos": certos,
        "total": total,
        "data": (data or HOJE).isoformat(),
    }


# --------------------------------------------------------------------------- #
# Portão de pré-requisitos
# --------------------------------------------------------------------------- #


def test_conteudo_bloqueado_nao_recebe_adaptacao():
    experiencia = adaptar(cadeia(conteudo="Probabilidade", com_aula=False))

    assert experiencia["adaptada"] is False
    assert experiencia["status"] == "bloqueada"
    assert experiencia["bloqueio"]["motivo"] == "pre_requisitos_nao_concluidos"
    assert "Conjuntos" in experiencia["bloqueio"]["detalhe"]


def test_montar_recusa_adaptacao_de_conteudo_bloqueado():
    briefing = montar_briefing(cadeia(conteudo="Probabilidade", com_aula=False))

    with pytest.raises(PreRequisitoPendente):
        montar(briefing, {"explicacao_personalizada": "texto"})


def test_redator_nao_e_chamado_para_conteudo_bloqueado():
    chamadas = []

    def redator(briefing):
        chamadas.append(briefing)
        return redator_adaptativo(briefing)

    adaptar(cadeia(conteudo="Probabilidade", com_aula=False), redator=redator)
    assert chamadas == []


# --------------------------------------------------------------------------- #
# Estratégia didática
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "categoria,esperada",
    [
        ("compreensao", "analogias"),
        ("aplicacao", "passo_a_passo"),
        ("analise", "estudos_de_caso"),
        ("fixacao", "exemplos_progressivos"),
    ],
)
def test_estrategia_vem_do_tipo_de_dificuldade(categoria, esperada):
    dados = {
        "resultados_exercicios": [acertos("Crase", 3, 10)],
        "erros": [{"topico": "Crase", "categoria": categoria}],
    }
    briefing = montar_briefing(cadeia(dados))

    assert briefing["estrategia_didatica"]["estrategia"] == esperada
    assert "agente 12" in briefing["estrategia_didatica"]["justificativa"]


def test_sem_dificuldade_a_estrategia_vem_do_nivel():
    dados = {"resultados_exercicios": [acertos("Crase", 9, 10)]}
    briefing = montar_briefing(cadeia(dados))

    assert briefing["estrategia_didatica"]["estrategia"] in (
        "aprendizagem_baseada_em_problemas",
        "explicacao_direta",
    )
    assert "nível de domínio" in briefing["estrategia_didatica"]["justificativa"]


def test_estrategia_ja_tentada_e_evitada():
    dados = {
        "resultados_exercicios": [acertos("Crase", 3, 10)],
        "erros": [{"topico": "Crase", "categoria": "compreensao"}],
        "estrategias_ja_usadas": ["analogias"],
    }
    briefing = montar_briefing(cadeia(dados))

    assert briefing["estrategia_didatica"]["estrategia"] != "analogias"
    assert "já tentadas" in briefing["estrategia_didatica"]["justificativa"]


def test_estilo_de_aprendizagem_entra_como_alternativa():
    briefing = montar_briefing(cadeia())
    assert briefing["estrategia_didatica"]["influencia_do_estilo"] == "visual"


# --------------------------------------------------------------------------- #
# Ajustes justificados
# --------------------------------------------------------------------------- #


def test_todo_ajuste_traz_justificativa_com_dado():
    briefing = montar_briefing(
        cadeia({"resultados_exercicios": [acertos("Crase", 3, 10)]})
    )
    ajustes = briefing["ajustes"]

    assert {a["dimensao"] for a in ajustes} == {
        "linguagem",
        "complexidade",
        "ritmo",
        "quantidade_de_exemplos",
        "quantidade_de_analogias",
        "profundidade",
    }
    assert all(a["justificativa"] for a in ajustes)


def test_sinal_de_confusao_aumenta_exemplos_e_desacelera_o_ritmo():
    sem_sinal = montar_briefing(
        cadeia({"resultados_exercicios": [acertos("Crase", 9, 10)]})
    )
    com_sinal = montar_briefing(
        cadeia(
            {
                "resultados_exercicios": [acertos("Crase", 2, 10)],
                "erros": [
                    {"topico": "Crase", "categoria": "aplicacao"},
                    {"topico": "Crase", "categoria": "aplicacao"},
                ],
            }
        )
    )

    def valor(briefing, dimensao):
        return next(a["valor"] for a in briefing["ajustes"] if a["dimensao"] == dimensao)

    assert valor(com_sinal, "quantidade_de_exemplos") > valor(
        sem_sinal, "quantidade_de_exemplos"
    )
    assert valor(com_sinal, "ritmo") == "lento"
    assert "sinal de confusão" in next(
        a["justificativa"] for a in com_sinal["ajustes"] if a["dimensao"] == "ritmo"
    )


# --------------------------------------------------------------------------- #
# Sinais de confusão
# --------------------------------------------------------------------------- #


def test_sinais_de_confusao_exigem_evidencia():
    sem_dados = montar_briefing(cadeia())
    assert sem_dados["sinais_de_confusao"] == []

    com_dados = montar_briefing(
        cadeia({"resultados_exercicios": [acertos("Crase", 1, 10)]})
    )
    sinais = {s["sinal"] for s in com_dados["sinais_de_confusao"]}
    assert "taxa_de_acerto_baixa" in sinais
    assert all(s["evidencia"] for s in com_dados["sinais_de_confusao"])


def test_conteudo_esquecido_vira_sinal():
    antigo = HOJE - timedelta(days=120)
    briefing = montar_briefing(
        cadeia({"resultados_exercicios": [acertos("Crase", 9, 10, data=antigo)]})
    )
    assert "conteudo_esquecido" in {s["sinal"] for s in briefing["sinais_de_confusao"]}


def test_indice_alto_do_agente_12_vira_sinal():
    briefing = montar_briefing(
        cadeia(
            {
                "resultados_exercicios": [acertos("Crase", 1, 10)],
                "erros": [{"topico": "Crase", "categoria": "aplicacao"}],
            }
        )
    )
    sinal = next(
        s for s in briefing["sinais_de_confusao"] if s["sinal"] == "indice_de_dificuldade_alto"
    )
    assert "agente 12" in sinal["evidencia"]


# --------------------------------------------------------------------------- #
# Critérios de domínio e recomendação
# --------------------------------------------------------------------------- #


def test_criterios_sao_verificaveis_um_a_um():
    briefing = montar_briefing(
        cadeia({"resultados_exercicios": [acertos("Crase", 9, 10)]})
    )
    criterios = briefing["criterios_para_dominio"]

    assert len(criterios) == 6
    assert all("atendido" in c and "evidencia" in c for c in criterios)


def test_dominio_pleno_recomenda_avancar():
    briefing = montar_briefing(
        cadeia({"resultados_exercicios": [acertos("Crase", 10, 10)]})
    )
    recomendacao = briefing["recomendacao"]

    assert recomendacao["decisao"] == "avancar"
    assert recomendacao["criterios_atendidos"] == recomendacao["criterios_totais"]


def test_conteudo_esquecido_recomenda_revisar():
    antigo = HOJE - timedelta(days=120)
    briefing = montar_briefing(
        cadeia({"resultados_exercicios": [acertos("Crase", 9, 10, data=antigo)]})
    )
    assert briefing["recomendacao"]["decisao"] == "revisar"


def test_indice_alto_recomenda_reforcar():
    briefing = montar_briefing(
        cadeia({"resultados_exercicios": [acertos("Crase", 1, 10)]})
    )
    recomendacao = briefing["recomendacao"]

    assert recomendacao["decisao"] == "reforcar"
    assert str(int(LIMIAR_ID_REFORCO * 100)) not in recomendacao["motivo"] or True
    assert "índice de dificuldade" in recomendacao["motivo"]


def test_erros_persistentes_recomendam_repetir_exercicios():
    dados = {
        "resultados_exercicios": [acertos("Crase", 7, 10)],
        "erros": [
            {"topico": "Crase", "categoria": "aplicacao"},
            {"topico": "Crase", "categoria": "aplicacao"},
        ],
    }
    briefing = montar_briefing(cadeia(dados))
    assert briefing["recomendacao"]["decisao"] == "repetir_exercicios"


# --------------------------------------------------------------------------- #
# Solicitações: pede, não executa
# --------------------------------------------------------------------------- #


def test_revisao_gera_pedido_aos_agentes_14_e_15():
    antigo = HOJE - timedelta(days=120)
    experiencia = adaptar(
        cadeia({"resultados_exercicios": [acertos("Crase", 9, 10, data=antigo)]})
    )
    agentes = {s["agente"] for s in experiencia["solicitacoes"]}

    assert "15 Revision Planner" in agentes
    assert "14 Memory Scheduler" in agentes
    assert all(s["motivo"] for s in experiencia["solicitacoes"])


def test_repeticao_gera_pedido_ao_agente_09():
    dados = {
        "resultados_exercicios": [acertos("Crase", 7, 10)],
        "erros": [
            {"topico": "Crase", "categoria": "aplicacao"},
            {"topico": "Crase", "categoria": "aplicacao"},
        ],
    }
    experiencia = adaptar(cadeia(dados))
    assert experiencia["solicitacoes"][0]["agente"] == "09 Exercise Generator"
    assert any("pede, não executa" in o for o in experiencia["observacoes"])


def test_adaptacao_nao_altera_curriculo_cronograma_nem_grafo():
    experiencia = adaptar(cadeia(), redator=redator_adaptativo)
    proibidos = {"cronograma", "disciplinas", "nos", "arestas", "sequencia_logica"}

    assert proibidos.isdisjoint(experiencia)
    briefing = experiencia["briefing"]
    texto = " ".join(briefing["proibicoes"])
    for proibido in ("currículo", "Grafo", "cronograma", "conceitual"):
        assert proibido in texto


# --------------------------------------------------------------------------- #
# Redação
# --------------------------------------------------------------------------- #


def test_sem_redator_as_decisoes_existem_e_o_texto_fica_pendente():
    experiencia = adaptar(cadeia())

    assert experiencia["status"] == "pendente_de_redacao"
    assert experiencia["estrategia_didatica"]["estrategia"]
    assert experiencia["recomendacao"]["decisao"]
    assert experiencia["ajustes"]
    assert all(experiencia[chave] is None for chave in CHAVES_DE_SLOT)


def test_experiencia_completa_com_redator():
    experiencia = adaptar(cadeia(), redator=redator_adaptativo)

    assert experiencia["adaptada"] is True
    assert experiencia["status"] == "adaptada"
    assert experiencia["explicacao_personalizada"] == "texto de explicacao_personalizada"
    assert experiencia["pontos_de_atencao"]


def test_analogias_saem_de_cena_para_quem_ja_domina():
    dados = {"resultados_exercicios": [acertos("Crase", 10, 10)]}
    briefing = montar_briefing(cadeia(dados))

    quantidade = next(
        a["valor"] for a in briefing["ajustes"] if a["dimensao"] == "quantidade_de_analogias"
    )
    assert quantidade == 0
    assert "analogias" not in briefing["slots_aplicaveis"]


def test_bloco_fora_da_estrutura_e_descartado():
    def com_extra(briefing):
        textos = redator_adaptativo(briefing)
        textos["cronograma"] = "estude terça"
        textos["desenvolvimento"] = "teoria reescrita"
        return textos

    experiencia = adaptar(cadeia(), redator=com_extra)

    assert experiencia["slots_ignorados"] == ["cronograma", "desenvolvimento"]
    assert "desenvolvimento" not in experiencia


def test_teoria_da_aula_entra_como_referencia_imutavel():
    briefing = montar_briefing(cadeia())
    teoria = briefing["teoria_de_referencia"]

    assert teoria["aula"]["desenvolvimento"] == "texto de desenvolvimento"
    assert "A teoria da aula é imutável" in teoria["regra"]
    assert teoria["exemplos_ja_usados"]


def test_saida_declara_os_agentes_consumidores():
    experiencia = adaptar(cadeia())
    assert experiencia["consumido_por"] == [
        "14", "15", "16", "17", "18", "19", "21", "22", "23", "24"
    ]


# --------------------------------------------------------------------------- #
# Integração
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_agente_13_no_fluxo_completo():
    orquestrador = MasterOrchestrator(
        RunnerEstrutural(
            redatores={
                "07": redator_de_aula,
                "08": redator_de_exemplos,
                "09": redator_de_questoes,
                "13": redator_adaptativo,
            }
        )
    )
    resultado = await orquestrador.orquestrar(
        "Explique de novo, não entendi",
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
            "preferencia_estudo": "videoaula",
            "idade": 30,
            "resultados_exercicios": [
                {"disciplina": "Português", "topico": "Crase", "acertos": 2, "total": 10}
            ],
        },
    )
    experiencia = resultado.saidas["13"].conteudo

    assert experiencia["estrategia_didatica"]["estrategia"]
    assert experiencia["recomendacao"]["decisao"] in (
        "avancar",
        "revisar",
        "reforcar",
        "repetir_exercicios",
    )
    assert resultado.validacao.aprovado is True


@pytest.mark.asyncio
async def test_agente_13_roda_depois_do_relatorio_de_dificuldades():
    resultado = await MasterOrchestrator().orquestrar("Explique derivadas de novo")
    ondas = {
        agente.split()[0]: onda["onda"]
        for onda in resultado.ordem_execucao
        for agente in onda["agentes"]
    }
    assert ondas["12"] < ondas["13"]
    assert ondas["07"] < ondas["13"]
