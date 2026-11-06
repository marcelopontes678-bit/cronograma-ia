"""Testes sem chamar a API: o cliente do Claude é substituído por um falso."""

from __future__ import annotations

import asyncio
import csv
import json
from pathlib import Path
from types import SimpleNamespace

import docx
import pytest

from triagem import cli, ia
from triagem.leitura import ler, listar_curriculos
from triagem.modelos import (
    AnaliseCurriculoIA,
    AvaliacaoVagaIA,
    CandidatoDestaque,
    Contato,
    ItemRequisito,
    ResumoVagaIA,
    Vaga,
    calcular_resultado,
)

RAIZ = Path(__file__).resolve().parent.parent
VAGAS = [Vaga.model_validate(v) for v in json.loads((RAIZ / "vagas.exemplo.json").read_text(encoding="utf-8"))]


def item(req, at):
    return ItemRequisito(requisito=req, atendido=at, evidencia="" if at == "nao" else "trecho")


def avaliacao(vaga: Vaga, obr: list[str], des: list[str]) -> AvaliacaoVagaIA:
    return AvaliacaoVagaIA(
        vaga_id=vaga.id,
        obrigatorios=[item(r, a) for r, a in zip(vaga.obrigatorios, obr)],
        desejaveis=[item(r, a) for r, a in zip(vaga.desejaveis, des)],
        pontos_fortes=["<b>forte</b>"],
        pontos_de_atencao=[],
    )


# ------------------------------------------------------------- nota/filtro


def test_nota_maxima():
    r = calcular_resultado(avaliacao(VAGAS[0], ["sim", "sim"], ["sim", "sim", "sim"]))
    assert r.nota == 100 and r.aprovado_filtro


def test_parcial_vale_meio_e_nao_elimina():
    r = calcular_resultado(avaliacao(VAGAS[0], ["sim", "parcial"], ["nao", "nao", "nao"]))
    assert r.aprovado_filtro
    assert r.nota == round(0.75 * 70)


def test_obrigatorio_nao_elimina():
    r = calcular_resultado(avaliacao(VAGAS[0], ["sim", "nao"], ["sim", "sim", "sim"]))
    assert not r.aprovado_filtro
    assert r.obrigatorios_faltando == ["Experiência com atendimento ao público"]


def test_vaga_sem_desejaveis_usa_peso_total():
    v = Vaga(id="x", titulo="X", obrigatorios=["a", "b"])
    r = calcular_resultado(avaliacao(v, ["sim", "parcial"], []))
    assert r.nota == 75


# ----------------------------------------------------------------- leitura


def test_leitura_docx_e_txt(tmp_path):
    d = docx.Document()
    d.add_paragraph("Fulano de Tal — experiência com atendimento")
    d.save(tmp_path / "cv.docx")
    (tmp_path / "cv.txt").write_text("texto", encoding="utf-8")
    (tmp_path / "foto.jpg").write_bytes(b"x")
    arquivos = listar_curriculos(tmp_path)
    assert [a.name for a in arquivos] == ["cv.docx", "cv.txt"]
    assert "atendimento" in ler(tmp_path / "cv.docx").texto


# ------------------------------------------------------------- cliente falso

# Respostas "da IA" por arquivo: (obrigatórios, desejáveis) para cada vaga.
RESPOSTAS = {
    "ana_souza.txt": {"atendente": (["sim", "sim"], ["sim", "sim", "parcial"]),
                      "aux-financeiro": (["nao", "parcial"], ["nao", "nao", "nao"])},
    "bruno_lima.txt": {"atendente": (["sim", "nao"], ["nao", "nao", "sim"]),
                       "aux-financeiro": (["sim", "sim"], ["parcial", "sim", "sim"])},
    "carla_mendes.txt": {"atendente": (["sim", "nao"], ["nao", "nao", "parcial"]),
                         "aux-financeiro": (["parcial", "parcial"], ["nao", "nao", "parcial"])},
    "diego_rocha.txt": {"atendente": (["sim", "sim"], ["parcial", "nao", "nao"]),
                        "aux-financeiro": (["nao", "nao"], ["nao", "nao", "nao"])},
}


def vagas_do_prompt(system) -> list[Vaga]:
    """Lê as vagas do system prompt, como a IA real faria (os ids podem não ser os do exemplo)."""
    texto = system[0]["text"]
    return [Vaga.model_validate(v) for v in json.loads(texto.split("VAGAS:\n", 1)[1])]


