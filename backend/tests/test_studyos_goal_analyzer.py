from datetime import date

import pytest

from app.studyos.agentes.objetivo import HORAS_POR_TOPICO, analisar
from app.studyos.agentes.perfil import analisar as analisar_perfil
from app.studyos.orchestrator import MasterOrchestrator

HOJE = date(2026, 1, 1)

EDITAL = {
    "Português": {"topicos": ["Sintaxe", "Crase", "Interpretação"], "questoes": 20},
    "Direito Constitucional": {
        "topicos": ["Princípios", "Direitos fundamentais"],
        "questoes": 15,
    },
    "Estatística": {"topicos": ["Probabilidade"], "questoes": 5},
}


def entradas(dados=None, perfil=None, solicitacao="Quero passar no concurso"):
    return {
        "solicitacao": solicitacao,
        "dados_usuario": dados or {},
        "saidas_anteriores": {"01": perfil} if perfil else {},
    }


def perfil_padrao(**overrides):
    dados = {
        "escolaridade": "Superior completo",
        "objetivo": "Passar no concurso do ICMS",
        "profissao": "Analista",
        "rotina": "Trabalho durante o dia",
        "horas_por_dia": 4,
        "dias_por_semana": 5,
        "data_prova": "2026-07-01",
        "experiencia_anterior": "nenhuma",
        "disciplinas_favoritas": ["Português"],
        "disciplinas_dificuldade": ["Estatística"],
        "preferencia_estudo": "questões",
        "idade": 30,
    }
    dados.update(overrides)
    return analisar_perfil({"dados_usuario": dados}, hoje=HOJE)


# --------------------------------------------------------------------------- #
# Categoria e objetivos
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "objetivo,esperado",
    [
        ("Passar no concurso do Tribunal de Justiça", "concurso_publico"),
        ("Quero gabaritar o ENEM", "enem"),
        ("Passar no vestibular da Fuvest", "vestibular"),
        ("Tirar a certificação AWS Solutions Architect", "certificacao"),
        ("Chegar à fluência em inglês", "idiomas"),
        ("Passar em Cálculo 2 na faculdade", "faculdade"),
        ("Quero uma promoção na carreira", "desenvolvimento_profissional"),
    ],
)
def test_categoria_do_objetivo(objetivo, esperado):
    resultado = analisar(entradas({"objetivo": objetivo}), hoje=HOJE)
    assert resultado["categoria_objetivo"]["categoria"] == esperado


def test_categoria_indeterminada_nao_e_chutada():
    resultado = analisar(
        entradas({"objetivo": "melhorar um pouco"}, solicitacao="me ajuda"), hoje=HOJE
    )
    assert resultado["categoria_objetivo"]["categoria"] is None
    assert resultado["competencias_necessarias"] == []
    assert any("Categoria" in o for o in resultado["observacoes"])


def test_objetivo_declarado_tem_precedencia_sobre_a_solicitacao():
    resultado = analisar(
        entradas(
            {"objetivo": "Chegar à fluência em inglês"},
            solicitacao="monte um cronograma para o concurso",
        ),
        hoje=HOJE,
    )
    assert resultado["categoria_objetivo"]["categoria"] == "idiomas"
    assert resultado["categoria_objetivo"]["base"] == "termos encontrados em objetivo/exame"


def test_solicitacao_classifica_quando_o_objetivo_nao_basta():
    resultado = analisar(
        entradas({"objetivo": "ir bem"}, solicitacao="quero gabaritar o ENEM"),
        hoje=HOJE,
    )
    assert resultado["categoria_objetivo"]["categoria"] == "enem"
    assert "solicitação" in resultado["categoria_objetivo"]["base"]


def test_objetivos_secundarios_saem_de_separadores_explicitos():
    resultado = analisar(
        entradas({"objetivo": "Passar no ENEM; melhorar a redação"}), hoje=HOJE
    )
    assert resultado["objetivo_principal"] == "Passar no ENEM"
    assert resultado["objetivos_secundarios"] == ["melhorar a redação"]


def test_objetivos_secundarios_informados_tem_precedencia():
    resultado = analisar(
        entradas(
            {
                "objetivo": "Passar no concurso",
                "objetivos_secundarios": ["aprender inglês", "manter a rotina"],
            }
        ),
        hoje=HOJE,
    )
    assert resultado["objetivos_secundarios"] == ["aprender inglês", "manter a rotina"]


# --------------------------------------------------------------------------- #
# Disciplinas — nunca inventadas
# --------------------------------------------------------------------------- #


def test_disciplinas_vem_do_edital_quando_existe():
    resultado = analisar(
        entradas({"objetivo": "Concurso fiscal", "edital": EDITAL}), hoje=HOJE
    )
    nomes = [d["nome"] for d in resultado["disciplinas"]]

    assert nomes == ["Português", "Direito Constitucional", "Estatística"]
    assert resultado["cobertura_das_disciplinas"] == "edital"
    assert all(d["origem"] == "edital" for d in resultado["disciplinas"])


