from datetime import date, timedelta

import pytest

from app.studyos.agentes.perfil import (
    FATOR_EFETIVIDADE_PADRAO,
    FATOR_EFETIVIDADE_ROTINA_INTENSA,
    TETO_COGNITIVO_DIARIO_H,
    analisar,
)
from app.studyos.orchestrator import MasterOrchestrator

HOJE = date(2026, 1, 1)


def perfil_completo(**overrides):
    dados = {
        "nome": "Marcelo",
        "idade": 29,
        "escolaridade": "Superior completo",
        "objetivo": "Passar em concurso da área fiscal",
        "exame": "ICMS-SP",
        "profissao": "Analista administrativo",
        "rotina": "Trabalho de segunda a sexta, estudo à noite",
        "horas_por_dia": 3,
        "dias_por_semana": 5,
        "data_prova": "2026-10-01",
        "experiencia_anterior": "Já estudei um ano para concurso",
        "disciplinas_favoritas": ["Português", "Direito Constitucional"],
        "disciplinas_dificuldade": ["Estatística"],
        "preferencia_estudo": "Prefiro vídeo aula e mapa mental",
        "idioma": "pt-BR",
        "restricoes": [],
        "necessidades_especiais": [],
    }
    dados.update(overrides)
    return {"dados_usuario": dados}


def test_tempo_disponivel_e_calculado_a_partir_do_declarado():
    resultado = analisar(perfil_completo(), hoje=HOJE)
    tempo = resultado["tempo_disponivel"]

    assert tempo["horas_semanais_declaradas"] == 15.0
    assert tempo["horas_semanais_efetivas"] == pytest.approx(
        15.0 * FATOR_EFETIVIDADE_PADRAO
    )
    assert tempo["calculavel"] is True


def test_rotina_intensa_reduz_o_fator_de_efetividade():
    resultado = analisar(
        perfil_completo(rotina="Trabalho em tempo integral, 44h semanais"), hoje=HOJE
    )
    assert resultado["tempo_disponivel"]["rotina_intensa"] is True
    assert (
        resultado["tempo_disponivel"]["fator_efetividade"]
        == FATOR_EFETIVIDADE_ROTINA_INTENSA
    )
    assert any(r["risco"] == "rotina_conflitante" for r in resultado["riscos"])


def test_carga_maxima_diaria_respeita_o_teto_cognitivo():
    resultado = analisar(perfil_completo(horas_por_dia=12), hoje=HOJE)
    carga = resultado["carga_maxima_diaria"]

    assert carga["horas"] == TETO_COGNITIVO_DIARIO_H
    assert carga["limitado_pelo_teto"] is True
    assert carga["blocos"] == 6  # 360 min em ciclos de 50+10
    assert any(r["risco"] == "sobrecarga" for r in resultado["riscos"])


def test_prazo_calcula_horas_totais_ate_a_prova():
    prova = HOJE + timedelta(days=70)
    resultado = analisar(
        perfil_completo(data_prova=prova.isoformat()), hoje=HOJE
    )
    prazo = resultado["prazo"]

    assert prazo["dias_restantes"] == 70
    assert prazo["horas_totais_efetivas"] == pytest.approx(15.0 * 0.85 * 10, rel=1e-3)


def test_prazo_curto_vira_risco_alto():
    prova = HOJE + timedelta(days=20)
    resultado = analisar(
        perfil_completo(data_prova=prova.isoformat(), horas_por_dia=2, dias_por_semana=3),
        hoje=HOJE,
    )
    risco = next(r for r in resultado["riscos"] if r["risco"] == "prazo_curto")
    assert risco["severidade"] == "alta"


def test_estilo_de_aprendizagem_vem_da_preferencia_declarada():
    resultado = analisar(perfil_completo(), hoje=HOJE)
    assert resultado["estilo_aprendizagem"]["predominante"] == "visual"

    pratico = analisar(
        perfil_completo(preferencia_estudo="Só aprendo resolvendo questões"), hoje=HOJE
    )
    assert pratico["estilo_aprendizagem"]["predominante"] == "cinestesico"


def test_estilo_ausente_nao_e_inventado():
    resultado = analisar(
        perfil_completo(preferencia_estudo=None, rotina=None, experiencia_anterior=None),
        hoje=HOJE,
    )
    assert resultado["estilo_aprendizagem"]["predominante"] is None
    assert "preferencia_estudo" in resultado["lacunas"]


def test_nivel_geral_sobe_com_experiencia_anterior():
    com = analisar(perfil_completo(), hoje=HOJE)["nivel_conhecimento_geral"]
    sem = analisar(
        perfil_completo(experiencia_anterior="Nenhuma, primeira vez"), hoje=HOJE
    )["nivel_conhecimento_geral"]

    assert com["estimativa"] == "avancado"
    assert sem["estimativa"] == "iniciante"


def test_perfil_vazio_declara_lacunas_em_vez_de_assumir_valores():
    resultado = analisar({"dados_usuario": {}}, hoje=HOJE)

    assert resultado["confiabilidade"] == "baixa"
    assert resultado["completude"] == 0.0
    assert resultado["tempo_disponivel"]["calculavel"] is False
    assert resultado["carga_maxima_diaria"]["calculavel"] is False
    assert resultado["nivel_conhecimento_geral"]["estimativa"] is None
    assert "horas_por_dia" in resultado["lacunas"]
    assert "objetivo" in resultado["lacunas"]


def test_pontos_fortes_e_fracos_saem_das_disciplinas_declaradas():
    resultado = analisar(perfil_completo(), hoje=HOJE)

    assert any("Português" in p for p in resultado["pontos_fortes"])
    assert any("Estatística" in p for p in resultado["pontos_fracos"])


def test_campos_aceitos_tambem_aninhados_em_perfil():
    resultado = analisar(
        {"dados_usuario": {"perfil": {"horas_por_dia": 2, "dias_por_semana": 6}}},
        hoje=HOJE,
    )
    assert resultado["tempo_disponivel"]["horas_semanais_declaradas"] == 12.0


def test_poucos_dias_por_semana_viram_risco_de_descontinuidade():
    resultado = analisar(perfil_completo(dias_por_semana=2), hoje=HOJE)
    assert any(r["risco"] == "descontinuidade" for r in resultado["riscos"])


def test_necessidades_especiais_geram_alerta_de_adaptacao():
    resultado = analisar(
        perfil_completo(necessidades_especiais=["TDAH"]), hoje=HOJE
    )
    assert any(r["risco"] == "adaptacao_necessaria" for r in resultado["riscos"])
    assert resultado["necessidades_especiais"] == ["TDAH"]


@pytest.mark.asyncio
async def test_orquestrador_usa_a_implementacao_real_do_agente_01():
    resultado = await MasterOrchestrator().orquestrar(
        "Monte um cronograma para o concurso",
        dados_usuario=perfil_completo()["dados_usuario"],
    )
    saida = resultado.saidas["01"].conteudo

    assert saida["perfil_academico"]["nome"] == "Marcelo"
    assert saida["carga_maxima_diaria"]["calculavel"] is True
    assert saida["confiabilidade"] in ("alta", "media")
