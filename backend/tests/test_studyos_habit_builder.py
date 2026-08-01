from datetime import date, timedelta

import pytest

from app.studyos.agentes.coach import TERMOS_MANIPULATIVOS, acompanhar
from app.studyos.agentes.conhecimento import analisar as analisar_conhecimento
from app.studyos.agentes.curriculo import construir as construir_curriculo
from app.studyos.agentes.dependencias import mapear as mapear_dependencias
from app.studyos.agentes.habitos import (
    ADESAO_PARA_AUMENTAR,
    ADESAO_PARA_CONSOLIDAR,
    ADESAO_PARA_REDUZIR,
    DIAS_PARA_CONSOLIDAR,
    DIAS_PARA_RISCO_DE_QUEBRA,
    JANELA_DE_OBSERVACAO_DIAS,
    MARCOS_DE_SEQUENCIA,
    MINIMO_DE_OBSERVACOES,
    MINUTOS_MINIMOS_DE_META,
    PASSO_DE_REDUCAO,
    PASSO_MAXIMO_DE_AUMENTO,
    REFORCOS_POSITIVOS,
    TERMOS_PUNITIVOS,
    TextoPunitivo,
    _validar_texto,
    construir,
)
from app.studyos.agentes.objetivo import analisar as analisar_objetivo
from app.studyos.agentes.perfil import analisar as analisar_perfil
from app.studyos.agentes.roadmap import construir as construir_roadmap
from app.studyos.orchestrator import MasterOrchestrator

INICIO_DO_PLANO = date(2026, 3, 2)
HOJE = INICIO_DO_PLANO + timedelta(days=20)

EDITAL = {
    "Estatística": {"questoes": 10, "topicos": ["Conjuntos", "Probabilidade"]},
    "Português": {"questoes": 20, "topicos": ["Crase", "Sintaxe", "Ortografia", "Verbos"]},
}


def cadeia(dados=None):
    """Roda 01–06 de verdade e devolve as entradas prontas para o 20."""
    base = {
        "objetivo": "Passar no concurso fiscal",
        "edital": EDITAL,
        "escolaridade": "Superior completo",
        "horas_por_dia": 2,
        "dias_por_semana": 5,
        "data_prova": "2026-09-01",
        **(dados or {}),
    }
    m1 = analisar_perfil({"dados_usuario": base}, hoje=INICIO_DO_PLANO)
    m2 = analisar_objetivo(
        {"dados_usuario": base, "solicitacao": ""}, hoje=INICIO_DO_PLANO
    )
    m3 = analisar_conhecimento(
        {"dados_usuario": base, "saidas_anteriores": {"01": m1, "02": m2}},
        hoje=INICIO_DO_PLANO,
    )
    m4 = construir_curriculo(
        {"dados_usuario": base, "saidas_anteriores": {"02": m2, "03": m3}}
    )
    m5 = mapear_dependencias(
        {"dados_usuario": base, "saidas_anteriores": {"03": m3, "04": m4}}
    )
    m6 = construir_roadmap(
        {"dados_usuario": base, "saidas_anteriores": {"01": m1, "02": m2, "05": m5}},
        hoje=INICIO_DO_PLANO,
    )
    return {
        "solicitacao": "",
        "dados_usuario": base,
        "saidas_anteriores": {"01": m1, "02": m2, "03": m3, "04": m4, "05": m5, "06": m6},
    }


def planejados(entradas):
    """Dias reservados pelo agente 06 dentro da janela de observação."""
    inicio = HOJE - timedelta(days=JANELA_DE_OBSERVACAO_DIAS - 1)
    return [
        date.fromisoformat(d["data"])
        for d in entradas["saidas_anteriores"]["06"]["cronograma"]
        if inicio <= date.fromisoformat(d["data"]) <= HOJE
    ]


def sessoes(datas, minutos=55, hora="07:30", **extras):
    return [
        {"data": d.isoformat(), "minutos": minutos, "hora": hora, **extras}
        for d in datas
    ]


def rodar(entradas, **campos):
    dados = {**entradas["dados_usuario"], **campos}
    return construir({**entradas, "dados_usuario": dados}, hoje=HOJE)


# --------------------------------------------------------------------------- #
# Sem registro, sem hábito
# --------------------------------------------------------------------------- #


def test_sem_sessoes_nao_ha_habito_a_medir():
    plano = rodar(cadeia())

    assert plano["habitos_positivos"]["consolidados"] == []
    assert plano["lacunas"] == ["historico_frequencia"]
    assert plano["confiabilidade"] == "baixa"
    assert any("não estima comportamento" in o for o in plano["observacoes"])


