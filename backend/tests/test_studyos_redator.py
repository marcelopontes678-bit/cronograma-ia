"""Redator real (app.studyos.redator) — conexão dos agentes 07-11, 13 e 16.

Duas frentes: (1) unidade — schema, `_por_numero`, `_slots_sem_banco`,
configuração de ambiente, chamada HTTP com retry, tudo sem rede real; (2)
integração — o agente 07 de ponta a ponta com uma resposta HTTP simulada,
provando que o resultado do redator passa pela mesma validação de `montar()`
que sempre existiu. A regra que atravessa os dois níveis: sem chave de API
ou com qualquer falha de rede, o comportamento é idêntico a "nenhum redator
conectado" — nunca conteúdo inventado.
"""

from __future__ import annotations

import asyncio
import time
from datetime import date

import httpx
import pytest

from app.studyos import redator as R
from app.studyos.agentes.aula import gerar as gerar_aula
from app.studyos.agentes.conhecimento import analisar as analisar_conhecimento
from app.studyos.agentes.curriculo import construir as construir_curriculo
from app.studyos.agentes.dependencias import mapear
from app.studyos.agentes.objetivo import analisar as analisar_objetivo
from app.studyos.agentes.perfil import analisar as analisar_perfil
from app.studyos.agentes.roadmap import construir as construir_roadmap
from app.studyos.agents import AGENTES
from app.studyos.runner import RunnerEstrutural

HOJE = date(2026, 1, 5)

EDITAL = {
    "Estatística": {"questoes": 10, "topicos": ["Conjuntos", "Probabilidade"]},
}


def cadeia_aula(dados=None):
    """Roda 01-06 de verdade e devolve as entradas prontas para o agente 07."""
    base = {
        "objetivo": "Passar no concurso fiscal",
        "edital": EDITAL,
        "pre_requisitos": {},
        "escolaridade": "Superior completo",
        "profissao": "Analista",
        "rotina": "Estudo em casa",
        "horas_por_dia": 4,
        "dias_por_semana": 5,
        "idade": 30,
        "experiencia_anterior": "nenhuma",
        "preferencia_estudo": "videoaula e mapa mental",
        "data_prova": "2026-06-01",
        "conteudo_solicitado": "Conjuntos",
        **(dados or {}),
    }
    m1 = analisar_perfil({"dados_usuario": base}, hoje=HOJE)
    m2 = analisar_objetivo({"dados_usuario": base, "solicitacao": ""}, hoje=HOJE)
    m3 = analisar_conhecimento(
        {"dados_usuario": base, "saidas_anteriores": {"01": m1, "02": m2}}, hoje=HOJE
    )
    m4 = construir_curriculo({"dados_usuario": base, "saidas_anteriores": {"02": m2, "03": m3}})
    m5 = mapear({"dados_usuario": base, "saidas_anteriores": {"03": m3, "04": m4}})
    m6 = construir_roadmap(
        {"dados_usuario": base, "saidas_anteriores": {"01": m1, "02": m2, "05": m5}}, hoje=HOJE
    )
    return {
        "solicitacao": "",
        "dados_usuario": base,
        "saidas_anteriores": {"01": m1, "03": m3, "04": m4, "05": m5, "06": m6},
    }


# --------------------------------------------------------------------------- #
# Configuração de ambiente
# --------------------------------------------------------------------------- #


def test_sem_chave_no_ambiente_nao_ha_configuracao():
    assert R.configuracao_do_ambiente() is None