class FakeMessages:
    def __init__(self, recusar=()):
        self.chamadas = []
        self.recusar = set(recusar)

    async def parse(self, **kw):
        self.chamadas.append(kw)
        assert kw["fallbacks"] == "default" and kw["betas"] == [ia.FALLBACK_BETA]
        texto = kw["messages"][0]["content"][-1]["text"]
        if kw["output_format"] is ResumoVagaIA:
            dados = json.loads(texto.split("CANDIDATOS (ordem do ranking):\n", 1)[1])
            saida = ResumoVagaIA(
                visao_geral="Comece por quem tem nota maior.",
                candidatos=[CandidatoDestaque(arquivo=d["arquivo"], resumo="r", por_que_entrevistar="p",
                                              riscos="x", perguntas_entrevista=["q1", "q2", "q3"]) for d in dados],
            )
            return SimpleNamespace(stop_reason="end_turn", parsed_output=saida)

        arquivo = texto.split("\n", 1)[0].removeprefix("Arquivo: ").strip()
        if arquivo in self.recusar:
            return SimpleNamespace(stop_reason="refusal", parsed_output=None)
        respostas = RESPOSTAS.get(arquivo)
        saida = AnaliseCurriculoIA(
            e_curriculo=respostas is not None,
            contato=Contato(nome=arquivo.split(".")[0].replace("_", " ").title(), email="", telefone="", cidade=""),
            anos_experiencia=3,
            resumo_perfil="perfil <script>x</script>",
            avaliacoes=[
                avaliacao(v, *(respostas or {}).get(VAGAS[i].id, (["nao"] * 3, ["nao"] * 3)))
                for i, v in enumerate(vagas_do_prompt(kw["system"]))
            ],
        )
        return SimpleNamespace(stop_reason="end_turn", parsed_output=saida)


@pytest.fixture
def fake(monkeypatch):
    msgs = FakeMessages()
    cliente = SimpleNamespace(beta=SimpleNamespace(messages=msgs))
    monkeypatch.setattr(ia.anthropic, "AsyncAnthropic", lambda **kw: cliente)
    return msgs


def rodar(tmp_path, *extra):
    return cli.main(["--vagas", str(RAIZ / "vagas.exemplo.json"),
                     "--curriculos", str(RAIZ / "exemplos" / "curriculos"),
                     "--saida", str(tmp_path), "--top", "3", *extra])


def test_fluxo_completo(tmp_path, fake):
    assert rodar(tmp_path) == 0
    # 5 arquivos + 2 resumos (uma por vaga)
    assert len(fake.chamadas) == 7

    with (tmp_path / "ranking.csv").open(encoding="utf-8-sig") as f:
        linhas = list(csv.DictReader(f, delimiter=";"))
    atendente = [l for l in linhas if l["vaga"] == "Atendente de loja"]
    assert [l["arquivo"] for l in atendente if l["status"] == "aprovado"] == ["ana_souza.txt", "diego_rocha.txt"]
    assert {l["arquivo"] for l in atendente if l["status"] == "filtrado"} == {"bruno_lima.txt", "carla_mendes.txt"}
    # "lista de compras" não é currículo e não entra no ranking
    assert not any(l["arquivo"] == "lista_compras.txt" for l in linhas)

    html = (tmp_path / "relatorio.html").read_text(encoding="utf-8")
    assert "Quem entrevistar" in html
    assert "<script>x</script>" not in html and "&lt;script&gt;" in html  # conteúdo escapado
    assert "lista_compras.txt" in html  # listado para revisão humana


def test_resumo_nao_envia_contato(tmp_path, fake):
    rodar(tmp_path)
    resumos = [c for c in fake.chamadas if c["output_format"] is ResumoVagaIA]
    for c in resumos:
        texto = c["messages"][0]["content"][-1]["text"]
        assert "contato" not in texto and "email" not in texto


def test_cache_evita_nova_chamada(tmp_path, fake):
    rodar(tmp_path)
    fake.chamadas.clear()
    rodar(tmp_path)
    assert all(c["output_format"] is ResumoVagaIA for c in fake.chamadas)


def test_recusa_vira_erro_sem_derrubar_o_resto(tmp_path, fake):
    fake.recusar = {"bruno_lima.txt"}
    assert rodar(tmp_path, "--sem-cache") == 0
    html = (tmp_path / "relatorio.html").read_text(encoding="utf-8")
    assert "recusou" in html
    with (tmp_path / "ranking.csv").open(encoding="utf-8-sig") as f:
        assert not any(l["arquivo"] == "bruno_lima.txt" for l in csv.DictReader(f, delimiter=";"))


def test_vaga_nao_avaliada_e_sinalizada():
    triador = ia.Triador(VAGAS, client=SimpleNamespace())
    analise = AnaliseCurriculoIA(
        e_curriculo=True, contato=Contato(nome="", email="", telefone="", cidade=""),
        anos_experiencia=1, resumo_perfil="", avaliacoes=[avaliacao(VAGAS[0], ["sim", "sim"], [])],
    )
    from triagem.modelos import Candidato
    c = triador._montar(Candidato(arquivo="a.txt"), analise)
    assert "aux-financeiro" in c.erro and "atendente" in c.resultados


def test_chave_invalida_para_tudo(tmp_path, monkeypatch):
    import httpx2
    import anthropic

    class Msgs:
        async def parse(self, **kw):
            req = httpx2.Request("POST", "https://api.anthropic.com/v1/messages")
            raise anthropic.AuthenticationError("invalid x-api-key", response=httpx2.Response(401, request=req), body=None)

    monkeypatch.setattr(ia.anthropic, "AsyncAnthropic", lambda **kw: SimpleNamespace(beta=SimpleNamespace(messages=Msgs())))
    assert rodar(tmp_path, "--sem-cache") == 2