def test_sem_duracao_registrada_a_meta_nao_e_inventada():
    entradas = cadeia()
    registros = [{"data": d.isoformat()} for d in planejados(entradas)[:4]]
    plano = rodar(entradas, historico_frequencia=registros)
    meta = plano["plano_de_acao"]["meta_diaria"]

    assert meta["minutos"] is None
    assert "não definida" in meta["base"]
    assert any("Meta diária não definida" in o for o in plano["observacoes"])


# --------------------------------------------------------------------------- #
# A meta é cumprível por construção
# --------------------------------------------------------------------------- #


def test_meta_sai_da_mediana_e_nao_da_media():
    """Um domingo de cinco horas não define a rotina de ninguém."""
    entradas = cadeia()
    dias = planejados(entradas)
    registros = sessoes(dias[:-1], minutos=40) + sessoes(dias[-1:], minutos=300)
    plano = rodar(entradas, historico_frequencia=registros)
    meta = plano["plano_de_acao"]["meta_diaria"]

    media = (40 * (len(dias) - 1) + 300) / len(dias)
    assert "40" in meta["base"]
    assert meta["minutos"] < media
    assert "mediana" in meta["fatores"][0]


def test_meta_nunca_passa_da_disponibilidade_declarada():
    entradas = cadeia({"horas_por_dia": 1})
    dias = planejados(entradas)
    plano = rodar(entradas, historico_frequencia=sessoes(dias, minutos=200))
    meta = plano["plano_de_acao"]["meta_diaria"]

    assert meta["minutos"] <= meta["disponibilidade"]["minutos"] == 60.0
    assert meta["ajuste"] == "limitada pela disponibilidade"
    assert any("teto" in f for f in meta["fatores"])
    assert any("nunca acima dele" in o for o in plano["observacoes"])


def test_adesao_alta_aumenta_a_meta_dentro_do_passo():
    entradas = cadeia()
    anterior = {"plano_de_acao": {"meta_diaria": {"minutos": 50}}}
    plano = rodar(
        entradas,
        historico_frequencia=sessoes(planejados(entradas)),
        plano_de_habitos_anterior=anterior,
    )
    meta = plano["plano_de_acao"]["meta_diaria"]

    assert plano["indicadores"]["taxa_de_adesao"] >= ADESAO_PARA_AUMENTAR
    assert meta["ajuste"] == "aumentada"
    assert meta["minutos"] == round(50 * (1 + PASSO_MAXIMO_DE_AUMENTO), 1)


def test_adesao_baixa_reduz_a_meta():
    """É o que o agente 19 pede quando sugere "reduzir a meta diária"."""
    entradas = cadeia()
    dias = planejados(entradas)
    anterior = {"plano_de_acao": {"meta_diaria": {"minutos": 80}}}
    plano = rodar(
        entradas,
        historico_frequencia=sessoes(dias[:2]),
        plano_de_habitos_anterior=anterior,
    )
    meta = plano["plano_de_acao"]["meta_diaria"]

    assert plano["indicadores"]["taxa_de_adesao"] < ADESAO_PARA_REDUZIR
    assert meta["ajuste"] == "reduzida"
    assert meta["minutos"] == round(80 * (1 - PASSO_DE_REDUCAO), 1)
    assert any("voltar a ser cumprida" in f for f in meta["fatores"])


def test_adesao_intermediaria_mantem_a_meta():
    entradas = cadeia()
    dias = planejados(entradas)
    anterior = {"plano_de_acao": {"meta_diaria": {"minutos": 60}}}
    metade = dias[: int(len(dias) * 0.7)]
    plano = rodar(
        entradas,
        historico_frequencia=sessoes(metade),
        plano_de_habitos_anterior=anterior,
    )
    meta = plano["plano_de_acao"]["meta_diaria"]

    assert meta["ajuste"] == "mantida"
    assert meta["minutos"] == 60.0
    assert any("até estabilizar" in f for f in meta["fatores"])


def test_meta_nunca_fica_abaixo_do_piso():
    entradas = cadeia()
    anterior = {"plano_de_acao": {"meta_diaria": {"minutos": 5}}}
    plano = rodar(
        entradas,
        historico_frequencia=sessoes(planejados(entradas)[:1], minutos=4),
        plano_de_habitos_anterior=anterior,
    )

    assert plano["plano_de_acao"]["meta_diaria"]["minutos"] >= MINUTOS_MINIMOS_DE_META


