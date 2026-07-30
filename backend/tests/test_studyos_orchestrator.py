import pytest

from app.studyos.agents import AGENTES, AGENTES_OBRIGATORIOS, get_agent
from app.studyos.graph import (
    dependencias_efetivas,
    fechar_dependencias,
    ondas_de_execucao,
)
from app.studyos.intents import (
    WORKFLOWS,
    Classificacao,
    Intencao,
    classificar,
    selecionar_agentes,
)
from app.studyos.orchestrator import MasterOrchestrator, renderizar_markdown
from app.studyos.runner import RunnerDelegado

# --------------------------------------------------------------------------- #
# Catálogo e grafo
# --------------------------------------------------------------------------- #


def test_catalogo_tem_24_agentes():
    assert len(AGENTES) == 24
    assert sorted(AGENTES) == [f"{n:02d}" for n in range(1, 25)]


def test_dependencias_apontam_para_agentes_existentes():
    for spec in AGENTES.values():
        for dep in spec.depende_de:
            assert dep in AGENTES, f"{spec.codigo} depende de agente inexistente {dep}"


def test_grafo_completo_nao_tem_ciclo():
    ondas = ondas_de_execucao(set(AGENTES))
    assert sum(len(o) for o in ondas) == 24


def test_ondas_respeitam_dependencias():
    selecionados = set(AGENTES)
    concluidos: set[str] = set()
    for onda in ondas_de_execucao(selecionados):
        for codigo in onda:
            deps = dependencias_efetivas(get_agent(codigo), selecionados)
            assert concluidos.issuperset(deps), f"{codigo} rodaria sem {deps}"
        concluidos.update(onda)


def test_agentes_independentes_ficam_na_mesma_onda():
    # 08 e 11 dependem apenas do Lesson Generator: rodam em paralelo.
    ondas = ondas_de_execucao({"07", "08", "09", "10", "11"})
    onda_producao = next(o for o in ondas if "08" in o)

    assert {"08", "11"}.issubset(set(onda_producao))


def test_cadeia_de_producao_e_serializada_pelas_dependencias():
    # 09 consome os exemplos do 08, e 10 consome os exercícios do 09.
    ondas = ondas_de_execucao({"07", "08", "09", "10", "11"})
    onda_de = {
        codigo: indice for indice, onda in enumerate(ondas) for codigo in onda
    }

    assert onda_de["07"] < onda_de["08"] < onda_de["09"] < onda_de["10"]


def test_validators_e_sempre_a_ultima_onda():
    ondas = ondas_de_execucao(set(AGENTES))
    assert ondas[-1] == ["24"]


def test_fechar_dependencias_puxa_pre_requisitos():
    # Pedir só o Roadmap Builder traz curriculum, dependency mapper, etc.
    fechado = fechar_dependencias({"06"})
    assert {"01", "02", "03", "04", "05", "06"} == fechado


def test_ciclo_e_detectado():
    from dataclasses import replace

    from app.studyos import graph

    original = AGENTES["04"]
    AGENTES["04"] = replace(original, depende_de=("06",))
    try:
        with pytest.raises(graph.CicloDeDependencia):
            ondas_de_execucao({"04", "05", "06"})
    finally:
        AGENTES["04"] = original


# --------------------------------------------------------------------------- #
# Classificação de intenção
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "texto,esperado",
    [
        ("Monte um cronograma para o ENEM", Intencao.CRIAR_PLANO),
        ("Quero uma lista de exercícios de logaritmo", Intencao.GERAR_EXERCICIOS),
        ("Preciso revisar com flashcards", Intencao.REVISAR),
        ("Faz um simulado pra mim", Intencao.SIMULADO),
        ("Como está meu desempenho?", Intencao.ANALISE_DESEMPENHO),
        ("Estou desanimado e procrastinando", Intencao.MOTIVACAO),
        ("Explique derivadas", Intencao.ESTUDAR_TOPICO),
        ("Qual é o meu nível?", Intencao.DIAGNOSTICO),
    ],
)
def test_classificacao_de_intencao(texto, esperado):
    assert classificar(texto).intencao is esperado


