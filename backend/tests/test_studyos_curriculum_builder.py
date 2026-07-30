import pytest

from app.studyos.agentes.conhecimento import analisar as analisar_conhecimento
from app.studyos.agentes.curriculo import (
    HORAS_POR_MICROTOPICO,
    HORAS_POR_TOPICO_SEM_DETALHE,
    construir,
)
from app.studyos.agentes.objetivo import analisar as analisar_objetivo
from app.studyos.orchestrator import MasterOrchestrator

from datetime import date

HOJE = date(2026, 1, 1)

EDITAL_SIMPLES = {
    "Português": {"topicos": ["Crase", "Sintaxe", "Interpretação"], "questoes": 20},
    "Estatística": {"topicos": ["Probabilidade", "Distribuições"], "questoes": 10},
}

EDITAL_MODULAR = {
    "Português": {
        "questoes": 20,
        "modulos": {
            "Gramática": {
                "Crase": {"Casos obrigatórios": ["Antes de palavras femininas"]},
                "Sintaxe": ["Período composto"],
            },
            "Leitura": {"Interpretação": ["Inferência", "Tese do autor"]},
        },
    }
}


def cadeia(dados, edital=EDITAL_SIMPLES):
    """Roda 02 e 03 de verdade e devolve as entradas prontas para o 04."""
    base = {"objetivo": "Passar no concurso fiscal", "edital": edital, **dados}
    mapa_02 = analisar_objetivo({"dados_usuario": base, "solicitacao": ""}, hoje=HOJE)
    mapa_03 = analisar_conhecimento(
        {"dados_usuario": base, "saidas_anteriores": {"02": mapa_02}}, hoje=HOJE
    )
    return {
        "solicitacao": "",
        "dados_usuario": base,
        "saidas_anteriores": {"02": mapa_02, "03": mapa_03},
    }


def topicos_de(arvore, disciplina):
    d = next(x for x in arvore["disciplinas"] if x["nome"] == disciplina)
    return [t for m in d["modulos"] for t in m["topicos"]]


# --------------------------------------------------------------------------- #
# Estrutura da árvore
# --------------------------------------------------------------------------- #


def test_arvore_cobre_todas_as_disciplinas_e_topicos_do_edital():
    arvore = construir(cadeia({}))

    assert [d["nome"] for d in arvore["disciplinas"]] == ["Português", "Estatística"]
    assert arvore["totais"]["topicos"] == 5
    assert arvore["integridade"]["ok"] is True
    assert arvore["integridade"]["faltando"] == []


def test_ordem_do_edital_e_preservada():
    arvore = construir(cadeia({}))
    assert [t["nome"] for t in topicos_de(arvore, "Português")] == [
        "Crase",
        "Sintaxe",
        "Interpretação",
    ]


def test_sem_modularizacao_a_disciplina_vira_modulo_unico():
    arvore = construir(cadeia({}))
    portugues = arvore["disciplinas"][0]

    assert len(portugues["modulos"]) == 1
    assert portugues["modulos"][0]["ordem_recomendada"] == 1
    assert (
        portugues["modulos"][0]["origem"]
        == "modulo_unico_por_ausencia_de_modularizacao"
    )
    assert any("módulo" in o for o in arvore["observacoes"])


def test_edital_modular_produz_os_cinco_niveis():
    arvore = construir(cadeia({}, edital=EDITAL_MODULAR))
    portugues = arvore["disciplinas"][0]

    assert [m["nome"] for m in portugues["modulos"]] == ["Gramática", "Leitura"]
    assert [m["ordem_recomendada"] for m in portugues["modulos"]] == [1, 2]

    crase = portugues["modulos"][0]["topicos"][0]
    assert crase["nome"] == "Crase"
    assert crase["subtopicos"][0]["nome"] == "Casos obrigatórios"
    assert crase["subtopicos"][0]["microtopicos"][0]["nome"] == (
        "Antes de palavras femininas"
    )
    # Listas sob o tópico são subtópicos; só o nível aninhado vira microtópico.
    assert arvore["totais"]["subtopicos"] == 4
    assert arvore["totais"]["microtopicos"] == 1