def test_edital_tem_precedencia_sobre_materias():
    resultado = analisar(
        entradas(
            {
                "objetivo": "Concurso",
                "edital": EDITAL,
                "materias": ["Matemática Financeira"],
            }
        ),
        hoje=HOJE,
    )
    assert "Matemática Financeira" not in [d["nome"] for d in resultado["disciplinas"]]


def test_sem_edital_usa_materias_e_avisa_sobre_matriz_equivalente():
    resultado = analisar(
        entradas({"objetivo": "Concurso", "materias": "Português, RLM"}), hoje=HOJE
    )
    assert [d["nome"] for d in resultado["disciplinas"]] == ["Português", "RLM"]
    assert resultado["cobertura_das_disciplinas"] == "materias_informadas"
    assert any("matriz curricular equivalente" in o for o in resultado["observacoes"])

    requisito = next(
        r for r in resultado["requisitos_obrigatorios"] if r["requisito"] == "edital"
    )
    assert requisito["status"] == "ausente"


def test_sem_nenhuma_fonte_nao_inventa_disciplina():
    resultado = analisar(entradas({"objetivo": "Passar no concurso"}), hoje=HOJE)

    assert resultado["disciplinas"] == []
    assert resultado["prioridade_disciplinas"] == []
    assert resultado["cobertura_das_disciplinas"] == "indefinida"
    assert resultado["confiabilidade"] == "baixa"
    assert any("Nenhuma disciplina" in o for o in resultado["observacoes"])


def test_edital_como_lista_de_dicts_e_aceito():
    resultado = analisar(
        entradas(
            {
                "objetivo": "Concurso",
                "edital": [
                    {"disciplina": "Português", "topicos": ["Crase"], "peso": 2},
                    {"nome": "RLM", "conteudos": ["Lógica"], "peso": 1},
                ],
            }
        ),
        hoje=HOJE,
    )
    assert [d["nome"] for d in resultado["disciplinas"]] == ["Português", "RLM"]
    assert resultado["disciplinas"][0]["peso"] == 2.0


def test_disciplinas_do_perfil_entram_como_cobertura_parcial():
    resultado = analisar(
        entradas(
            {
                "objetivo": "Concurso",
                "disciplinas_favoritas": ["Português"],
                "disciplinas_dificuldade": ["Estatística"],
            }
        ),
        hoje=HOJE,
    )
    assert resultado["cobertura_das_disciplinas"] == "parcial_declarada_no_perfil"
    assert {d["nome"] for d in resultado["disciplinas"]} == {"Português", "Estatística"}


# --------------------------------------------------------------------------- #
# Prioridade, carga e prazo
# --------------------------------------------------------------------------- #


def test_prioridade_combina_peso_dificuldade_e_volume():
    resultado = analisar(
        entradas(
            {
                "objetivo": "Concurso",
                "edital": EDITAL,
                "disciplinas_favoritas": ["Português"],
                "disciplinas_dificuldade": ["Estatística"],
            }
        ),
        hoje=HOJE,
    )
    por_disciplina = {p["disciplina"]: p for p in resultado["prioridade_disciplinas"]}

    # Estatística tem peso baixo, mas dificuldade declarada sobe seu score.
    assert por_disciplina["Estatística"]["score"] > 2
    assert any(
        "dificuldade declarada" in f for f in por_disciplina["Estatística"]["fatores"]
    )
    # Português tem o maior peso do edital e continua prioritário.
    assert por_disciplina["Português"]["prioridade"] == "alta"


def test_nivel_minimo_acompanha_a_prioridade():
    resultado = analisar(
        entradas({"objetivo": "Concurso", "edital": EDITAL}), hoje=HOJE
    )
    for prioridade in resultado["prioridade_disciplinas"]:
        esperado = {"alta": "avancado", "media": "intermediario", "baixa": "basico"}
        assert prioridade["nivel_minimo_esperado"] == esperado[prioridade["prioridade"]]


def test_carga_estimada_usa_os_topicos_do_edital():
    resultado = analisar(
        entradas({"objetivo": "Concurso", "edital": EDITAL}), hoje=HOJE
    )
    carga = resultado["estimativa_carga_estudo"]

    assert carga["total_topicos"] == 6
    assert carga["horas_estimadas"] == pytest.approx(6 * HORAS_POR_TOPICO)
    assert carga["precisao"] == "alta"


def test_carga_sem_topicos_cai_para_estimativa_grosseira():
    resultado = analisar(
        entradas({"objetivo": "Concurso", "materias": ["A", "B"]}), hoje=HOJE
    )
    carga = resultado["estimativa_carga_estudo"]

    assert carga["precisao"] == "baixa"
    assert carga["horas_estimadas"] == 60.0


def test_tempo_disponivel_vem_do_agente_01():
    perfil = perfil_padrao()
    resultado = analisar(
        entradas({"objetivo": "Concurso", "edital": EDITAL}, perfil=perfil), hoje=HOJE
    )
    tempo = resultado["tempo_disponivel"]

    assert tempo["horas_semanais_efetivas"] == perfil["tempo_disponivel"][
        "horas_semanais_efetivas"
    ]
    assert tempo["origem"] == "agente 01 Profile Analyzer"


