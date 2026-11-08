"""Testa o GeradorClaude com o SDK de verdade, trocando só o transporte HTTP."""

import json
from datetime import date

import anthropic
import httpx2 as httpx
import pytest

from pauta.ia import ErroIA, GeradorClaude, data_do_post, pedido_plano
from pauta.modelos import Marca, Plano

PLANO_JSON = {
    "estrategia": "Educar e depois vender.",
    "posts": [
        {"dia": 0, "plataforma": "instagram", "formato": "reels", "pilar": "Dicas", "titulo": "T", "gancho": "G",
         "roteiro": "R", "legenda": "L", "hashtags": ["a"], "cta": "C"}
    ],
}


def _cliente(texto: str, stop_reason: str = "end_turn", capturar: list | None = None) -> anthropic.Anthropic:
    def responder(req: httpx.Request) -> httpx.Response:
        if capturar is not None:
            capturar.append(json.loads(req.content))
        return httpx.Response(200, json={
            "id": "msg_1", "type": "message", "role": "assistant", "model": "claude-opus-5-5",
            "content": [{"type": "text", "text": texto}], "stop_reason": stop_reason, "stop_sequence": None,
            "usage": {"input_tokens": 11, "output_tokens": 22},
        })
    return anthropic.Anthropic(api_key="teste", http_client=httpx.Client(transport=httpx.MockTransport(responder)))


def _marca_plano():
    marca = Marca(nome="Ana", nicho="fitness", publico_alvo="", tom_de_voz="", objetivo="", plataformas=["instagram"], pilares=["Dicas"])
    plano = Plano(data_inicio=date(2026, 11, 9), semanas=2, posts_por_semana=3, plataformas=["instagram"], foco="Black Friday")
    return marca, plano


def test_gerar_plano_envia_pedido_e_le_saida_estruturada():
    enviados = []
    gerador = GeradorClaude("claude-opus-5-5", client=_cliente(json.dumps(PLANO_JSON), capturar=enviados))
    resultado, uso = gerador.gerar_plano(*_marca_plano())
    assert resultado.estrategia == "Educar e depois vender." and resultado.posts[0].plataforma == "instagram"
    assert (uso.entrada, uso.saida) == (11, 22)
    corpo = enviados[0]
    assert corpo["model"] == "claude-opus-5-5"
    assert "6 posts" in corpo["messages"][0]["content"] and "Black Friday" in corpo["messages"][0]["content"]
    assert corpo["output_config"]["format"]["type"] == "json_schema"


def test_resposta_cortada_vira_erro_claro():
    gerador = GeradorClaude("m", client=_cliente("{", stop_reason="max_tokens"))
    with pytest.raises(ErroIA, match="incompleta"):
        gerador.gerar_plano(*_marca_plano())


def test_pedido_e_datas():
    _, plano = _marca_plano()
    texto = pedido_plano(plano)
    assert "2026-11-09 (segunda)" in texto and "de 0 a 13" in texto
    assert data_do_post(date(2026, 11, 9), 999, 14) == date(2026, 11, 22)
    assert data_do_post(date(2026, 11, 9), -3, 14) == date(2026, 11, 9)


def test_sem_chave_da_api_vira_erro_claro(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_AUTH_TOKEN", raising=False)
    with pytest.raises(ErroIA, match="ANTHROPIC_API_KEY"):
        GeradorClaude("m").gerar_plano(*_marca_plano())
