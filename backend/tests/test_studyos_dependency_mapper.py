from datetime import date

import pytest

from app.studyos.agentes.conhecimento import analisar as analisar_conhecimento
from app.studyos.agentes.curriculo import construir as construir_curriculo
from app.studyos.agentes.dependencias import mapear
from app.studyos.agentes.objetivo import analisar as analisar_objetivo
from app.studyos.orchestrator import MasterOrchestrator

HOJE = date(2026, 1, 1)

EDITAL = {
    "Estatística": {
        "questoes": 10,
        "topicos": ["Conjuntos", "Probabilidade", "Distribuições"],
    },
    "Português": {"questoes": 20, "topicos": ["Crase", "Sintaxe"]},
}


def cadeia(dados=None, edital=EDITAL):
    """Roda 02, 03 e 04 de verdade e devolve as entradas prontas para o 05."""
    base = {"objetivo": "Passar no concurso fiscal", "edital": edital, **(dados or {})}
    mapa_02 = analisar_objetivo({"dados_usuario": base, "solicitacao": ""}, hoje=HOJE)
    mapa_03 = analisar_conhecimento(
        {"dados_usuario": base, "saidas_anteriores": {"02": mapa_02}}, hoje=HOJE
    )
    arvore = construir_curriculo(
        {"dados_usuario": base, "saidas_anteriores": {"02": mapa_02, "03": mapa_03}}
    )
    return {
        "solicitacao": "",
        "dados_usuario": base,
        "saidas_anteriores": {"02": mapa_02, "03": mapa_03, "04": arvore},
    }


def no_por_nome(grafo, nome):
    return next(n for n in grafo["nos"] if n["nome"] == nome)


PRE = {
    "pre_requisitos": {
        "Probabilidade": ["Conjuntos"],
        "Distribuições": ["Probabilidade"],
    }
}


# --------------------------------------------------------------------------- #
# Nós e arestas
# --------------------------------------------------------------------------- #


def test_todos_os_niveis_viram_nos_com_id_unico():
    grafo = mapear(cadeia())
    ids = [n["id"] for n in grafo["nos"]]

    assert len(ids) == len(set(ids))
    assert grafo["totais"]["por_tipo"]["disciplina"] == 2
    assert grafo["totais"]["por_tipo"]["modulo"] == 2
    assert grafo["totais"]["por_tipo"]["topico"] == 5
    assert no_por_nome(grafo, "Conjuntos")["id"] == "d1.m1.t1"


def test_arestas_saem_dos_pre_requisitos_declarados():
    grafo = mapear(cadeia(PRE))
    probabilidade = no_por_nome(grafo, "Probabilidade")
    conjuntos = no_por_nome(grafo, "Conjuntos")

    assert probabilidade["pre_requisitos"] == [conjuntos["id"]]
    assert conjuntos["dependentes"] == [probabilidade["id"]]
    assert grafo["totais"]["arestas"] == 2


def test_ordem_do_edital_nao_vira_dependencia():
    grafo = mapear(cadeia())

    assert grafo["totais"]["arestas"] == 0
    assert all(n["status"] == "disponivel" for n in grafo["nos"])
    assert any("não foram inferidas da ordem do edital" in o for o in grafo["observacoes"])


def test_contencao_nao_vira_dependencia():
    grafo = mapear(cadeia(PRE))
    topico = no_por_nome(grafo, "Conjuntos")

    assert topico["contido_em"] == "d1.m1"
    assert topico["pre_requisitos"] == []


def test_pre_requisito_inexistente_nao_vira_aresta():
    grafo = mapear(cadeia({"pre_requisitos": {"Probabilidade": ["Cálculo I"]}}))

    assert grafo["totais"]["arestas"] == 0
    assert grafo["dependencias_nao_resolvidas"][0]["pre_requisito"] == "Cálculo I"
    assert "não encontrado" in grafo["dependencias_nao_resolvidas"][0]["motivo"]


def test_auto_dependencia_e_descartada():
    grafo = mapear(cadeia({"pre_requisitos": {"Crase": ["Crase"]}}))

    assert no_por_nome(grafo, "Crase")["pre_requisitos"] == []
    assert any(
        d["motivo"] == "auto-dependência descartada"
        for d in grafo["dependencias_nao_resolvidas"]
    )