def test_prazo_viavel_quando_ha_folga():
    perfil = perfil_padrao(horas_por_dia=6, dias_por_semana=6)
    resultado = analisar(
        entradas(
            {"objetivo": "Concurso", "edital": EDITAL, "data_prova": "2026-07-01"},
            perfil=perfil,
        ),
        hoje=HOJE,
    )
    assert resultado["restricoes_de_prazo"]["viabilidade"] == "viavel"
    assert resultado["restricoes_de_prazo"]["deficit_horas"] == 0


def test_prazo_inviavel_gera_deficit_em_horas():
    edital_grande = {f"Disciplina {i}": [f"T{j}" for j in range(20)] for i in range(10)}
    perfil = perfil_padrao(horas_por_dia=1, dias_por_semana=2, data_prova="2026-02-01")
    resultado = analisar(
        entradas(
            {"objetivo": "Concurso", "edital": edital_grande, "data_prova": "2026-02-01"},
            perfil=perfil,
        ),
        hoje=HOJE,
    )
    restricoes = resultado["restricoes_de_prazo"]

    assert restricoes["viabilidade"] == "inviavel_no_ritmo_atual"
    assert restricoes["deficit_horas"] > 0
    assert restricoes["horas_semanais_necessarias"] > restricoes[
        "horas_semanais_disponiveis"
    ]


def test_viabilidade_indeterminada_sem_perfil_ou_sem_prazo():
    resultado = analisar(
        entradas({"objetivo": "Concurso", "edital": EDITAL}), hoje=HOJE
    )
    assert resultado["restricoes_de_prazo"]["viabilidade"] == "indeterminada"
    assert "perfil_cognitivo_do_agente_01" in resultado["lacunas"]


# --------------------------------------------------------------------------- #
# Competências, requisitos e critérios
# --------------------------------------------------------------------------- #


def test_competencias_saem_do_catalogo_com_origem_declarada():
    resultado = analisar(entradas({"objetivo": "Gabaritar o ENEM"}), hoje=HOJE)
    competencias = resultado["competencias_necessarias"]

    assert any("redação" in c["competencia"] for c in competencias)
    assert all(c["origem"] == "catalogo_por_categoria" for c in competencias)


def test_bibliografia_informada_vira_requisito_disponivel():
    resultado = analisar(
        entradas(
            {
                "objetivo": "Concurso",
                "edital": EDITAL,
                "bibliografia": ["Manual de Direito Constitucional"],
                "materiais_obrigatorios": ["Lei seca atualizada"],
            }
        ),
        hoje=HOJE,
    )
    requisitos = {r["requisito"]: r for r in resultado["requisitos_obrigatorios"]}

    assert requisitos["bibliografia"]["status"] == "disponivel"
    assert requisitos["materiais_obrigatorios"]["status"] == "disponivel"


def test_criterios_de_sucesso_incluem_nota_de_corte_e_prazo():
    resultado = analisar(
        entradas(
            {
                "objetivo": "Concurso",
                "edital": EDITAL,
                "nota_corte": 75,
                "data_prova": "2026-07-01",
            }
        ),
        hoje=HOJE,
    )
    criterios = " | ".join(resultado["criterios_sucesso"])

    assert "75" in criterios
    assert "100% dos tópicos do edital" in criterios
    assert "2026-07-01" in criterios


def test_saida_declara_os_agentes_consumidores():
    resultado = analisar(entradas({"objetivo": "Concurso"}), hoje=HOJE)
    assert resultado["consumido_por"] == ["04", "05", "06", "16", "21", "22"]


# --------------------------------------------------------------------------- #
# Integração com o orquestrador
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_agente_02_recebe_o_perfil_do_agente_01():
    resultado = await MasterOrchestrator().orquestrar(
        "Monte um cronograma para o concurso",
        dados_usuario={
            "objetivo": "Passar no concurso do ICMS",
            "edital": EDITAL,
            "escolaridade": "Superior completo",
            "horas_por_dia": 4,
            "dias_por_semana": 5,
            "data_prova": "2027-01-01",
            "profissao": "Analista",
            "rotina": "Trabalho durante o dia",
            "experiencia_anterior": "nenhuma",
            "disciplinas_favoritas": ["Português"],
            "disciplinas_dificuldade": ["Estatística"],
            "preferencia_estudo": "questões",
            "idade": 30,
        },
    )
    mapa = resultado.saidas["02"].conteudo

    assert mapa["categoria_objetivo"]["categoria"] == "concurso_publico"
    assert mapa["tempo_disponivel"]["horas_semanais_efetivas"] is not None
    assert mapa["restricoes_de_prazo"]["viabilidade"] != "indeterminada"
    assert resultado.validacao.aprovado is True


@pytest.mark.asyncio
async def test_agente_02_roda_depois_do_01():
    resultado = await MasterOrchestrator().orquestrar("Monte um cronograma")
    ondas = {
        agente["codigo"]: onda["onda"]
        for onda in resultado.ordem_execucao
        for agente in [{"codigo": a.split()[0]} for a in onda["agentes"]]
    }
    assert ondas["01"] < ondas["02"]