def test_solicitacao_ambigua_cai_no_fluxo_completo():
    classificacao = classificar("me ajuda aí")
    assert classificacao.fallback is True
    assert classificacao.intencao is Intencao.COMPLETO


def test_agentes_obrigatorios_entram_em_qualquer_workflow():
    for intencao in Intencao:
        classificacao = Classificacao(
            intencao=intencao,
            workflow=WORKFLOWS[intencao],
            termos_encontrados=(),
            fallback=False,
        )
        selecionados = fechar_dependencias(selecionar_agentes(classificacao))
        assert set(AGENTES_OBRIGATORIOS).issubset(selecionados)


# --------------------------------------------------------------------------- #
# Orquestração
# --------------------------------------------------------------------------- #


async def test_orquestracao_produz_saida_canonica():
    resultado = await MasterOrchestrator().orquestrar("Monte um cronograma de estudos")
    payload = resultado.to_dict()

    assert set(payload) == {
        "agentes_executados",
        "ordem_execucao",
        "tarefas_realizadas",
        "resultado_consolidado",
    }
    assert payload["agentes_executados"]
    assert payload["ordem_execucao"][0]["onda"] == 1


async def test_validators_sempre_executa():
    resultado = await MasterOrchestrator().orquestrar("Explique matrizes")
    codigos = [e["codigo"] for e in resultado.agentes_executados]
    assert "24" in codigos
    assert "validacao" in resultado.resultado_consolidado


async def test_nenhum_agente_roda_antes_da_entrada_existir():
    ordem: list[str] = []

    async def registrar(spec, entradas):
        ordem.append(spec.codigo)
        return {"ok": True}

    resultado = await MasterOrchestrator(RunnerDelegado(registrar)).orquestrar(
        "Monte um cronograma completo", intencao=Intencao.COMPLETO
    )
    posicao = {codigo: i for i, codigo in enumerate(ordem)}
    selecionados = {e["codigo"] for e in resultado.agentes_executados}
    for codigo in posicao:
        for dep in dependencias_efetivas(get_agent(codigo), selecionados):
            if dep in posicao:
                assert posicao[dep] < posicao[codigo]


async def test_falha_de_agente_nao_derruba_o_fluxo_e_bloqueia_dependentes():
    async def falhar_no_curriculum(spec, entradas):
        if spec.codigo == "04":
            raise RuntimeError("fonte indisponível")
        return {"ok": True}

    resultado = await MasterOrchestrator(
        RunnerDelegado(falhar_no_curriculum)
    ).orquestrar("Monte um cronograma", intencao=Intencao.CRIAR_PLANO)

    status = {t["agente"].split()[0]: t["status"] for t in resultado.tarefas_realizadas}
    assert status["04"] == "falhou"
    assert status["05"] == "ignorado"  # dependia de 04
    assert status["24"] == "concluido"  # validação roda mesmo assim
    assert resultado.validacao.aprovado is False
    assert any("04" in p for p in resultado.validacao.problemas)


async def test_runner_delegado_alimenta_o_proximo_agente():
    vistos: dict[str, dict] = {}

    async def eco(spec, entradas):
        vistos[spec.codigo] = entradas
        return {"marca": f"conteudo-{spec.codigo}"}

    await MasterOrchestrator(RunnerDelegado(eco)).orquestrar(
        "Monte um cronograma", intencao=Intencao.CRIAR_PLANO
    )

    entradas_do_roadmap = vistos["06"]["saidas_anteriores"]
    assert entradas_do_roadmap["05"] == {"marca": "conteudo-05"}
    assert entradas_do_roadmap["01"] == {"marca": "conteudo-01"}


async def test_markdown_lista_agentes_e_ondas():
    resultado = await MasterOrchestrator().orquestrar("Preciso revisar com flashcards")
    texto = renderizar_markdown(resultado)
    assert "## Agentes executados" in texto
    assert "## Ordem de execução" in texto
    assert "## Tarefas realizadas" in texto
    assert "## Resultado consolidado" in texto
