"""Testes da tela web, com o mesmo cliente falso do Claude."""

from __future__ import annotations

import json
import time
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from triagem import ia, web

from test_triagem import RAIZ, FakeMessages

CURRICULOS = RAIZ / "exemplos" / "curriculos"
VAGAS = json.loads((RAIZ / "vagas.exemplo.json").read_text(encoding="utf-8"))


@pytest.fixture
def fake(monkeypatch):
    msgs = FakeMessages()
    monkeypatch.setattr(ia.anthropic, "AsyncAnthropic", lambda **kw: SimpleNamespace(beta=SimpleNamespace(messages=msgs)))
    return msgs


def cliente(tmp_path, **kw):
    return TestClient(web.criar_app(pasta_dados=tmp_path, **kw))


def enviar(c, arquivos=None, vagas=VAGAS):
    arquivos = arquivos or [(p.name, p.read_bytes()) for p in sorted(CURRICULOS.iterdir())]
    return c.post(
        "/api/triagens",
        data={"vagas": json.dumps(vagas), "top": "3"},
        files=[("curriculos", (n, b, "text/plain")) for n, b in arquivos],
    )


def esperar(c, id_, auth=None):
    for _ in range(200):
        t = c.get(f"/api/triagens/{id_}", auth=auth).json()
        if t["status"] in ("concluida", "erro"):
            return t
        time.sleep(0.02)
    raise AssertionError("triagem não terminou")


def test_pagina_abre(tmp_path):
    with cliente(tmp_path) as c:
        r = c.get("/")
        assert r.status_code == 200 and "Triagem de currículos" in r.text


def test_fluxo_web_completo(tmp_path, fake):
    with cliente(tmp_path) as c:
        r = enviar(c)
        assert r.status_code == 200, r.text
        t = esperar(c, r.json()["id"])
        assert t["status"] == "concluida"
        assert t["feitos"] == t["total"] == 5
        atendente = t["resultado"][0]
        assert atendente["titulo"] == "Atendente de loja"
        assert [m["nome"] for m in atendente["melhores"]] == ["Ana Souza", "Diego Rocha"]

        rel = c.get(f"/api/triagens/{t['id']}/relatorio")
        assert rel.status_code == 200 and "Quem entrevistar" in rel.text
        assert "default-src 'none'" in rel.headers["content-security-policy"]
        assert c.get(f"/api/triagens/{t['id']}/ranking.csv").status_code == 200

        # currículos originais apagados após a análise; relatório fica até expirar/apagar
        pasta = tmp_path / t["id"]
        assert not (pasta / "curriculos").exists() and (pasta / "saida" / "relatorio.html").exists()

        assert c.delete(f"/api/triagens/{t['id']}").status_code == 200
        assert not pasta.exists()
        assert c.get(f"/api/triagens/{t['id']}").status_code == 404


def test_vagas_invalidas(tmp_path, fake):
    with cliente(tmp_path) as c:
        assert enviar(c, vagas=[]).status_code == 400
        sem_req = [{"id": "a", "titulo": "A"}]
        r = enviar(c, vagas=sem_req)
        assert r.status_code == 400 and "requisito" in r.json()["detail"]
        assert list(tmp_path.iterdir()) == []


def test_formato_nao_suportado_e_nome_malicioso(tmp_path, fake):
    with cliente(tmp_path) as c:
        assert enviar(c, arquivos=[("foto.jpg", b"x")]).status_code == 400
        r = enviar(c, arquivos=[("../../fora.txt", b"Experiencia com atendimento " * 20), ("cv.txt", b"a" * 300),
                                ("cv.txt", b"b" * 300), ("virus.exe", b"x")])
        assert r.status_code == 200
        t = esperar(c, r.json()["id"])
        assert t["total"] == 3 and "ignorado" in t["mensagem"]
        assert not (tmp_path.parent / "fora.txt").exists()


def test_arquivo_grande_demais(tmp_path, fake, monkeypatch):
    monkeypatch.setattr(web, "MAX_BYTES_ARQUIVO", 100)
    with cliente(tmp_path) as c:
        r = enviar(c, arquivos=[("cv.txt", b"x" * 200)])
        assert r.status_code == 400 and "MB" in r.json()["detail"]
        assert list(tmp_path.iterdir()) == []


def test_senha(tmp_path, fake):
    with cliente(tmp_path, senha="segredo") as c:
        assert c.get("/").status_code == 401
        assert c.get("/", auth=("rh", "errada")).status_code == 401
        assert c.get("/", auth=("rh", "segredo")).status_code == 200
        assert enviar(c).status_code == 401


def test_chave_invalida_vira_mensagem(tmp_path, monkeypatch):
    import anthropic
    import httpx2

    class Msgs:
        async def parse(self, **kw):
            req = httpx2.Request("POST", "https://api.anthropic.com/v1/messages")
            raise anthropic.AuthenticationError("x", response=httpx2.Response(401, request=req), body=None)

    monkeypatch.setattr(ia.anthropic, "AsyncAnthropic", lambda **kw: SimpleNamespace(beta=SimpleNamespace(messages=Msgs())))
    with cliente(tmp_path) as c:
        t = esperar(c, enviar(c).json()["id"])
        assert t["status"] == "erro" and "chave" in t["mensagem"]


def test_expiracao(tmp_path, fake):
    with cliente(tmp_path, retencao_horas=0) as c:
        primeira = enviar(c).json()["id"]
        esperar(c, primeira)
        time.sleep(0.01)
        enviar(c)  # novo envio limpa as triagens expiradas
        assert c.get(f"/api/triagens/{primeira}").status_code == 404


def test_saude_sem_senha(tmp_path):
    with cliente(tmp_path, senha="segredo") as c:
        assert c.get("/api/saude").json() == {"ok": True}


def test_exigir_senha_bloqueia_sem_senha_configurada(tmp_path):
    with cliente(tmp_path, senha="", exigir_senha=True) as c:
        r = c.get("/")
        assert r.status_code == 503 and "TRIAGEM_SENHA" in r.json()["detail"]
        assert c.get("/api/saude").status_code == 200


def test_nenhum_analisado_vira_erro(tmp_path, monkeypatch):
    class Msgs:
        async def parse(self, **kw):
            raise ia.ErroIA("Connection error.")

    monkeypatch.setattr(ia.anthropic, "AsyncAnthropic", lambda **kw: SimpleNamespace(beta=SimpleNamespace(messages=Msgs())))
    with cliente(tmp_path) as c:
        t = esperar(c, enviar(c, arquivos=[("cv.txt", b"a" * 300)]).json()["id"])
        assert t["status"] == "erro" and "Connection error" in t["mensagem"]