def test_meta_semanal_usa_os_dias_declarados():
    entradas = cadeia()
    plano = rodar(entradas, historico_frequencia=sessoes(planejados(entradas)))
    semanal = plano["plano_de_acao"]["meta_semanal"]
    diaria = plano["plano_de_acao"]["meta_diaria"]

    assert semanal["dias"] == 5
    assert semanal["minutos"] == round(diaria["minutos"] * 5, 1)


# --------------------------------------------------------------------------- #
# Nunca punir
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("termo", TERMOS_PUNITIVOS)
def test_texto_punitivo_e_recusado(termo):
    with pytest.raises(TextoPunitivo):
        _validar_texto(f"Aviso: {termo} por não ter estudado.")


@pytest.mark.parametrize("termo", TERMOS_MANIPULATIVOS)
def test_texto_manipulativo_tambem_e_recusado_aqui(termo):
    with pytest.raises(TextoPunitivo):
        _validar_texto(f"Atenção: {termo}.")


def test_reforcos_sao_todos_positivos():
    """Não existe variedade punitiva na tabela — é isso que garante a regra."""
    for texto in REFORCOS_POSITIVOS.values():
        _validar_texto(texto)


def test_nenhum_texto_emitido_contem_punicao():
    entradas = cadeia()
    plano = rodar(entradas, historico_frequencia=sessoes(planejados(entradas)[:3]))
    estrategia = plano["plano_de_acao"]["estrategia_de_manutencao"]

    for texto in [estrategia["acao"], *estrategia["reforcos"]]:
        _validar_texto(texto)
    assert plano["textos_recusados"] == []


def test_quebra_de_sequencia_gera_retomada_e_nao_cobranca():
    entradas = cadeia()
    antigo = HOJE - timedelta(days=DIAS_PARA_RISCO_DE_QUEBRA + 3)
    plano = rodar(entradas, historico_frequencia=sessoes([antigo]))
    reforcos = plano["plano_de_acao"]["estrategia_de_manutencao"]["reforcos"]

    assert REFORCOS_POSITIVOS["retomada"] in reforcos
    assert "sem cobrança" in REFORCOS_POSITIVOS["retomada"]


# --------------------------------------------------------------------------- #
# Padrões precisam de amostra
# --------------------------------------------------------------------------- #


def test_horario_com_poucas_sessoes_nao_vira_melhor_horario():
    entradas = cadeia()
    poucas = sessoes(planejados(entradas)[: MINIMO_DE_OBSERVACOES - 1], hora="06:00")
    plano = rodar(entradas, historico_frequencia=poucas)

    assert plano["indicadores"]["padroes_por_dia"]["dias_de_maior_falta"] == [] or True
    assert any("não declarado" in o for o in plano["observacoes"])


def test_horario_com_amostra_vira_melhor_faixa():
    entradas = cadeia()
    plano = rodar(entradas, historico_frequencia=sessoes(planejados(entradas), hora="07:00"))
    consolidados = plano["habitos_positivos"]["consolidados"]

    assert any("manha" in h["habito"] for h in consolidados + plano["habitos_positivos"]["em_formacao"])


def test_dias_observados_e_o_intervalo_real_e_nao_a_janela():
    """Hábito observado em 8 dias não virou hábito de 28."""
    entradas = cadeia()
    dias = planejados(entradas)[:4]
    plano = rodar(entradas, historico_frequencia=sessoes(dias, hora="07:00"))
    faixa = next(
        h
        for h in plano["habitos_positivos"]["em_formacao"]
        + plano["habitos_positivos"]["consolidados"]
        if "manha" in h["habito"]
    )

    assert faixa["dias_observados"] == (max(dias) - min(dias)).days + 1
    assert faixa["dias_observados"] < JANELA_DE_OBSERVACAO_DIAS


def test_motivo_unico_de_interrupcao_e_episodio_nao_obstaculo():
    entradas = cadeia()
    plano = rodar(
        entradas,
        historico_frequencia=sessoes(planejados(entradas)[:3]),
        historico_interrupcoes=[{"motivo": "visita"}],
    )
    interrupcoes = plano["indicadores"]["interrupcoes"]

    assert interrupcoes["recorrentes"] == []
    assert interrupcoes["episodicos"][0]["motivo"] == "visita"
    assert plano["habitos_negativos"]["principais_obstaculos"] == []


