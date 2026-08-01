from datetime import date

from app.studyos.agentes.conhecimento import analisar as analisar_conhecimento
from app.studyos.agentes.curriculo import construir as construir_curriculo
from app.studyos.agentes.dependencias import mapear as mapear_dependencias
from app.studyos.agentes.dificuldade import detectar
from app.studyos.agentes.erros import analisar as analisar_erros
from app.studyos.agentes.fraquezas import (
    ACAO_POR_NIVEL,
    AMPLIFICACAO_MAXIMA_DO_BLOQUEIO,
    BLOQUEIO_MAXIMO,
    NIVEIS,
    NIVEL_MAXIMO,
    PESOS_DO_INDICE,
    TAMANHO_DO_RANKING,
    VALOR_POR_CLASSIFICACAO,
    mapear,
)
from app.studyos.agentes.objetivo import analisar as analisar_objetivo
from app.studyos.agentes.perfil import analisar as analisar_perfil
from app.studyos.agentes.roadmap import construir as construir_roadmap
from app.studyos.orchestrator import MasterOrchestrator

HOJE = date(2026, 1, 5)

EDITAL = {
    "Estatística": {"questoes": 10, "topicos": ["Conjuntos", "Probabilidade"]},
    "Português": {"questoes": 20, "topicos": ["Crase", "Sintaxe"]},
}


def acertos(topico, certos, total, disciplina="Português", quando=HOJE):
    return {
        "disciplina": disciplina,
        "topico": topico,
        "acertos": certos,
        "total": total,
        "data": quando.isoformat(),
    }


#: Crase dominada, Conjuntos não — a distância entre os dois é o que o Índice
#: de Fraqueza precisa enxergar.
HISTORICO = {
    "resultados_exercicios": [
        acertos("Crase", 19, 20),
        acertos("Sintaxe", 6, 10),
        acertos("Conjuntos", 3, 10, disciplina="Estatística"),
        acertos("Probabilidade", 7, 10, disciplina="Estatística"),
    ]
}


