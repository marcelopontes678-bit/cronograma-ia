from datetime import date, timedelta

import pytest

from app.studyos.agentes.coach import (
    DIAS_DE_AUSENCIA_RELEVANTE,
    JANELA_ANTIRREPETICAO_DIAS,
    JANELA_DE_ANALISE_DIAS,
    MINIMO_DE_DIAS_PLANEJADOS,
    NIVEIS_DE_ENGAJAMENTO,
    SEQUENCIA_MINIMA_PARA_RECONHECIMENTO,
    TERMOS_GENERICOS,
    TERMOS_MANIPULATIVOS,
    TIPOS_DE_MENSAGEM,
    MensagemGenerica,
    MensagemManipulativa,
    _validar_mensagem,
    acompanhar,
)
from app.studyos.agentes.conhecimento import analisar as analisar_conhecimento
from app.studyos.agentes.curriculo import construir as construir_curriculo
from app.studyos.agentes.dependencias import mapear as mapear_dependencias
from app.studyos.agentes.dificuldade import detectar
from app.studyos.agentes.erros import analisar as analisar_erros
from app.studyos.agentes.fraquezas import mapear as mapear_fraquezas
from app.studyos.agentes.objetivo import analisar as analisar_objetivo
from app.studyos.agentes.perfil import analisar as analisar_perfil
from app.studyos.agentes.roadmap import construir as construir_roadmap
from app.studyos.orchestrator import MasterOrchestrator

#: O plano é feito no começo e o acompanhamento acontece depois: a janela de
#: análise olha para trás, então só há engajamento a medir se o plano já tiver
#: dias no passado. Um plano recém-gerado não tem passado, e isso também é
#: testado.
INICIO_DO_PLANO = date(2026, 3, 2)
HOJE = INICIO_DO_PLANO + timedelta(days=12)

EDITAL = {
    "Estatística": {"questoes": 10, "topicos": ["Conjuntos", "Probabilidade"]},
    "Português": {"questoes": 20, "topicos": ["Crase", "Sintaxe", "Ortografia", "Verbos"]},
}


def acertos(topico, certos, total, disciplina="Português", quando=None):
    return {
        "disciplina": disciplina,
        "topico": topico,
        "acertos": certos,
        "total": total,
        "data": (quando or HOJE).isoformat(),
    }


HISTORICO = {
    "resultados_exercicios": [
        acertos("Crase", 19, 20),
        acertos("Sintaxe", 6, 10),
        acertos("Conjuntos", 3, 10, disciplina="Estatística"),
        acertos("Probabilidade", 7, 10, disciplina="Estatística"),
    ]
}


def cadeia(dados=None):
    """Roda 01–06, 12, 17 e 18 de verdade e devolve as entradas para o 19."""
    base = {
        "objetivo": "Passar no concurso fiscal",
        "edital": EDITAL,
        "escolaridade": "Superior completo",
        "horas_por_dia": 2,
        "dias_por_semana": 5,
        "data_prova": "2026-09-01",
        **HISTORICO,
        **(dados or {}),
    }
    m1 = analisar_perfil({"dados_usuario": base}, hoje=INICIO_DO_PLANO)
    m2 = analisar_objetivo({"dados_usuario": base, "solicitacao": ""}, hoje=INICIO_DO_PLANO)
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
    ant = {"01": m1, "02": m2, "03": m3, "04": m4, "05": m5, "06": m6}
    ant["12"] = detectar({"dados_usuario": base, "saidas_anteriores": ant}, hoje=HOJE)
    ant["17"] = analisar_erros(
        {"dados_usuario": base, "saidas_anteriores": ant}, hoje=HOJE
    )
    entradas = {"solicitacao": "", "dados_usuario": base, "saidas_anteriores": ant}
    ant["18"] = mapear_fraquezas(entradas, hoje=HOJE)
    return entradas