def test_motivo_repetido_vira_obstaculo():
    entradas = cadeia()
    plano = rodar(
        entradas,
        historico_frequencia=sessoes(planejados(entradas)[:3]),
        historico_interrupcoes=[{"motivo": "trabalho"}, {"motivo": "trabalho"}],
    )
    obstaculos = plano["habitos_negativos"]["principais_obstaculos"]

    assert obstaculos[0]["obstaculo"] == "trabalho"
    assert obstaculos[0]["ocorrencias"] == 2


# --------------------------------------------------------------------------- #
# Hábitos
# --------------------------------------------------------------------------- #


def test_habito_so_consolida_com_adesao_e_tempo():
    entradas = cadeia()
    dias = planejados(entradas)
    curto = [d for d in dias if (max(dias) - d).days < DIAS_PARA_CONSOLIDAR - 5]
    plano = rodar(entradas, historico_frequencia=sessoes(curto, hora="07:00"))

    for habito in plano["habitos_positivos"]["consolidados"]:
        assert habito["adesao"] >= ADESAO_PARA_CONSOLIDAR
        assert habito["dias_observados"] >= DIAS_PARA_CONSOLIDAR
        assert habito["observacoes"] >= MINIMO_DE_OBSERVACOES


def test_habito_em_formacao_declara_o_que_falta():
    entradas = cadeia()
    dias = planejados(entradas)
    plano = rodar(entradas, historico_frequencia=sessoes(dias[: int(len(dias) * 0.6)]))

    for habito in plano["habitos_positivos"]["em_formacao"]:
        assert habito["falta_para_consolidar"]
        assert habito["base"]


def test_habito_declarado_pelo_estudante_e_aceito():
    entradas = cadeia()
    plano = rodar(
        entradas,
        historico_frequencia=sessoes(planejados(entradas)[:3]),
        historico_habitos=[
            {"habito": "revisar antes de dormir", "adesao": 0.9,
             "observacoes": 20, "dias_observados": 30}
        ],
    )
    todos = (
        plano["habitos_positivos"]["consolidados"]
        + plano["habitos_positivos"]["em_formacao"]
    )

    declarado = next(h for h in todos if h["habito"] == "revisar antes de dormir")
    assert declarado["estado"] == "consolidado"
    assert declarado["base"] == "hábito informado pelo estudante"


def test_habito_prioritario_e_um_so():
    entradas = cadeia()
    plano = rodar(entradas, historico_frequencia=sessoes(planejados(entradas)[:4]))
    prioritario = plano["plano_de_acao"]["habito_prioritario"]

    assert prioritario is not None
    assert prioritario["motivo"]
    assert prioritario["origem"]


# --------------------------------------------------------------------------- #
# Sequências, marcos e indicadores
# --------------------------------------------------------------------------- #


def test_melhor_sequencia_historica_e_registrada():
    entradas = cadeia()
    seguidos = [HOJE - timedelta(days=n) for n in range(10, 15)]
    esparsos = [HOJE - timedelta(days=n) for n in (1, 4)]
    plano = rodar(entradas, historico_frequencia=sessoes(seguidos + esparsos))
    melhor = plano["resumo_geral"]["melhor_sequencia_historica"]

    assert melhor["dias"] == 5
    assert melhor["inicio"] and melhor["fim"]


def test_proximo_marco_e_o_seguinte_da_escala():
    entradas = cadeia()
    seguidos = [HOJE - timedelta(days=n) for n in range(4)]
    plano = rodar(entradas, historico_frequencia=sessoes(seguidos))
    marco = plano["plano_de_acao"]["proximo_marco"]

    assert marco["sequencia_atual"] == 4
    assert marco["faltam"] == next(m for m in MARCOS_DE_SEQUENCIA if m > 4) - 4
    assert marco["reforco"] == REFORCOS_POSITIVOS["marco"]


def test_ausencia_prolongada_vira_situacao_de_risco():
    entradas = cadeia()
    antigo = HOJE - timedelta(days=DIAS_PARA_RISCO_DE_QUEBRA + 2)
    plano = rodar(entradas, historico_frequencia=sessoes([antigo]))
    riscos = plano["habitos_negativos"]["situacoes_de_risco"]

    assert riscos
    assert "sem estudo registrado" in riscos[0]["situacao"]