def test_subtopicos_e_microtopicos_avulsos_sao_aceitos():
    arvore = construir(
        cadeia(
            {
                "subtopicos": {"Crase": ["Regra geral", "Casos especiais"]},
                "microtopicos": {"Regra geral": ["Antes de artigo definido"]},
            }
        )
    )
    crase = topicos_de(arvore, "Português")[0]

    assert [s["nome"] for s in crase["subtopicos"]] == ["Regra geral", "Casos especiais"]
    assert crase["subtopicos"][0]["microtopicos"][0]["nome"] == (
        "Antes de artigo definido"
    )


def test_nivel_ausente_vira_pendencia_e_nao_conteudo_inventado():
    arvore = construir(cadeia({}))
    pendencias = arvore["pendencias_de_detalhamento"]

    assert len(pendencias) == 5  # um por tópico, todos sem subtópicos
    assert {p["nivel_faltante"] for p in pendencias} == {"subtopicos"}
    assert all(t["subtopicos"] == [] for t in topicos_de(arvore, "Português"))
    assert all(t["detalhamento_pendente"] for t in topicos_de(arvore, "Português"))
    assert arvore["totais"]["subtopicos"] == 0


def test_microtopico_faltante_e_registrado_separadamente():
    arvore = construir(cadeia({"subtopicos": {"Crase": ["Regra geral"]}}))
    faltantes = [
        p
        for p in arvore["pendencias_de_detalhamento"]
        if p["nivel_faltante"] == "microtopicos"
    ]
    assert faltantes and faltantes[0]["subtopico"] == "Regra geral"


# --------------------------------------------------------------------------- #
# Classificações
# --------------------------------------------------------------------------- #


def test_importancia_vem_da_prioridade_do_agente_02():
    arvore = construir(cadeia({}))
    por_nome = {d["nome"]: d for d in arvore["disciplinas"]}

    assert por_nome["Português"]["prioridade_do_agente_02"] == "alta"
    assert por_nome["Português"]["importancia"] == "essencial"


def test_conteudo_marcado_como_opcional_perde_obrigatoriedade():
    arvore = construir(cadeia({"conteudos_opcionais": ["Interpretação"]}))
    interpretacao = next(
        t for t in topicos_de(arvore, "Português") if t["nome"] == "Interpretação"
    )

    assert interpretacao["importancia"] == "baixa"
    assert interpretacao["obrigatorio"] is False
    assert "Interpretação" in arvore["conteudos_opcionais"]
    assert "Interpretação" not in arvore["conteudos_obrigatorios"]


def test_conteudo_obrigatorio_declarado_vira_essencial():
    arvore = construir(
        cadeia({"conteudos_obrigatorios": ["Distribuições"]})
    )
    distribuicoes = next(
        t for t in topicos_de(arvore, "Estatística") if t["nome"] == "Distribuições"
    )
    assert distribuicoes["importancia"] == "essencial"
    assert "conteúdo obrigatório" in distribuicoes["base_da_importancia"]


def test_dificuldade_reflete_o_dominio_medido_pelo_agente_03():
    dados = {
        "resultados_exercicios": [
            {"disciplina": "Português", "topico": "Crase", "acertos": 10, "total": 10},
            {"disciplina": "Português", "topico": "Sintaxe", "acertos": 1, "total": 10},
        ]
    }
    arvore = construir(cadeia(dados))
    por_nome = {t["nome"]: t for t in topicos_de(arvore, "Português")}

    assert por_nome["Crase"]["dificuldade"]["grau"] == "muito_facil"
    assert por_nome["Sintaxe"]["dificuldade"]["grau"] == "dificil"
    assert por_nome["Interpretação"]["dificuldade"]["confianca"] == "baixa"


