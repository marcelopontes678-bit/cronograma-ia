"""Testes da API do StudyOS.

O router é montado isoladamente: o orquestrador não toca banco nem autenticação,
então os testes não dependem de `app.main` (que exige DATABASE_URL).
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.routers import studyos

PREFIX = "/api/v1"


@pytest.fixture(scope="module")
def client():
    app = FastAPI()
    app.include_router(studyos.router, prefix=PREFIX)
    with TestClient(app) as c:
        yield c


def test_catalogo_de_agentes(client):
    resposta = client.get(f"{PREFIX}/studyos/agentes")
    assert resposta.status_code == 200

    agentes = resposta.json()
    assert len(agentes) == 24
    assert agentes[-1]["codigo"] == "24"
    assert agentes[-1]["obrigatorio"] is True


def test_plano_nao_executa_agentes(client):
    resposta = client.post(
        f"{PREFIX}/studyos/plano",
        json={"solicitacao": "Monte um cronograma para o ENEM"},
    )
    assert resposta.status_code == 200

    corpo = resposta.json()
    assert corpo["intencao"] == "criar_plano"
    assert corpo["intencao_por_fallback"] is False
    assert corpo["ordem_execucao"][-1]["agentes"][0]["codigo"] == "24"


def test_orquestrar_devolve_saida_canonica(client):
    resposta = client.post(
        f"{PREFIX}/studyos/orquestrar",
        json={
            "solicitacao": "Monte um cronograma para o concurso",
            "dados_usuario": {
                "escolaridade": "Superior completo",
                "objetivo": "Passar no concurso",
                "horas_por_dia": 3,
                "dias_por_semana": 5,
                "rotina": "Trabalho durante o dia",
                "preferencia_estudo": "videoaula",
                "experiencia_anterior": "nenhuma",
                "disciplinas_favoritas": "Português",
                "disciplinas_dificuldade": "Estatística",
                "idade": 30,
                "profissao": "Analista",
            },
        },
    )
    assert resposta.status_code == 200

    corpo = resposta.json()
    codigos = [a["codigo"] for a in corpo["agentes_executados"]]
    assert "01" in codigos and "24" in codigos
    assert corpo["resultado_consolidado"]["validacao"]["aprovado"] is True
    assert corpo["resposta_markdown"] is None


def test_orquestrar_em_markdown(client):
    resposta = client.post(
        f"{PREFIX}/studyos/orquestrar",
        json={"solicitacao": "Preciso revisar com flashcards", "formato": "markdown"},
    )
    assert resposta.status_code == 200
    assert "## Ordem de execução" in resposta.json()["resposta_markdown"]


def test_formato_invalido_e_rejeitado(client):
    resposta = client.post(
        f"{PREFIX}/studyos/orquestrar",
        json={"solicitacao": "Qualquer coisa", "formato": "pdf"},
    )
    assert resposta.status_code == 422


def test_intencao_forcada(client):
    resposta = client.post(
        f"{PREFIX}/studyos/plano",
        json={"solicitacao": "qualquer texto", "intencao": "simulado"},
    )
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["intencao"] == "simulado"
    assert "16" in corpo["agentes_selecionados"]