def cadeia(dados=None, erros=None):
    """Roda 01–06, 12 e 17 de verdade e devolve as entradas prontas para o 18."""
    base = {
        "objetivo": "Passar no concurso fiscal",
        "edital": EDITAL,
        "escolaridade": "Superior completo",
        "horas_por_dia": 4,
        "dias_por_semana": 5,
        "data_prova": "2026-06-01",
        **HISTORICO,
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
    m5 = mapear_dependencias(
        {"dados_usuario": base, "saidas_anteriores": {"03": m3, "04": m4}}
    )
    m6 = construir_roadmap(
        {"dados_usuario": base, "saidas_anteriores": {"01": m1, "02": m2, "05": m5}},
        hoje=HOJE,
    )
    ant = {"01": m1, "02": m2, "03": m3, "04": m4, "05": m5, "06": m6}
    ant["12"] = detectar({"dados_usuario": base, "saidas_anteriores": ant}, hoje=HOJE)

    com_erros = {**base, "erros": erros} if erros else base
    ant["17"] = analisar_erros(
        {"dados_usuario": com_erros, "saidas_anteriores": ant}, hoje=HOJE
    )
    return {"solicitacao": "", "dados_usuario": base, "saidas_anteriores": ant}


def rodar(entradas, **campos):
    dados = {**entradas["dados_usuario"], **campos}
    return mapear({**entradas, "dados_usuario": dados}, hoje=HOJE)


def fraqueza_de(mapa, topico):
    return next(f for f in mapa["fraquezas"] if f["topico"] == topico)


# --------------------------------------------------------------------------- #
# Evidência: sem medição não há fraqueza
# --------------------------------------------------------------------------- #


def test_conteudo_sem_medicao_nao_recebe_indice():
    """Índice zero seria dizer "está estável" sobre quem ninguém mediu."""
    entradas = cadeia({"edital": {"Direito": {"topicos": ["Princípios"]}}})
    mapa = rodar(entradas)

    assert mapa["fraquezas"] == []
    assert mapa["conteudos_sem_evidencia"][0]["topico"] == "Princípios"
    assert "sem domínio medido" in mapa["conteudos_sem_evidencia"][0]["motivo"]
    assert mapa["resumo_geral"]["indice_geral_de_fragilidade"] is None
    assert mapa["confiabilidade"] == "baixa"
    assert mapa["lacunas"] == ["medicoes_de_desempenho"]


def test_todo_indice_declara_seus_componentes():
    mapa = rodar(cadeia())

    for fraqueza in mapa["fraquezas"]:
        componentes = fraqueza["indice"]["componentes"]
        assert componentes
        for nome, dados in componentes.items():
            assert nome in PESOS_DO_INDICE
            assert dados["base"]


def test_componente_ausente_nao_entra_como_zero():
    """Peso é redistribuído entre os componentes presentes, não zerado."""
    mapa = rodar(cadeia())
    conjuntos = fraqueza_de(mapa, "Conjuntos")
    componentes = conjuntos["indice"]["componentes"]

    assert "bloqueio" not in componentes
    esperado = sum(
        PESOS_DO_INDICE[c] * d["valor"] for c, d in componentes.items()
    ) / sum(PESOS_DO_INDICE[c] for c in componentes)
    assert conjuntos["indice_de_fraqueza"] == round(esperado, 4)


def test_confianca_acompanha_a_quantidade_de_componentes():
    mapa = rodar(cadeia())

    for fraqueza in mapa["fraquezas"]:
        quantidade = len(fraqueza["indice"]["componentes"])
        esperada = "alta" if quantidade >= 3 else "media" if quantidade == 2 else "baixa"
        assert fraqueza["indice"]["confianca"] == esperada


# --------------------------------------------------------------------------- #
# Índice de Fraqueza
# --------------------------------------------------------------------------- #


def test_dominio_pior_produz_indice_maior():
    mapa = rodar(cadeia())

    assert (
        fraqueza_de(mapa, "Conjuntos")["indice_de_fraqueza"]
        > fraqueza_de(mapa, "Crase")["indice_de_fraqueza"]
    )


def test_classificacao_do_agente_03_entra_com_o_valor_declarado():
    mapa = rodar(cadeia())
    conjuntos = fraqueza_de(mapa, "Conjuntos")

    assert conjuntos["indice"]["componentes"]["dominio"]["valor"] == (
        VALOR_POR_CLASSIFICACAO["nao_conhece"]
    )
    assert "agente 03" in conjuntos["indice"]["componentes"]["dominio"]["base"]


def test_bloqueio_amplia_o_indice_em_vez_de_diluir():
    """Travar outros conteúdos nunca pode deixar a fraqueza menor."""
    com_bloqueio = rodar(cadeia({"pre_requisitos": {"Probabilidade": ["Conjuntos"]}}))
    sem_bloqueio = rodar(cadeia())
    conjuntos = fraqueza_de(com_bloqueio, "Conjuntos")

    assert conjuntos["indice"]["amplificador_de_bloqueio"]["fator"] > 1
    assert "grafo do agente 05" in conjuntos["indice"]["amplificador_de_bloqueio"]["base"]
    assert conjuntos["conteudos_dependentes_afetados"] == ["Probabilidade"]
    assert (
        conjuntos["indice_de_fraqueza"]
        > fraqueza_de(sem_bloqueio, "Conjuntos")["indice_de_fraqueza"]
    )


def test_sem_bloqueio_nao_ha_amplificador():
    conjuntos = fraqueza_de(rodar(cadeia()), "Conjuntos")
    assert conjuntos["indice"]["amplificador_de_bloqueio"] is None


def test_amplificacao_satura_no_maximo_declarado():
    entradas = cadeia(
        {
            "edital": {
                "Estatística": {
                    "questoes": 10,
                    "topicos": ["Conjuntos", "A", "B", "C", "D", "E", "F", "G"],
                }
            },
            "pre_requisitos": {
                nome: ["Conjuntos"] for nome in ("A", "B", "C", "D", "E", "F", "G")
            },
        }
    )
    conjuntos = fraqueza_de(rodar(entradas), "Conjuntos")

    assert conjuntos["indice"]["amplificador_de_bloqueio"]["fator"] == round(
        1 + AMPLIFICACAO_MAXIMA_DO_BLOQUEIO, 4
    )
    assert len(conjuntos["conteudos_dependentes_afetados"]) > BLOQUEIO_MAXIMO


def test_indice_amplificado_nunca_passa_de_um():
    entradas = cadeia(
        {
            "edital": {
                "Estatística": {"questoes": 10, "topicos": ["Conjuntos", "A", "B"]}
            },
            "pre_requisitos": {nome: ["Conjuntos"] for nome in ("A", "B")},
        }
    )
    assert fraqueza_de(rodar(entradas), "Conjuntos")["indice_de_fraqueza"] <= 1.0


def test_esquecimento_entra_como_componente():
    entradas = cadeia(
        {
            "resultados_exercicios": [
                acertos("Crase", 19, 20, quando=date(2025, 6, 1)),
                acertos("Sintaxe", 6, 10),
            ]
        }
    )
    crase = fraqueza_de(rodar(entradas), "Crase")

    assert "esquecimento" in crase["indice"]["componentes"]


def test_nivel_de_prioridade_sai_das_faixas():
    mapa = rodar(cadeia())

    for fraqueza in mapa["fraquezas"]:
        assert fraqueza["nivel_de_prioridade"] in NIVEIS
    assert fraqueza_de(mapa, "Conjuntos")["nivel_de_prioridade"] == NIVEL_MAXIMO
    assert fraqueza_de(mapa, "Crase")["nivel_de_prioridade"] == "estavel"


def test_indice_geral_e_a_media_dos_conteudos_avaliados():
    mapa = rodar(cadeia())
    resumo = mapa["resumo_geral"]

    assert resumo["conteudos_avaliados"] == len(mapa["fraquezas"])
    assert resumo["indice_geral_de_fragilidade"] == round(
        sum(f["indice_de_fraqueza"] for f in mapa["fraquezas"]) / len(mapa["fraquezas"]),
        4,
    )


# --------------------------------------------------------------------------- #
# Erros do agente 17
# --------------------------------------------------------------------------- #


def test_erros_do_agente_17_entram_na_fraqueza():
    entradas = cadeia(
        erros=[
            {"topico": "Sintaxe", "disciplina": "Português", "tipo": "conceitual"},
            {"topico": "Sintaxe", "disciplina": "Português", "tipo": "conceitual"},
        ]
    )
    sintaxe = fraqueza_de(rodar(entradas), "Sintaxe")

    assert sintaxe["frequencia_de_erros"] == 2
    assert sintaxe["tipos_de_erro"]["conceitual"] == 2
    assert sintaxe["erros_recorrentes"] == 2


def test_sem_taxa_o_erro_do_17_vira_componente_com_base_declarada():
    entradas = cadeia(
        {"resultados_exercicios": []},
        erros=[{"topico": "Sintaxe", "disciplina": "Português", "tipo": "conceitual"}],
    )
    sintaxe = fraqueza_de(rodar(entradas), "Sintaxe")

    assert "erro(s) registrados pelo agente 17" in (
        sintaxe["indice"]["componentes"]["erro"]["base"]
    )


def test_competencias_comprometidas_saem_dos_erros():
    entradas = cadeia(
        erros=[
            {"topico": "Sintaxe", "disciplina": "Português", "tipo": "conceitual"},
        ]
    )
    entradas["saidas_anteriores"]["17"]["erros"][0]["competencia_avaliada"] = (
        "Aplicar o conceito"
    )
    mapa = rodar(entradas)
    competencias = mapa["ranking"]["competencias_mais_comprometidas"]

    assert competencias[0]["competencia"] == "Aplicar o conceito"
    assert competencias[0]["erros"] == 1
    assert competencias[0]["topicos"] == ["Sintaxe"]


def test_sem_erros_o_agente_declara_a_ausencia():
    mapa = rodar(cadeia())

    assert mapa["ranking"]["competencias_mais_comprometidas"] == []
    assert any("agente 17 informado" in o for o in mapa["observacoes"])


# --------------------------------------------------------------------------- #
# Impacto e urgência
# --------------------------------------------------------------------------- #


def test_impacto_declara_os_fatores_do_ganho():
    mapa = rodar(cadeia())
    impacto = fraqueza_de(mapa, "Conjuntos")["impacto_na_aprendizagem"]

    assert impacto["ganho_estimado"] > 0
    assert any("edital" in f for f in impacto["fatores"])
    assert impacto["esforco_estimado_h"] is not None


def test_conteudo_que_destrava_outros_tem_impacto_maior():
    com_bloqueio = rodar(cadeia({"pre_requisitos": {"Probabilidade": ["Conjuntos"]}}))
    sem_bloqueio = rodar(cadeia())

    assert (
        fraqueza_de(com_bloqueio, "Conjuntos")["impacto_na_aprendizagem"]["ganho_estimado"]
        > fraqueza_de(sem_bloqueio, "Conjuntos")["impacto_na_aprendizagem"]["ganho_estimado"]
    )


def test_urgencia_e_diferente_do_indice():
    """As duas listas não são a mesma lista com outro nome."""
    entradas = cadeia({"pre_requisitos": {"Probabilidade": ["Sintaxe"]}})
    mapa = rodar(entradas)
    sintaxe = fraqueza_de(mapa, "Sintaxe")

    assert sintaxe["urgencia"]["score"] != sintaxe["indice_de_fraqueza"]
    assert sintaxe["urgencia"]["fatores"]


def test_ranking_de_urgencia_diverge_do_ranking_de_indice():
    """Empate no índice é desempatado pela posição no plano — e só na urgência."""
    entradas = cadeia(
        {
            "resultados_exercicios": [
                acertos("Crase", 6, 10),
                acertos("Sintaxe", 7, 10),
                acertos("Conjuntos", 6, 10, disciplina="Estatística"),
                acertos("Probabilidade", 7, 10, disciplina="Estatística"),
            ]
        }
    )
    mapa = rodar(entradas)
    por_indice = [f["topico"] for f in mapa["ranking"]["maiores_fraquezas"]]
    por_urgencia = [f["topico"] for f in mapa["ranking"]["mais_urgentes"]]

    assert por_indice != por_urgencia
    assert mapa["ranking"]["base_das_listas"]


def test_reta_final_aumenta_a_urgencia():
    normal = rodar(cadeia())
    reta = rodar(cadeia({"data_prova": "2026-01-20"}))

    assert (
        fraqueza_de(reta, "Conjuntos")["urgencia"]["score"]
        > fraqueza_de(normal, "Conjuntos")["urgencia"]["score"]
    )
    assert any(
        "dias para a prova" in f
        for f in fraqueza_de(reta, "Conjuntos")["urgencia"]["fatores"]
    )


def test_rankings_respeitam_o_tamanho_declarado():
    mapa = rodar(cadeia())

    assert len(mapa["ranking"]["maiores_fraquezas"]) <= TAMANHO_DO_RANKING
    assert len(mapa["ranking"]["mais_urgentes"]) <= TAMANHO_DO_RANKING
    assert [f["posicao"] for f in mapa["ranking"]["maiores_fraquezas"]] == list(
        range(1, len(mapa["ranking"]["maiores_fraquezas"]) + 1)
    )


# --------------------------------------------------------------------------- #
# Recomendações
# --------------------------------------------------------------------------- #


def test_acao_segue_o_nivel_de_prioridade():
    mapa = rodar(cadeia())

    for fraqueza in mapa["fraquezas"]:
        acao = fraqueza["recomendacao"]["acao"]
        if acao != "avancar":
            assert acao == ACAO_POR_NIVEL[fraqueza["nivel_de_prioridade"]]


def test_dominio_avancado_e_retido_recebe_avancar():
    mapa = rodar(cadeia())
    crase = fraqueza_de(mapa, "Crase")

    assert crase["recomendacao"]["acao"] == "avancar"
    assert "avançado" in crase["recomendacao"]["base"]
    assert "Crase" in [c["topico"] for c in mapa["recomendacoes"]["avancar"]]


def test_esquecido_nao_recebe_avancar():
    """Domínio alto sem retenção não é conteúdo para deixar para trás."""
    entradas = cadeia(
        {
            "resultados_exercicios": [
                acertos("Crase", 19, 20, quando=date(2025, 6, 1)),
                acertos("Sintaxe", 6, 10),
            ]
        }
    )
    crase = fraqueza_de(rodar(entradas), "Crase")

    assert crase["recomendacao"]["acao"] != "avancar"


def test_recomendacao_sinaliza_o_que_ja_esta_agendado():
    entradas = cadeia()
    entradas["saidas_anteriores"]["15"] = {
        "sessoes": [{"conteudos": [{"topico": "Conjuntos"}]}]
    }
    conjuntos = fraqueza_de(rodar(entradas), "Conjuntos")

    assert conjuntos["recomendacao"]["ja_agendado_para_revisao"] is True


# --------------------------------------------------------------------------- #
# Continuidade: o mapa se atualiza
# --------------------------------------------------------------------------- #


def test_sem_mapa_anterior_a_tendencia_e_indeterminada():
    mapa = rodar(cadeia())
    tendencia = mapa["resumo_geral"]["tendencia_de_evolucao"]

    assert tendencia["disponivel"] is False
    assert tendencia["tendencia"] == "indeterminada"


def test_queda_do_indice_geral_e_lida_como_melhora():
    entradas = cadeia()
    anterior = {"resumo_geral": {"indice_geral_de_fragilidade": 0.9}}
    tendencia = rodar(entradas, mapa_de_fraquezas_anterior=anterior)["resumo_geral"][
        "tendencia_de_evolucao"
    ]

    assert tendencia["tendencia"] == "melhora"
    assert tendencia["variacao"] < 0


def test_alta_do_indice_geral_e_lida_como_piora():
    entradas = cadeia()
    anterior = {"resumo_geral": {"indice_geral_de_fragilidade": 0.05}}
    tendencia = rodar(entradas, mapa_de_fraquezas_anterior=anterior)["resumo_geral"][
        "tendencia_de_evolucao"
    ]

    assert tendencia["tendencia"] == "piora"


def test_variacao_por_conteudo_vem_do_mapa_anterior():
    entradas = cadeia()
    anterior = {
        "fraquezas": [
            {
                "topico": "Conjuntos",
                "indice_de_fraqueza": 0.5,
                "nivel_de_prioridade": "atencao",
            }
        ]
    }
    conjuntos = fraqueza_de(
        rodar(entradas, mapa_de_fraquezas_anterior=anterior), "Conjuntos"
    )

    assert conjuntos["variacao"]["indice_anterior"] == 0.5
    assert conjuntos["variacao"]["nivel_anterior"] == "atencao"
    assert conjuntos["variacao"]["variacao"] == round(
        conjuntos["indice_de_fraqueza"] - 0.5, 4
    )


def test_frequencia_de_esquecimento_acumula_entre_mapas():
    """Ela é contada ao longo dos mapas, não deduzida de um retrato só."""
    entradas = cadeia(
        {
            "resultados_exercicios": [
                acertos("Crase", 19, 20, quando=date(2025, 6, 1)),
                acertos("Sintaxe", 6, 10),
            ]
        }
    )
    primeiro = rodar(entradas)
    segundo = rodar(entradas, mapa_de_fraquezas_anterior=primeiro)

    assert fraqueza_de(primeiro, "Crase")["frequencia_de_esquecimento"] == 1
    assert fraqueza_de(segundo, "Crase")["frequencia_de_esquecimento"] == 2
    assert "acumuladas nos mapas" in fraqueza_de(segundo, "Crase")["base_do_esquecimento"]


def test_padrao_de_baixo_desempenho_exige_repeticao():
    """Uma medição ruim é uma medição; duas são um padrão."""
    uma_vez = cadeia({"resultados_exercicios": [acertos("Sintaxe", 3, 10)]})
    duas_vezes = cadeia(
        {
            "resultados_exercicios": [
                acertos("Sintaxe", 3, 10, quando=date(2025, 11, 1)),
                acertos("Sintaxe", 4, 10, quando=date(2025, 12, 1)),
            ]
        }
    )

    assert fraqueza_de(rodar(uma_vez), "Sintaxe")["padrao_de_baixo_desempenho"] is None
    padrao = fraqueza_de(rodar(duas_vezes), "Sintaxe")["padrao_de_baixo_desempenho"]
    assert padrao["ocorrencias"] == 2
    assert "abaixo de 60%" in padrao["base"]


# --------------------------------------------------------------------------- #
# Limites do agente
# --------------------------------------------------------------------------- #


def test_mapa_nao_carrega_plano_curriculo_nem_exercicio():
    mapa = rodar(cadeia())

    proibidos = ("cronograma", "plano_de_estudos", "sessoes", "exercicios", "aula", "arvore")
    assert not set(mapa) & set(proibidos)
    for fraqueza in mapa["fraquezas"]:
        assert "enunciado" not in fraqueza
        assert "conteudo_da_aula" not in fraqueza


def test_localizacao_curricular_vem_da_arvore():
    mapa = rodar(cadeia())
    conjuntos = fraqueza_de(mapa, "Conjuntos")

    assert conjuntos["disciplina"] == "Estatística"
    assert conjuntos["modulo"]
    assert conjuntos["id"].startswith("w")


def test_areas_de_risco_ordenam_por_indice_medio():
    mapa = rodar(cadeia())
    areas = mapa["resumo_geral"]["principais_areas_de_risco"]

    assert areas[0]["disciplina"] == "Estatística"
    assert [a["indice_medio"] for a in areas] == sorted(
        [a["indice_medio"] for a in areas], reverse=True
    )


def test_constantes_sao_declaradas():
    constantes = rodar(cadeia())["constantes_aplicadas"]

    assert constantes["pesos_do_indice"] == PESOS_DO_INDICE
    assert constantes["valor_por_classificacao"] == VALOR_POR_CLASSIFICACAO
    assert constantes["bloqueio_maximo"] == BLOQUEIO_MAXIMO


# --------------------------------------------------------------------------- #
# Orquestrador
# --------------------------------------------------------------------------- #


async def test_orquestrador_executa_o_18_depois_do_17():
    resultado = await MasterOrchestrator().orquestrar(
        "quais são meus pontos fracos",
        dados_usuario={
            "objetivo": "Passar no concurso fiscal",
            "edital": EDITAL,
            "escolaridade": "Superior completo",
            "horas_por_dia": 4,
            "dias_por_semana": 5,
            "data_prova": "2026-06-01",
            **HISTORICO,
        },
    )
    ordem = [sorted(onda) for onda in resultado.ondas]
    posicao = {agente: indice for indice, onda in enumerate(ordem) for agente in onda}

    assert posicao["18"] > posicao["17"] > posicao["16"]
    mapa = resultado.saidas["18"].conteudo
    assert mapa["resumo_geral"]["conteudos_avaliados"] > 0