def test_esquecimento_nao_e_cobrado_duas_vezes():
    dados = {
        "disciplinas_dificuldade": ["Estatística"],
        "resultados_exercicios": [
            {
                "disciplina": "Estatística",
                "topico": "Probabilidade",
                "acertos": 7,
                "total": 10,
                "data": "2025-01-01",
            }
        ],
    }
    arvore = construir(cadeia(dados))
    probabilidade = topicos_de(arvore, "Estatística")[0]

    # O agente 03 já rebaixou 'intermediario' → 'basico' pelo esquecimento.
    # Aqui entra só a percepção: 'medio' + 1 = 'dificil'.
    assert probabilidade["dificuldade"]["grau"] == "dificil"
    fatores = probabilidade["dificuldade"]["fatores"]
    assert "domínio medido: basico" in fatores
    assert any("já rebaixada por esquecimento" in f for f in fatores)


def test_pre_requisitos_informados_entram_no_topico():
    arvore = construir(cadeia({"pre_requisitos": {"Distribuições": ["Probabilidade"]}}))
    distribuicoes = next(
        t for t in topicos_de(arvore, "Estatística") if t["nome"] == "Distribuições"
    )
    assert distribuicoes["pre_requisitos"] == ["Probabilidade"]


# --------------------------------------------------------------------------- #
# Status e tempo
# --------------------------------------------------------------------------- #


def test_status_vem_do_mapa_de_conhecimento():
    dados = {
        "resultados_exercicios": [
            {"disciplina": "Português", "topico": "Crase", "acertos": 10, "total": 10},
            {"disciplina": "Português", "topico": "Sintaxe", "acertos": 6, "total": 10},
        ]
    }
    arvore = construir(cadeia(dados))
    por_nome = {t["nome"]: t for t in topicos_de(arvore, "Português")}

    assert por_nome["Crase"]["status"] == "dominado"
    assert por_nome["Sintaxe"]["status"] == "em_andamento"
    assert por_nome["Interpretação"]["status"] == "nao_iniciado"
    assert arvore["conteudos_dominados"] == ["Crase"]
    assert "Crase" not in arvore["conteudos_pendentes"]


def test_status_do_microtopico_herda_o_topico_medido():
    dados = {
        "subtopicos": {"Crase": ["Regra geral"]},
        "microtopicos": {"Regra geral": ["Antes de artigo"]},
        "resultados_exercicios": [
            {"disciplina": "Português", "topico": "Crase", "acertos": 10, "total": 10}
        ],
    }
    arvore = construir(cadeia(dados))
    crase = topicos_de(arvore, "Português")[0]

    assert crase["subtopicos"][0]["microtopicos"][0]["status"] == "dominado"
    assert crase["subtopicos"][0]["status"] == "dominado"
    assert crase["status"] == "dominado"


def test_tempo_soma_de_baixo_para_cima():
    arvore = construir(
        cadeia(
            {
                "subtopicos": {"Crase": ["Regra geral"]},
                "microtopicos": {"Regra geral": ["A", "B", "C"]},
            }
        )
    )
    crase = topicos_de(arvore, "Português")[0]

    assert crase["subtopicos"][0]["tempo_estimado_h"] == 3 * HORAS_POR_MICROTOPICO
    assert crase["tempo_estimado_h"] == 3 * HORAS_POR_MICROTOPICO


def test_topico_sem_detalhamento_usa_o_tempo_padrao():
    arvore = construir(cadeia({}))
    assert all(
        t["tempo_estimado_h"] == HORAS_POR_TOPICO_SEM_DETALHE
        for t in topicos_de(arvore, "Português")
    )
    assert arvore["tempo_total_estimado_h"] == 5 * HORAS_POR_TOPICO_SEM_DETALHE