def test_com_chave_no_ambiente_configuracao_usa_modelo_padrao(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-teste")
    monkeypatch.delenv("STUDYOS_REDATOR_MODELO", raising=False)
    config = R.configuracao_do_ambiente()
    assert config is not None
    assert config.api_key == "sk-teste"
    assert config.modelo == R.MODELO_PADRAO


def test_modelo_customizado_por_variavel_de_ambiente(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-teste")
    monkeypatch.setenv("STUDYOS_REDATOR_MODELO", "claude-opus-5")
    config = R.configuracao_do_ambiente()
    assert config.modelo == "claude-opus-5"


def test_redatores_reais_sem_chave_devolve_vazio(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert R.redatores_reais() == {}


def test_redatores_reais_com_chave_cobre_os_sete_agentes():
    config = R.ConfiguracaoDoRedator(api_key="sk-teste")
    redatores = R.redatores_reais(config)
    assert set(redatores) == {"07", "08", "09", "10", "11", "13", "16"}
    assert all(callable(f) for f in redatores.values())


# --------------------------------------------------------------------------- #
# Chamada HTTP — sucesso, retry, falha esgotada, resposta sem ferramenta
# --------------------------------------------------------------------------- #


class _FakeHttpx:
    """Substitui `redator.httpx` só dentro do módulo — não toca no httpx real."""

    def __init__(self, respostas):
        self._respostas = list(respostas)
        self.chamadas: list[dict] = []
        self.HTTPError = httpx.HTTPError
        self.HTTPStatusError = httpx.HTTPStatusError

    def Client(self, *, timeout):  # noqa: N802 - espelha a API do httpx
        return self

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def post(self, url, *, headers, json):
        self.chamadas.append(json)
        if not self._respostas:
            raise AssertionError("mais chamadas do que respostas configuradas")
        resposta = self._respostas.pop(0)
        if isinstance(resposta, BaseException):
            raise resposta
        return resposta


class _FakeResponse:
    def __init__(self, status_code, corpo):
        self.status_code = status_code
        self._corpo = corpo
        self.request = "request-fake"

    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx.HTTPStatusError("erro", request=self.request, response=self)

    def json(self):
        return self._corpo


def _corpo_tool_use(nome_da_ferramenta: str, entrada: dict) -> dict:
    return {
        "content": [{"type": "tool_use", "name": nome_da_ferramenta, "input": entrada}],
        "stop_reason": "tool_use",
    }


def _config():
    return R.ConfiguracaoDoRedator(api_key="sk-teste", tentativas=2)


def test_chamada_bem_sucedida_devolve_o_input_da_ferramenta(monkeypatch):
    fake = _FakeHttpx([_FakeResponse(200, _corpo_tool_use("ferramenta", {"campo": "valor"}))])
    monkeypatch.setattr(R, "httpx", fake)

    resultado = R._chamar_ferramenta(_config(), "sistema", "usuario", "ferramenta", {"type": "object"})

    assert resultado == {"campo": "valor"}
    assert len(fake.chamadas) == 1
    assert fake.chamadas[0]["tool_choice"] == {"type": "tool", "name": "ferramenta"}


def test_falha_transitoria_tenta_de_novo_e_depois_funciona(monkeypatch):
    fake = _FakeHttpx(
        [
            _FakeResponse(503, {}),
            _FakeResponse(200, _corpo_tool_use("ferramenta", {"ok": True})),
        ]
    )
    monkeypatch.setattr(R, "httpx", fake)
    monkeypatch.setattr(R.time, "sleep", lambda _s: None)

    resultado = R._chamar_ferramenta(_config(), "sistema", "usuario", "ferramenta", {"type": "object"})

    assert resultado == {"ok": True}
    assert len(fake.chamadas) == 2


def test_falha_esgotada_devolve_none_nunca_levanta(monkeypatch):
    fake = _FakeHttpx([_FakeResponse(500, {}), _FakeResponse(500, {})])
    monkeypatch.setattr(R, "httpx", fake)
    monkeypatch.setattr(R.time, "sleep", lambda _s: None)

    resultado = R._chamar_ferramenta(_config(), "sistema", "usuario", "ferramenta", {"type": "object"})

    assert resultado is None


def test_resposta_sem_bloco_tool_use_e_tratada_como_falha(monkeypatch):
    fake = _FakeHttpx(
        [
            _FakeResponse(200, {"content": [{"type": "text", "text": "não uso ferramenta"}]}),
            _FakeResponse(200, {"content": [{"type": "text", "text": "de novo não"}]}),
        ]
    )
    monkeypatch.setattr(R, "httpx", fake)
    monkeypatch.setattr(R.time, "sleep", lambda _s: None)

    resultado = R._chamar_ferramenta(_config(), "sistema", "usuario", "ferramenta", {"type": "object"})

    assert resultado is None


def test_erro_4xx_nao_transitorio_nao_tenta_de_novo(monkeypatch):
    fake = _FakeHttpx([_FakeResponse(401, {})])
    monkeypatch.setattr(R, "httpx", fake)

    resultado = R._chamar_ferramenta(_config(), "sistema", "usuario", "ferramenta", {"type": "object"})

    assert resultado is None
    assert len(fake.chamadas) == 1


# --------------------------------------------------------------------------- #
# `_por_numero` — array de slots numerados de volta para dicionário por número
# --------------------------------------------------------------------------- #


def test_por_numero_converte_lista_em_dicionario_por_numero():
    resultado = {
        "questoes": [
            {"numero": 2, "enunciado": "b"},
            {"numero": 1, "enunciado": "a"},
        ]
    }
    convertido = R._por_numero(resultado, "questoes")
    assert convertido == {1: {"enunciado": "a"}, 2: {"enunciado": "b"}}


def test_por_numero_ignora_item_sem_numero_inteiro():
    resultado = {"questoes": [{"enunciado": "sem numero"}, {"numero": "x", "enunciado": "invalido"}]}
    assert R._por_numero(resultado, "questoes") == {}


def test_por_numero_lista_ausente_devolve_vazio():
    assert R._por_numero({}, "questoes") == {}


# --------------------------------------------------------------------------- #
# `_slots_sem_banco` — reaproveitar o banco do agente 09 em vez de regerar
# --------------------------------------------------------------------------- #


def _slot(numero, topico="Conjuntos", dificuldade="medio"):
    return {"numero": numero, "topico": topico, "dificuldade": dificuldade}


def test_slots_sem_banco_exclui_o_que_o_banco_ja_cobre():
    briefing = {
        "slots": [_slot(1), _slot(2)],
        "banco_disponivel": {"conjuntos|medio": [{"enunciado": "questão do banco"}]},
    }
    pendentes = R._slots_sem_banco(briefing)
    assert [s["numero"] for s in pendentes] == [2]


def test_slots_sem_banco_nao_reusa_a_mesma_questao_duas_vezes():
    briefing = {
        "slots": [_slot(1), _slot(2), _slot(3)],
        "banco_disponivel": {"conjuntos|medio": [{"enunciado": "única questão do banco"}]},
    }
    pendentes = R._slots_sem_banco(briefing)
    assert [s["numero"] for s in pendentes] == [2, 3]


def test_slots_sem_banco_vazio_pede_tudo():
    briefing = {"slots": [_slot(1), _slot(2)], "banco_disponivel": {}}
    assert len(R._slots_sem_banco(briefing)) == 2


def test_redator_simulado_pula_chamada_quando_banco_cobre_tudo(monkeypatch):
    chamado = []
    monkeypatch.setattr(R, "_chamar_ferramenta", lambda *a, **k: chamado.append(1))
    briefing = {
        "slots": [_slot(1)],
        "banco_disponivel": {"conjuntos|medio": [{"enunciado": "questão do banco"}]},
        "objetivo": "x", "banca": {}, "correcao": {}, "proibicoes": [],
    }
    resultado = R.redator_simulado(briefing, _config())
    assert resultado == {}
    assert chamado == []


# --------------------------------------------------------------------------- #
# Construtores de ferramenta — schema espelha exatamente o que `montar()` valida
# --------------------------------------------------------------------------- #


def test_ferramenta_aula_uma_propriedade_obrigatoria_por_secao():
    briefing = {
        "secoes": [
            {"chave": "desenvolvimento", "etapa": "Desenvolvimento", "instrucao": "explique"},
            {"chave": "pontos_chave", "etapa": "Pontos-chave", "instrucao": "liste"},
        ]
    }
    schema = R._ferramenta_aula(briefing)
    assert schema["required"] == ["desenvolvimento", "pontos_chave"]
    assert schema["properties"]["pontos_chave"]["type"] == "array"
    assert schema["properties"]["desenvolvimento"]["type"] == "string"


def test_ferramenta_exemplos_so_inclui_slots_aplicaveis():
    briefing = {
        "slots": [
            {"chave": "exemplo_introdutorio", "nivel": "basico", "instrucao": "x", "aplicavel": True},
            {"chave": "contraexemplo", "nivel": "avancado", "instrucao": "y", "aplicavel": False},
        ]
    }
    schema = R._ferramenta_exemplos(briefing)
    assert schema["required"] == ["exemplo_introdutorio"]
    assert "contraexemplo" not in schema["properties"]


def test_ferramenta_exercicios_schema_fixo_com_array_de_questoes():
    schema = R._ferramenta_exercicios()
    assert schema["required"] == ["questoes"]
    item = schema["properties"]["questoes"]["items"]
    assert set(item["required"]) == {"numero", "enunciado", "resposta", "explicacao"}


def test_ferramenta_flashcards_schema_fixo_com_array_de_cartoes():
    schema = R._ferramenta_flashcards()
    item = schema["properties"]["cartoes"]["items"]
    assert set(item["required"]) == {"numero", "pergunta", "resposta"}


def test_ferramenta_resumos_so_inclui_secoes_aplicaveis_e_cita_limite():
    briefing = {
        "secoes": [
            {"chave": "resumo_1min", "instrucao": "essencial", "aplicavel": True, "limite_palavras": 60},
            {"chave": "resumo_formulas", "instrucao": "formulas", "aplicavel": False, "limite_palavras": None},
        ],
        "conceitos_chave": ["conjunto", "intersecção"],
    }
    schema = R._ferramenta_resumos(briefing)
    assert schema["required"] == ["resumo_1min"]
    assert "60 palavras" in schema["properties"]["resumo_1min"]["description"]


def test_ferramenta_resumos_completo_exige_termos_literais():
    briefing = {
        "secoes": [
            {"chave": "resumo_completo", "instrucao": "sintese", "aplicavel": True, "limite_palavras": None},
        ],
        "conceitos_chave": ["conjunto", "intersecção"],
    }
    schema = R._ferramenta_resumos(briefing)
    descricao = schema["properties"]["resumo_completo"]["description"]
    assert "conjunto" in descricao and "intersecção" in descricao


def test_ferramenta_adaptativo_so_inclui_slots_aplicaveis():
    briefing = {
        "slots": [
            {"chave": "analogias", "instrucao": "x", "aplicavel": True, "quantidade": 2},
            {"chave": "exemplos_adicionais", "instrucao": "y", "aplicavel": False, "quantidade": None},
        ]
    }
    schema = R._ferramenta_adaptativo(briefing)
    assert schema["required"] == ["analogias"]
    assert "2" in schema["properties"]["analogias"]["description"]


def test_ferramenta_simulado_schema_fixo_com_array_de_questoes():
    schema = R._ferramenta_simulado()
    item = schema["properties"]["questoes"]["items"]
    assert set(item["required"]) == {"numero", "enunciado", "resposta"}


# --------------------------------------------------------------------------- #
# Integração: agente 07 de ponta a ponta com HTTP simulado
# --------------------------------------------------------------------------- #


def test_redator_aula_conectado_produz_aula_completa(monkeypatch):
    entradas = cadeia_aula()

    def resposta_falsa(config, sistema, usuario, nome_da_ferramenta, schema):
        assert nome_da_ferramenta == "escrever_aula"
        return {chave: (["A", "B"] if chave == "pontos_chave" else f"texto de {chave}") for chave in schema["properties"]}

    monkeypatch.setattr(R, "_chamar_ferramenta", resposta_falsa)
    config = R.ConfiguracaoDoRedator(api_key="sk-teste")
    redator = R.redatores_reais(config)["07"]

    aula = gerar_aula(entradas, redator=redator)

    assert aula["gerada"] is True
    assert aula["status"] == "gerada"


def test_redator_aula_com_falha_de_rede_cai_para_pendente_de_redacao(monkeypatch):
    entradas = cadeia_aula()
    monkeypatch.setattr(R, "_chamar_ferramenta", lambda *a, **k: None)
    config = R.ConfiguracaoDoRedator(api_key="sk-teste")
    redator = R.redatores_reais(config)["07"]

    aula = gerar_aula(entradas, redator=redator)

    assert aula["gerada"] is False
    assert aula["status"] == "pendente_de_redacao"


# --------------------------------------------------------------------------- #
# `runner.py` não pode travar o event loop com um redator que faz I/O
# --------------------------------------------------------------------------- #


async def test_runner_nao_bloqueia_o_event_loop_com_redator_lento(monkeypatch):
    ordem: list[str] = []

    def redator_lento(briefing):
        time.sleep(0.2)
        ordem.append("redator")
        return {
            secao["chave"]: (["A", "B"] if secao["chave"] == "pontos_chave" else "texto")
            for secao in briefing["secoes"]
        }

    async def tique():
        await asyncio.sleep(0.02)
        ordem.append("tique")

    runner = RunnerEstrutural(redatores={"07": redator_lento})
    entradas = cadeia_aula()

    await asyncio.gather(runner.executar(AGENTES["07"], entradas), tique())

    assert ordem == ["tique", "redator"]