def dias_planejados(entradas, quantos=None):
    """Datas que o agente 06 reservou dentro da janela de análise."""
    inicio = HOJE - timedelta(days=JANELA_DE_ANALISE_DIAS - 1)
    datas = [
        date.fromisoformat(d["data"])
        for d in entradas["saidas_anteriores"]["06"]["cronograma"]
        if inicio <= date.fromisoformat(d["data"]) <= HOJE
    ]
    return datas if quantos is None else datas[:quantos]


def frequencia(datas):
    return [{"data": d.isoformat(), "minutos": 90} for d in datas]


def rodar(entradas, **campos):
    dados = {**entradas["dados_usuario"], **campos}
    return acompanhar({**entradas, "dados_usuario": dados}, hoje=HOJE)


def textos(plano):
    return [m["texto"] for m in plano["mensagens"]]


# --------------------------------------------------------------------------- #
# Silêncio: sem dado, sem estimativa
# --------------------------------------------------------------------------- #


def test_sem_frequencia_o_engajamento_nao_e_estimado():
    """Um coach que inventa consistência a partir de nada é pior que um calado."""
    plano = rodar(cadeia())
    resumo = plano["resumo_geral"]

    assert resumo["indice_de_consistencia"] == 0.0 or resumo["nivel_de_engajamento"]
    assert plano["lacunas"] == ["historico_frequencia"]
    assert plano["confiabilidade"] in ("baixa", "media")
    assert any("não foi estimado" in o or "invenção" in o for o in plano["observacoes"])


def test_sem_dias_planejados_nao_ha_indice_de_consistencia():
    entradas = cadeia()
    entradas["saidas_anteriores"]["06"] = {"cronograma": []}
    plano = rodar(entradas, historico_frequencia=frequencia([HOJE]))
    resumo = plano["resumo_geral"]

    assert resumo["indice_de_consistencia"] is None
    assert "sem denominador" in resumo["base_da_consistencia"]
    assert resumo["nivel_de_engajamento"] == "indeterminado"


def test_poucos_dias_planejados_nao_classificam_engajamento():
    """Cumprir o único dia planejado não é "engajamento alto"."""
    entradas = cadeia()
    poucos = dias_planejados(entradas, MINIMO_DE_DIAS_PLANEJADOS - 1)
    entradas["saidas_anteriores"]["06"] = {
        "cronograma": [{"data": d.isoformat(), "sessoes": []} for d in poucos],
        "metas": entradas["saidas_anteriores"]["06"]["metas"],
    }
    plano = rodar(entradas, historico_frequencia=frequencia(poucos))

    assert plano["resumo_geral"]["indice_de_consistencia"] == 1.0
    assert plano["resumo_geral"]["nivel_de_engajamento"] == "indeterminado"
    assert any("abaixo do mínimo" in o for o in plano["observacoes"])
    assert not any(m["chave"].startswith("consistencia") for m in plano["mensagens"])


# --------------------------------------------------------------------------- #
# Nenhuma mensagem sem dado
# --------------------------------------------------------------------------- #


def test_toda_mensagem_emitida_cita_um_dado():
    entradas = cadeia()
    plano = rodar(entradas, historico_frequencia=frequencia(dias_planejados(entradas)))

    assert plano["mensagens"]
    for mensagem in plano["mensagens"]:
        assert mensagem["dados_citados"], mensagem["texto"]
        assert mensagem["tipo"] in TIPOS_DE_MENSAGEM
        assert mensagem["emitida"] is True


@pytest.mark.parametrize("termo", TERMOS_GENERICOS)
def test_frase_generica_e_recusada(termo):
    with pytest.raises(MensagemGenerica):
        _validar_mensagem(f"{termo}, você estudou 5 dias", ["5"])


@pytest.mark.parametrize("termo", TERMOS_MANIPULATIVOS)
def test_frase_manipulativa_e_recusada(termo):
    with pytest.raises(MensagemManipulativa):
        _validar_mensagem(f"Atenção: {termo}. São 5 dias sem estudar.", ["5"])