# --------------------------------------------------------------------------- #
# Ciclos
# --------------------------------------------------------------------------- #


def test_ciclo_e_detectado_e_eliminado():
    grafo = mapear(
        cadeia(
            {
                "pre_requisitos": {
                    "Conjuntos": ["Distribuições"],  # aresta que volta no currículo
                    "Probabilidade": ["Conjuntos"],
                    "Distribuições": ["Probabilidade"],
                }
            }
        )
    )

    assert grafo["acilico"] is True
    assert len(grafo["ciclos_eliminados"]) == 1
    removida = grafo["ciclos_eliminados"][0]
    assert removida["nomes"] == "Conjuntos → Distribuições"
    assert "ordem do currículo" in removida["motivo"]
    # As dependências que respeitam a ordem do edital sobrevivem.
    assert no_por_nome(grafo, "Probabilidade")["pre_requisitos"] == [
        no_por_nome(grafo, "Conjuntos")["id"]
    ]


def test_grafo_sem_ciclo_nao_remove_nada():
    grafo = mapear(cadeia(PRE))
    assert grafo["ciclos_eliminados"] == []


# --------------------------------------------------------------------------- #
# Status, paralelismo e profundidade
# --------------------------------------------------------------------------- #


def test_status_bloqueado_enquanto_o_pre_requisito_nao_esta_dominado():
    grafo = mapear(cadeia(PRE))

    assert no_por_nome(grafo, "Conjuntos")["status"] == "disponivel"
    assert no_por_nome(grafo, "Probabilidade")["status"] == "bloqueado"
    assert no_por_nome(grafo, "Probabilidade")["bloqueado_por"] == [
        no_por_nome(grafo, "Conjuntos")["id"]
    ]


def test_dominio_medido_libera_o_dependente():
    dados = dict(PRE)
    dados["resultados_exercicios"] = [
        {"disciplina": "Estatística", "topico": "Conjuntos", "acertos": 10, "total": 10}
    ]
    grafo = mapear(cadeia(dados))

    assert no_por_nome(grafo, "Conjuntos")["status"] == "concluido"
    assert no_por_nome(grafo, "Conjuntos")["ignoravel_no_planejamento"] is True
    assert no_por_nome(grafo, "Probabilidade")["status"] == "disponivel"


def test_bloqueio_de_ancestral_desce_sem_criar_aresta():
    grafo = mapear(
        cadeia(
            {
                "pre_requisitos": {"Português": ["Estatística"]},
                "subtopicos": {"Crase": ["Regra geral"]},
            }
        )
    )
    subtopico = no_por_nome(grafo, "Regra geral")

    assert subtopico["status"] == "bloqueado"
    assert subtopico["pre_requisitos"] == []  # nenhuma aresta inventada
    assert subtopico["bloqueado_por_ancestral"]


def test_profundidade_cresce_com_a_cadeia():
    grafo = mapear(cadeia(PRE))

    assert no_por_nome(grafo, "Conjuntos")["profundidade"] == 0
    assert no_por_nome(grafo, "Probabilidade")["profundidade"] == 1
    assert no_por_nome(grafo, "Distribuições")["profundidade"] == 2
    assert grafo["profundidade_maxima"] == 2


def test_nos_sem_dependencia_entre_si_sao_paralelizaveis():
    grafo = mapear(cadeia(PRE))
    crase = no_por_nome(grafo, "Crase")

    assert crase["pode_ser_estudado_em_paralelo"] is True
    assert no_por_nome(grafo, "Conjuntos")["id"] in crase["paralelo_com"]
    assert no_por_nome(grafo, "Probabilidade")["id"] not in crase["paralelo_com"]


def test_ondas_agrupam_o_que_pode_andar_junto():
    grafo = mapear(cadeia(PRE))
    ondas = grafo["ondas_de_estudo"]

    assert ondas[0]["paralelo"] is True
    assert no_por_nome(grafo, "Probabilidade")["id"] in ondas[1]["nos"]
    assert no_por_nome(grafo, "Distribuições")["id"] in ondas[2]["nos"]