def test_tempo_pendente_desconta_o_que_ja_esta_dominado():
    dados = {
        "resultados_exercicios": [
            {"disciplina": "Português", "topico": "Crase", "acertos": 10, "total": 10}
        ]
    }
    arvore = construir(cadeia(dados))

    assert arvore["tempo_pendente_estimado_h"] == (
        arvore["tempo_total_estimado_h"] - HORAS_POR_TOPICO_SEM_DETALHE
    )


# --------------------------------------------------------------------------- #
# Fontes e limites
# --------------------------------------------------------------------------- #


def test_edital_e_a_referencia_quando_existe():
    arvore = construir(cadeia({}))
    assert arvore["referencia_utilizada"] == "edital"
    assert all(d["origem_da_estrutura"] == "edital" for d in arvore["disciplinas"])


def test_matriz_curricular_e_usada_na_ausencia_de_edital():
    mapa_02 = analisar_objetivo(
        {
            "dados_usuario": {"objetivo": "Concurso", "materias": ["Português"]},
            "solicitacao": "",
        },
        hoje=HOJE,
    )
    arvore = construir(
        {
            "dados_usuario": {
                "matriz_curricular": {"Português": {"topicos": ["Crase", "Sintaxe"]}}
            },
            "saidas_anteriores": {"02": mapa_02},
        }
    )
    assert arvore["referencia_utilizada"] == "matriz_curricular"
    assert [t["nome"] for t in topicos_de(arvore, "Português")] == ["Crase", "Sintaxe"]


def test_sem_referencia_a_arvore_declara_o_limite():
    mapa_02 = analisar_objetivo(
        {
            "dados_usuario": {"objetivo": "Concurso", "materias": ["Português"]},
            "solicitacao": "",
        },
        hoje=HOJE,
    )
    arvore = construir({"dados_usuario": {}, "saidas_anteriores": {"02": mapa_02}})

    assert arvore["referencia_utilizada"] == "materias_informadas"
    assert "edital_ou_matriz_curricular" in arvore["lacunas"]
    assert any("referência reconhecida da área" in o for o in arvore["observacoes"])


def test_sem_disciplinas_nao_ha_curriculo():
    arvore = construir({"dados_usuario": {}, "saidas_anteriores": {}})

    assert arvore["disciplinas"] == []
    assert arvore["confiabilidade"] == "baixa"
    assert "mapa_estrategico_do_agente_02" in arvore["lacunas"]


def test_saida_nao_contem_aulas_exercicios_nem_cronograma():
    arvore = construir(cadeia({}))
    proibidos = {"aulas", "exercicios", "questoes", "cronograma", "resumos", "datas"}
    assert proibidos.isdisjoint(arvore)


def test_saida_declara_os_agentes_consumidores():
    arvore = construir(cadeia({}))
    assert arvore["consumido_por"] == [
        "05", "06", "07", "09", "10", "11", "14", "15", "16", "23"
    ]


# --------------------------------------------------------------------------- #
# Integração
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_agente_04_recebe_as_tres_saidas_anteriores():
    resultado = await MasterOrchestrator().orquestrar(
        "Monte um cronograma para o concurso",
        dados_usuario={
            "objetivo": "Passar no concurso fiscal",
            "edital": EDITAL_MODULAR,
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
                    "acertos": 10,
                    "total": 10,
                    "tipo": "simulado",
                }
            ],
        },
    )
    arvore = resultado.saidas["04"].conteudo

    assert arvore["objetivo"] == "Passar no concurso fiscal"
    assert arvore["referencia_utilizada"] == "edital"
    assert arvore["totais"]["modulos"] == 2
    assert "Crase" in arvore["conteudos_dominados"]
    assert resultado.validacao.aprovado is True


@pytest.mark.asyncio
async def test_agente_04_roda_depois_do_diagnostico():
    resultado = await MasterOrchestrator().orquestrar("Monte um cronograma")
    ondas = {
        agente.split()[0]: onda["onda"]
        for onda in resultado.ordem_execucao
        for agente in onda["agentes"]
    }
    assert ondas["03"] < ondas["04"]
    assert ondas["01"] < ondas["04"]