def test_mensagem_sem_dado_e_recusada_mesmo_sem_termo_proibido():
    """Frase educada e vazia continua sendo frase vazia."""
    with pytest.raises(MensagemGenerica):
        _validar_mensagem("Continue se dedicando aos estudos.", ["7", "Crase"])


def test_mensagem_com_dado_passa():
    _validar_mensagem("Você cumpriu 7 de 10 dias planejados.", ["7", "10"])


def test_manipulacao_tem_precedencia_sobre_generico():
    """A recusa mais grave é a que precisa aparecer."""
    with pytest.raises(MensagemManipulativa):
        _validar_mensagem("Você consegue, mas você vai reprovar assim. 3 dias.", ["3"])


def test_nenhuma_mensagem_emitida_contem_termo_proibido():
    entradas = cadeia()
    plano = rodar(entradas, historico_frequencia=frequencia(dias_planejados(entradas)[:2]))

    for texto in textos(plano):
        normalizado = texto.lower()
        for termo in TERMOS_GENERICOS + TERMOS_MANIPULATIVOS:
            assert termo not in normalizado


# --------------------------------------------------------------------------- #
# Repetição
# --------------------------------------------------------------------------- #


def test_mensagem_ja_enviada_na_janela_e_suprimida():
    entradas = cadeia()
    enviadas = [
        {"chave": "foco", "data": (HOJE - timedelta(days=1)).isoformat()},
    ]
    plano = rodar(
        entradas,
        historico_frequencia=frequencia(dias_planejados(entradas)),
        mensagens_enviadas=enviadas,
    )

    assert not any(m["chave"] == "foco" for m in plano["mensagens"])
    suprimida = next(m for m in plano["mensagens_recusadas"] if m["chave"] == "foco")
    assert "já enviada" in suprimida["motivo_da_recusa"]
    assert any("repetição" in o for o in plano["observacoes"])


def test_mensagem_antiga_pode_ser_reenviada():
    entradas = cadeia()
    enviadas = [
        {
            "chave": "foco",
            "data": (HOJE - timedelta(days=JANELA_ANTIRREPETICAO_DIAS + 1)).isoformat(),
        }
    ]
    plano = rodar(
        entradas,
        historico_frequencia=frequencia(dias_planejados(entradas)),
        mensagens_enviadas=enviadas,
    )

    assert any(m["chave"] == "foco" for m in plano["mensagens"])


def test_mesmo_fato_nao_vira_duas_mensagens():
    """Sequência de dias é reconhecimento; não precisa virar conquista também."""
    entradas = cadeia()
    seguidos = [HOJE - timedelta(days=n) for n in range(SEQUENCIA_MINIMA_PARA_RECONHECIMENTO)]
    plano = rodar(entradas, historico_frequencia=frequencia(seguidos))
    reconhecimentos = [m for m in plano["mensagens"] if m["tipo"] == "reconhecimento"]

    assert len(reconhecimentos) == 1
    assert len({m["chave"] for m in plano["mensagens"]}) == len(plano["mensagens"])


# --------------------------------------------------------------------------- #
# Consistência, sequência e ausência
# --------------------------------------------------------------------------- #