# --------------------------------------------------------------------------- #
# Caminhos, críticos e sequência
# --------------------------------------------------------------------------- #


def test_caminho_principal_e_a_cadeia_mais_longa():
    grafo = mapear(cadeia(PRE))
    principal = grafo["caminho_principal"]

    assert principal["nomes"] == ["Conjuntos", "Probabilidade", "Distribuições"]
    assert principal["tempo_h"] == 7.5  # 3 tópicos × 2.5h


def test_no_bloqueador_e_ordenado_por_dependentes_transitivos():
    grafo = mapear(cadeia(PRE))
    criticos = grafo["nos_criticos"]

    assert criticos[0]["nome"] == "Conjuntos"
    assert criticos[0]["dependentes_transitivos"] == 2
    assert criticos[1]["nome"] == "Probabilidade"


def test_nos_independentes_nao_tem_pre_requisito_nem_dependente():
    grafo = mapear(cadeia(PRE))
    nomes = {n["nome"] for n in grafo["nos"] if n["id"] in grafo["nos_independentes"]}

    assert "Crase" in nomes
    assert "Probabilidade" not in nomes


def test_sequencia_respeita_o_grafo_e_desempata_pelo_edital():
    grafo = mapear(cadeia(PRE))
    nomes = [item["nome"] for item in grafo["sequencia_logica"]]

    assert nomes.index("Conjuntos") < nomes.index("Probabilidade")
    assert nomes.index("Probabilidade") < nomes.index("Distribuições")


def test_sequencia_ignora_o_que_ja_esta_dominado():
    dados = dict(PRE)
    dados["resultados_exercicios"] = [
        {"disciplina": "Português", "topico": "Crase", "acertos": 10, "total": 10}
    ]
    grafo = mapear(cadeia(dados))
    nomes = [item["nome"] for item in grafo["sequencia_logica"]]

    assert "Crase" not in nomes
    assert no_por_nome(grafo, "Crase")["id"] in grafo["conteudos_ignoraveis"]


def test_conteudo_opcional_e_marcado():
    grafo = mapear(cadeia({**PRE, "conteudos_opcionais": ["Sintaxe"]}))
    assert no_por_nome(grafo, "Sintaxe")["id"] in grafo["conteudos_opcionais"]


# --------------------------------------------------------------------------- #
# Limites e integração
# --------------------------------------------------------------------------- #


def test_sem_arvore_nao_ha_grafo():
    grafo = mapear({"dados_usuario": {}, "saidas_anteriores": {}})

    assert grafo["nos"] == []
    assert grafo["confiabilidade"] == "baixa"
    assert "arvore_curricular_do_agente_04" in grafo["lacunas"]


def test_saida_nao_contem_cronograma_nem_conteudo():
    grafo = mapear(cadeia(PRE))
    proibidos = {"cronograma", "aulas", "exercicios", "datas", "resumos"}
    assert proibidos.isdisjoint(grafo)


def test_saida_declara_os_agentes_consumidores():
    grafo = mapear(cadeia())
    assert grafo["consumido_por"] == [
        "06", "07", "09", "10", "11", "14", "15", "16", "23", "24"
    ]


@pytest.mark.asyncio
async def test_agente_05_no_fluxo_completo():
    resultado = await MasterOrchestrator().orquestrar(
        "Monte um cronograma para o concurso",
        dados_usuario={
            "objetivo": "Passar no concurso fiscal",
            "edital": EDITAL,
            "pre_requisitos": {
                "Probabilidade": ["Conjuntos"],
                "Distribuições": ["Probabilidade"],
            },
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
    grafo = resultado.saidas["05"].conteudo

    assert grafo["acilico"] is True
    assert grafo["profundidade_maxima"] == 2
    assert grafo["caminho_principal"]["nomes"][0] == "Conjuntos"
    assert resultado.validacao.aprovado is True


@pytest.mark.asyncio
async def test_agente_05_roda_depois_da_arvore():
    resultado = await MasterOrchestrator().orquestrar("Monte um cronograma")
    ondas = {
        agente.split()[0]: onda["onda"]
        for onda in resultado.ordem_execucao
        for agente in onda["agentes"]
    }
    assert ondas["04"] < ondas["05"]