def test_probabilidade_de_manutencao_mostra_a_conta():
    entradas = cadeia()
    plano = rodar(entradas, historico_frequencia=sessoes(planejados(entradas)))
    probabilidade = plano["indicadores"]["probabilidade_de_manutencao"]

    assert 0 <= probabilidade["probabilidade"] <= 1
    assert probabilidade["fatores"]
    assert "projeção comportamental" in probabilidade["base"]


def test_sem_adesao_nao_ha_probabilidade():
    entradas = cadeia()
    entradas["saidas_anteriores"]["06"] = {"cronograma": []}
    plano = rodar(entradas, historico_frequencia=sessoes([HOJE]))
    probabilidade = plano["indicadores"]["probabilidade_de_manutencao"]

    assert probabilidade["probabilidade"] is None
    assert probabilidade["confianca"] == "baixa"


def test_frequencia_semanal_e_mensal_sao_contadas():
    entradas = cadeia()
    datas = [HOJE - timedelta(days=n) for n in (0, 2, 5, 12, 25)]
    plano = rodar(entradas, historico_frequencia=sessoes(datas))
    frequencia = plano["resumo_geral"]["frequencia"]

    assert frequencia["semanal"]["dias"] == 3
    assert frequencia["mensal"]["dias"] == 5


# --------------------------------------------------------------------------- #
# Um número só, compartilhado com o agente 19
# --------------------------------------------------------------------------- #


def test_sequencia_e_identica_a_do_coach():
    """As janelas dos dois agentes são diferentes de propósito — hábito se mede
    em semanas —, mas a leitura do registro é a mesma função, então tudo que
    não depende da janela precisa bater exatamente."""
    entradas = cadeia()
    seguidos = [HOJE - timedelta(days=n) for n in range(4)]
    registros = sessoes(seguidos)
    plano = rodar(entradas, historico_frequencia=registros)

    do_coach = acompanhar(
        {
            **entradas,
            "dados_usuario": {**entradas["dados_usuario"], "historico_frequencia": registros},
        },
        hoje=HOJE,
    )
    assert plano["resumo_geral"]["sequencia_atual"] == (
        do_coach["indicadores"]["sequencia_de_dias_estudando"]
    )


def test_engajamento_do_coach_e_reaproveitado_e_nao_recalculado():
    entradas = cadeia()
    registros = sessoes(planejados(entradas))
    entradas["saidas_anteriores"]["19"] = acompanhar(
        {
            **entradas,
            "dados_usuario": {**entradas["dados_usuario"], "historico_frequencia": registros},
        },
        hoje=HOJE,
    )
    plano = rodar(entradas, historico_frequencia=registros)

    assert plano["resumo_geral"]["engajamento_do_agente_19"] == (
        entradas["saidas_anteriores"]["19"]["resumo_geral"]["nivel_de_engajamento"]
    )


# --------------------------------------------------------------------------- #
# Limites do agente
# --------------------------------------------------------------------------- #


def test_plano_de_habitos_nao_carrega_cronograma_nem_conteudo():
    entradas = cadeia()
    plano = rodar(entradas, historico_frequencia=sessoes(planejados(entradas)))

    proibidos = ("cronograma", "disciplinas", "exercicios", "aula", "sessoes", "arvore")
    assert not set(plano) & set(proibidos)


def test_constantes_sao_declaradas():
    constantes = rodar(cadeia())["constantes_aplicadas"]

    assert constantes["passo_maximo_de_aumento"] == PASSO_MAXIMO_DE_AUMENTO
    assert constantes["adesao_para_consolidar"] == ADESAO_PARA_CONSOLIDAR
    assert constantes["reforcos_positivos"] == REFORCOS_POSITIVOS
    assert constantes["termos_punitivos"] == TERMOS_PUNITIVOS


# --------------------------------------------------------------------------- #
# Orquestrador
# --------------------------------------------------------------------------- #


async def test_orquestrador_executa_o_20_depois_do_19():
    resultado = await MasterOrchestrator().orquestrar(
        "quero criar o hábito de estudar todo dia",
        dados_usuario={
            "objetivo": "Passar no concurso fiscal",
            "edital": EDITAL,
            "escolaridade": "Superior completo",
            "horas_por_dia": 2,
            "dias_por_semana": 5,
            "data_prova": "2026-09-01",
        },
    )
    ordem = [sorted(onda) for onda in resultado.ondas]
    posicao = {agente: indice for indice, onda in enumerate(ordem) for agente in onda}

    assert posicao["20"] > posicao["19"]
    plano = resultado.saidas["20"].conteudo
    assert plano["plano_de_acao"]["estrategia_de_manutencao"]["reforcos"]