def test_consistencia_e_dias_cumpridos_sobre_planejados():
    entradas = cadeia()
    planejados = dias_planejados(entradas)
    metade = planejados[: len(planejados) // 2]
    plano = rodar(entradas, historico_frequencia=frequencia(metade))
    resumo = plano["resumo_geral"]

    assert resumo["indice_de_consistencia"] == round(len(metade) / len(planejados), 4)
    assert str(len(planejados)) in resumo["base_da_consistencia"]


def test_engajamento_alto_com_plano_cumprido():
    entradas = cadeia()
    plano = rodar(entradas, historico_frequencia=frequencia(dias_planejados(entradas)))

    assert plano["resumo_geral"]["nivel_de_engajamento"] == "alto"
    assert plano["resumo_geral"]["nivel_de_engajamento"] in NIVEIS_DE_ENGAJAMENTO


def test_engajamento_critico_gera_alerta_e_nao_incentivo():
    entradas = cadeia()
    planejados = dias_planejados(entradas)
    plano = rodar(entradas, historico_frequencia=frequencia(planejados[:1]))

    assert plano["resumo_geral"]["nivel_de_engajamento"] in ("critico", "baixo")
    tipos = {m["tipo"] for m in plano["mensagens"]}
    assert "alerta" in tipos
    assert not any(m["chave"] == "consistencia_boa" for m in plano["mensagens"])


def test_sequencia_de_dias_conta_apenas_consecutivos():
    entradas = cadeia()
    datas = [HOJE, HOJE - timedelta(days=1), HOJE - timedelta(days=5)]
    plano = rodar(entradas, historico_frequencia=frequencia(datas))

    assert plano["indicadores"]["sequencia_de_dias_estudando"]["dias"] == 2


def test_sequencia_zera_quando_o_estudo_e_antigo():
    entradas = cadeia()
    plano = rodar(entradas, historico_frequencia=frequencia([HOJE - timedelta(days=6)]))
    sequencia = plano["indicadores"]["sequencia_de_dias_estudando"]

    assert sequencia["dias"] == 0
    assert "há 6 dias" in sequencia["base"]


def test_ausencia_prolongada_vira_alerta():
    entradas = cadeia()
    ausente = HOJE - timedelta(days=DIAS_DE_AUSENCIA_RELEVANTE + 1)
    plano = rodar(entradas, historico_frequencia=frequencia([ausente]))
    alertas = [m for m in plano["mensagens"] if m["chave"] == "ausencia"]

    assert alertas
    assert str(DIAS_DE_AUSENCIA_RELEVANTE + 1) in alertas[0]["texto"]
    assert plano["indicadores"]["dias_desde_o_ultimo_estudo"] == (
        DIAS_DE_AUSENCIA_RELEVANTE + 1
    )


def test_dia_registrado_sem_estudo_nao_conta_como_frequencia():
    entradas = cadeia()
    planejados = dias_planejados(entradas)
    registros = frequencia(planejados[:1]) + [
        {"data": d.isoformat(), "estudou": False} for d in planejados[1:]
    ]
    plano = rodar(entradas, historico_frequencia=registros)

    assert plano["resumo_geral"]["indice_de_consistencia"] == round(
        1 / len(planejados), 4
    )


# --------------------------------------------------------------------------- #
# Risco de abandono
# --------------------------------------------------------------------------- #


def test_risco_do_agente_12_e_reaproveitado_e_nao_recalculado():
    entradas = cadeia()
    entradas["saidas_anteriores"]["12"]["risco_de_abandono"] = {
        "nivel": "medio",
        "fatores": ["índice geral de dificuldade alto"],
        "base": "medido pelo agente 12",
    }
    plano = rodar(entradas, historico_frequencia=frequencia(dias_planejados(entradas)))
    risco = plano["resumo_geral"]["risco_de_abandono"]

    assert risco["nivel"] == "medio"
    assert "índice geral de dificuldade alto" in risco["fatores"]


def test_frequencia_ruim_eleva_o_risco_e_declara_o_motivo():
    entradas = cadeia()
    ausente = HOJE - timedelta(days=DIAS_DE_AUSENCIA_RELEVANTE + 2)
    plano = rodar(entradas, historico_frequencia=frequencia([ausente]))
    risco = plano["resumo_geral"]["risco_de_abandono"]

    assert risco["nivel"] != "baixo"
    assert any("sem registro de estudo" in f for f in risco["fatores"])
    assert "agente 12" in risco["base"]


# --------------------------------------------------------------------------- #
# Orientação
# --------------------------------------------------------------------------- #


def test_foco_sai_do_ranking_de_urgencia_do_agente_18():
    entradas = cadeia()
    plano = rodar(entradas, historico_frequencia=frequencia(dias_planejados(entradas)))
    foco = plano["orientacoes"]["principal_foco"]
    urgentes = entradas["saidas_anteriores"]["18"]["ranking"]["mais_urgentes"]

    assert foco["topico"] == urgentes[0]["topico"]
    assert foco["origem"] == "agente 18"


def test_sem_fraqueza_o_foco_vem_do_erro_recorrente():
    entradas = cadeia()
    entradas["saidas_anteriores"]["18"] = {}
    entradas["saidas_anteriores"]["17"] = {
        "indicadores": {
            "erros_recorrentes": [
                {"topico": "Sintaxe", "tipo": "conceitual", "frequencia": 3}
            ]
        }
    }
    plano = rodar(entradas, historico_frequencia=frequencia(dias_planejados(entradas)))
    foco = plano["orientacoes"]["principal_foco"]

    assert foco["topico"] == "Sintaxe"
    assert foco["origem"] == "agente 17"


def test_sem_nenhuma_fonte_o_foco_e_declarado_ausente():
    entradas = cadeia()
    entradas["saidas_anteriores"]["18"] = {}
    entradas["saidas_anteriores"]["17"] = {}
    plano = rodar(entradas, historico_frequencia=frequencia(dias_planejados(entradas)))

    assert plano["orientacoes"]["principal_foco"] is None
    assert any("Nenhum ponto de foco" in o for o in plano["observacoes"])


def test_engajamento_baixo_muda_a_estrategia():
    entradas = cadeia()
    planejados = dias_planejados(entradas)
    ruim = rodar(entradas, historico_frequencia=frequencia(planejados[:1]))
    bom = rodar(entradas, historico_frequencia=frequencia(planejados))

    assert "reduzir a meta" in ruim["orientacoes"]["estrategia_sugerida"]["estrategia"]
    assert ruim["orientacoes"]["estrategia_sugerida"]["agente_responsavel"] == "20"
    assert bom["orientacoes"]["estrategia_sugerida"]["estrategia"] != (
        ruim["orientacoes"]["estrategia_sugerida"]["estrategia"]
    )


def test_tom_acompanha_o_engajamento_sem_mudar_o_dado():
    entradas = cadeia()
    planejados = dias_planejados(entradas)
    ruim = rodar(entradas, historico_frequencia=frequencia(planejados[:1]))
    bom = rodar(entradas, historico_frequencia=frequencia(planejados))

    assert ruim["orientacoes"]["tom_da_comunicacao"]["tom"] != (
        bom["orientacoes"]["tom_da_comunicacao"]["tom"]
    )
    for plano in (ruim, bom):
        for mensagem in plano["mensagens"]:
            assert mensagem["dados_citados"]


def test_proxima_meta_vem_do_plano_quando_nao_ha_pendencia():
    entradas = cadeia()
    plano = rodar(entradas, historico_frequencia=frequencia(dias_planejados(entradas)))
    meta = plano["orientacoes"]["proxima_meta"]

    assert meta is not None
    assert meta["origem"] in ("agente 06", "metas pendentes")


def test_meta_declarada_pelo_estudante_entra_nos_indicadores():
    entradas = cadeia()
    metas = [
        {"meta": "terminar Estatística", "cumprida": True},
        {"meta": "fazer 200 questões", "cumprida": False},
    ]
    plano = rodar(
        entradas,
        historico_frequencia=frequencia(dias_planejados(entradas)),
        historico_metas=metas,
    )

    assert plano["indicadores"]["metas_cumpridas"][0]["meta"] == "terminar Estatística"
    assert any(
        m["meta"] == "fazer 200 questões" for m in plano["indicadores"]["metas_pendentes"]
    )


# --------------------------------------------------------------------------- #
# Momento de contato e conquistas
# --------------------------------------------------------------------------- #


def test_melhor_momento_sai_do_plano_de_estudos():
    entradas = cadeia()
    plano = rodar(entradas, historico_frequencia=frequencia(dias_planejados(entradas)))
    momento = plano["melhor_momento_de_contato"]

    assert momento["momento"]
    assert "agente 06" in momento["base"]


def test_sem_plano_o_momento_nao_e_inventado():
    entradas = cadeia()
    entradas["saidas_anteriores"]["06"] = {"cronograma": []}
    entradas["saidas_anteriores"]["01"] = {}
    plano = rodar(entradas, historico_frequencia=frequencia([HOJE]))

    assert plano["melhor_momento_de_contato"]["momento"] is None
    assert "não definido" in plano["melhor_momento_de_contato"]["base"]


def test_conquista_vem_do_registro_e_nao_de_cortesia():
    entradas = cadeia()
    sem_nada = rodar(entradas)
    assert sem_nada["indicadores"]["conquistas"] == []

    seguidos = [HOJE - timedelta(days=n) for n in range(SEQUENCIA_MINIMA_PARA_RECONHECIMENTO)]
    com_sequencia = rodar(entradas, historico_frequencia=frequencia(seguidos))
    assert com_sequencia["indicadores"]["conquistas"][0]["tipo"] == "constancia"
    assert com_sequencia["indicadores"]["conquistas"][0]["base"]


def test_fraqueza_reduzida_vira_conquista():
    entradas = cadeia()
    entradas["saidas_anteriores"]["18"] = {
        "fraquezas": [
            {
                "topico": "Conjuntos",
                "indice_de_fraqueza": 0.4,
                "variacao": {"indice_anterior": 0.8, "variacao": -0.4},
            }
        ],
        "ranking": {"mais_urgentes": []},
    }
    plano = rodar(entradas, historico_frequencia=frequencia(dias_planejados(entradas)))
    conquistas = [
        c for c in plano["indicadores"]["conquistas"] if c["tipo"] == "fraqueza_reduzida"
    ]

    assert conquistas
    assert "Conjuntos" in conquistas[0]["conquista"]


# --------------------------------------------------------------------------- #
# Limites do agente
# --------------------------------------------------------------------------- #


def test_plano_de_acompanhamento_nao_carrega_cronograma_nem_conteudo():
    entradas = cadeia()
    plano = rodar(entradas, historico_frequencia=frequencia(dias_planejados(entradas)))

    proibidos = ("cronograma", "plano_de_estudos", "sessoes", "exercicios", "aula", "disciplinas")
    assert not set(plano) & set(proibidos)


def test_constantes_sao_declaradas():
    constantes = rodar(cadeia())["constantes_aplicadas"]

    assert constantes["janela_de_analise_dias"] == JANELA_DE_ANALISE_DIAS
    assert constantes["termos_genericos"] == TERMOS_GENERICOS
    assert constantes["termos_manipulativos"] == TERMOS_MANIPULATIVOS
    assert constantes["minimo_de_dias_planejados"] == MINIMO_DE_DIAS_PLANEJADOS


# --------------------------------------------------------------------------- #
# Orquestrador
# --------------------------------------------------------------------------- #


async def test_orquestrador_executa_o_19_depois_do_18():
    resultado = await MasterOrchestrator().orquestrar(
        "me ajuda a manter o ritmo de estudos",
        dados_usuario={
            "objetivo": "Passar no concurso fiscal",
            "edital": EDITAL,
            "escolaridade": "Superior completo",
            "horas_por_dia": 2,
            "dias_por_semana": 5,
            "data_prova": "2026-09-01",
            **HISTORICO,
        },
    )
    ordem = [sorted(onda) for onda in resultado.ondas]
    posicao = {agente: indice for indice, onda in enumerate(ordem) for agente in onda}

    assert posicao["19"] > posicao["18"]
    plano = resultado.saidas["19"].conteudo
    assert plano["resumo_geral"]["nivel_de_engajamento"]
    for mensagem in plano["mensagens"]:
        assert mensagem["dados_citados"]
