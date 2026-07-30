from datetime import date, timedelta

import pytest

from app.studyos.agentes.conhecimento import analisar as analisar_conhecimento
from app.studyos.agentes.curriculo import construir as construir_curriculo
from app.studyos.agentes.dependencias import mapear
from app.studyos.agentes.dificuldade import (
    LIMIAR_PADRAO_RECORRENTE,
    LIMIAR_SOBRECARGA_TEMPO,
    detectar,
)
from app.studyos.agentes.objetivo import analisar as analisar_objetivo
from app.studyos.agentes.perfil import analisar as analisar_perfil
from app.studyos.agentes.roadmap import construir as construir_roadmap
from app.studyos.orchestrator import MasterOrchestrator

HOJE = date(2026, 1, 5)

EDITAL = {
    "Estatística": {"questoes": 10, "topicos": ["Conjuntos", "Probabilidade"]},
    "Português": {"questoes": 20, "topicos": ["Crase", "Sintaxe"]},
}

PRE = {"Probabilidade": ["Conjuntos"]}


def cadeia(dados=None):
    """Roda 01–06 de verdade e devolve as entradas prontas para o 12."""
    base = {
        "objetivo": "Passar no concurso fiscal",
        "edital": EDITAL,
        "pre_requisitos": PRE,
        "escolaridade": "Superior completo",
        "profissao": "Analista",
        "rotina": "Estudo em casa",
        "horas_por_dia": 4,
        "dias_por_semana": 5,
        "idade": 30,
        "experiencia_anterior": "nenhuma",
        "preferencia_estudo": "questões",
        "data_prova": "2026-06-01",
        **(dados or {}),
    }
    m1 = analisar_perfil({"dados_usuario": base}, hoje=HOJE)
    m2 = analisar_objetivo({"dados_usuario": base, "solicitacao": ""}, hoje=HOJE)
    m3 = analisar_conhecimento(
        {"dados_usuario": base, "saidas_anteriores": {"01": m1, "02": m2}}, hoje=HOJE
    )
    m4 = construir_curriculo(
        {"dados_usuario": base, "saidas_anteriores": {"02": m2, "03": m3}}
    )
    m5 = mapear({"dados_usuario": base, "saidas_anteriores": {"03": m3, "04": m4}})
    m6 = construir_roadmap(
        {"dados_usuario": base, "saidas_anteriores": {"01": m1, "02": m2, "05": m5}},
        hoje=HOJE,
    )
    return {
        "solicitacao": "",
        "dados_usuario": base,
        "saidas_anteriores": {"01": m1, "02": m2, "03": m3, "04": m4, "05": m5, "06": m6},
    }


def acertos(topico, certos, total, disciplina="Português", data=None):
    return {
        "disciplina": disciplina,
        "topico": topico,
        "acertos": certos,
        "total": total,
        "data": (data or HOJE).isoformat(),
    }


def topico_de(relatorio, nome):
    return next(t for t in relatorio["topicos"] if t["topico"] == nome)


# --------------------------------------------------------------------------- #
# Sem evidência, sem dificuldade presumida
# --------------------------------------------------------------------------- #


def test_sem_evidencia_nenhum_indice_e_calculado():
    relatorio = detectar(cadeia(), hoje=HOJE)

    assert relatorio["resumo_geral"]["indice_geral_de_dificuldade"] is None
    assert relatorio["resumo_geral"]["nivel_geral"] == "indeterminado"
    assert all(t["dificuldade"]["indice"] is None for t in relatorio["topicos"])
    assert all(
        t["dificuldade"]["nivel"] == "indeterminado" for t in relatorio["topicos"]
    )
    assert any("não é presumida" in o for o in relatorio["observacoes"])


def test_sem_mapa_de_conhecimento_nao_ha_o_que_medir():
    relatorio = detectar({"dados_usuario": {}, "saidas_anteriores": {}}, hoje=HOJE)

    assert relatorio["topicos"] == []
    assert relatorio["confiabilidade"] == "baixa"
    assert "mapa_de_conhecimento_do_agente_03" in relatorio["lacunas"]


def test_base_do_indice_declara_a_evidencia_usada():
    dados = {"resultados_exercicios": [acertos("Crase", 3, 10)]}
    relatorio = detectar(cadeia(dados), hoje=HOJE)
    crase = topico_de(relatorio, "Crase")

    assert "10 questões" in crase["dificuldade"]["base"]
    assert "erro" in crase["dificuldade"]["componentes"]


# --------------------------------------------------------------------------- #
# Índice de dificuldade
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "certos,total,esperado",
    [
        (10, 10, "muito_facil"),
        (5, 10, "medio"),
        (1, 10, "critico"),
    ],
)
def test_indice_acompanha_a_taxa_de_erro(certos, total, esperado):
    dados = {"resultados_exercicios": [acertos("Crase", certos, total)]}
    relatorio = detectar(cadeia(dados), hoje=HOJE)

    assert topico_de(relatorio, "Crase")["dificuldade"]["nivel"] == esperado


def test_esquecimento_entra_como_componente():
    antigo = HOJE - timedelta(days=120)
    dados = {"resultados_exercicios": [acertos("Crase", 9, 10, data=antigo)]}
    relatorio = detectar(cadeia(dados), hoje=HOJE)
    dificuldade = topico_de(relatorio, "Crase")["dificuldade"]

    assert "esquecimento" in dificuldade["componentes"]
    assert topico_de(relatorio, "Crase")["esquecido"] is True
    assert "Crase" in relatorio["conteudos_esquecidos"]


def test_tempo_acima_do_estimado_entra_no_indice():
    dados = {
        "resultados_exercicios": [acertos("Crase", 8, 10)],
        "historico_sessoes": [{"conteudo": "Crase", "tempo_gasto_min": 300}],
    }
    relatorio = detectar(cadeia(dados), hoje=HOJE)
    componentes = topico_de(relatorio, "Crase")["dificuldade"]["componentes"]

    assert "tempo" in componentes
    assert componentes["tempo"]["razao"] > 1
    assert "150 min estimados" in componentes["tempo"]["base"]


def test_confianca_cresce_com_o_numero_de_componentes():
    so_erro = detectar(
        cadeia({"resultados_exercicios": [acertos("Crase", 5, 10)]}), hoje=HOJE
    )
    completo = detectar(
        cadeia(
            {
                "resultados_exercicios": [
                    acertos("Crase", 5, 10, data=HOJE - timedelta(days=90))
                ],
                "historico_sessoes": [{"conteudo": "Crase", "tempo_gasto_min": 300}],
                "erros": [{"topico": "Crase", "categoria": "aplicacao"}],
            }
        ),
        hoje=HOJE,
    )

    assert topico_de(so_erro, "Crase")["dificuldade"]["confianca"] == "baixa"
    assert topico_de(completo, "Crase")["dificuldade"]["confianca"] == "alta"


# --------------------------------------------------------------------------- #
# Tipos de dificuldade
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "categoria,esperado",
    [
        ("fixacao", "memorizacao"),
        ("compreensao", "conceitual"),
        ("aplicacao", "procedimental"),
        ("analise", "interpretacao"),
    ],
)
def test_tipo_de_dificuldade_vem_da_categoria_da_questao(categoria, esperado):
    dados = {
        "resultados_exercicios": [acertos("Crase", 4, 10)],
        "erros": [{"topico": "Crase", "categoria": categoria}],
    }
    relatorio = detectar(cadeia(dados), hoje=HOJE)

    assert topico_de(relatorio, "Crase")["tipos_de_dificuldade"]["predominante"] == esperado


def test_tipo_declarado_tem_precedencia_sobre_a_categoria():
    dados = {
        "resultados_exercicios": [acertos("Crase", 4, 10)],
        "erros": [{"topico": "Crase", "categoria": "fixacao", "tipo": "interpretacao"}],
    }
    relatorio = detectar(cadeia(dados), hoje=HOJE)

    assert topico_de(relatorio, "Crase")["tipos_de_dificuldade"]["predominante"] == (
        "interpretacao"
    )


def test_sem_erros_os_tipos_nao_sao_separados():
    dados = {"resultados_exercicios": [acertos("Crase", 4, 10)]}
    relatorio = detectar(cadeia(dados), hoje=HOJE)

    assert relatorio["tipos_de_dificuldade"]["predominante"] is None
    assert any("não puderam ser separados" in o for o in relatorio["observacoes"])


# --------------------------------------------------------------------------- #
# Padrões, gargalos e sobrecarga
# --------------------------------------------------------------------------- #


def test_erro_repetido_no_mesmo_topico_vira_padrao():
    dados = {
        "resultados_exercicios": [acertos("Crase", 3, 10)],
        "erros": [
            {"topico": "Crase", "categoria": "aplicacao"},
            {"topico": "Crase", "categoria": "aplicacao"},
        ],
    }
    relatorio = detectar(cadeia(dados), hoje=HOJE)
    padrao = relatorio["padroes_de_erro"][0]

    assert padrao["padrao"] == "erro_repetido_no_topico"
    assert padrao["ocorrencias"] >= LIMIAR_PADRAO_RECORRENTE
    assert padrao["alvo"] == "Crase"


def test_erro_unico_nao_vira_padrao():
    dados = {
        "resultados_exercicios": [acertos("Crase", 3, 10)],
        "erros": [{"topico": "Crase", "categoria": "aplicacao"}],
    }
    relatorio = detectar(cadeia(dados), hoje=HOJE)
    assert relatorio["padroes_de_erro"] == []


def test_gargalo_combina_dificuldade_com_bloqueio():
    dados = {
        "resultados_exercicios": [
            acertos("Conjuntos", 1, 10, disciplina="Estatística"),
            acertos("Crase", 1, 10),
        ]
    }
    relatorio = detectar(cadeia(dados), hoje=HOJE)
    gargalos = relatorio["principais_gargalos"]

    # Conjuntos bloqueia Probabilidade; Crase não bloqueia nada.
    assert gargalos[0]["topico"] == "Conjuntos"
    assert gargalos[0]["conteudos_bloqueados"] == 1
    assert relatorio["conceitos_que_bloqueiam_o_progresso"][0]["topico"] == "Conjuntos"


def test_tempo_muito_acima_do_estimado_sinaliza_sobrecarga():
    dados = {
        "resultados_exercicios": [acertos("Crase", 5, 10)],
        "historico_sessoes": [{"conteudo": "Crase", "tempo_gasto_min": 600}],
    }
    relatorio = detectar(cadeia(dados), hoje=HOJE)
    sinais = {s["sinal"] for s in relatorio["sinais_de_sobrecarga"]}

    assert "tempo_muito_acima_do_estimado" in sinais
    assert str(LIMIAR_SOBRECARGA_TEMPO) in " ".join(
        s["evidencia"] for s in relatorio["sinais_de_sobrecarga"]
    )


def test_acumulo_de_conteudos_dificeis_sinaliza_sobrecarga():
    dados = {
        "resultados_exercicios": [
            acertos("Crase", 1, 10),
            acertos("Sintaxe", 1, 10),
            acertos("Conjuntos", 1, 10, disciplina="Estatística"),
        ]
    }
    relatorio = detectar(cadeia(dados), hoje=HOJE)
    sinais = {s["sinal"] for s in relatorio["sinais_de_sobrecarga"]}

    assert "acumulo_de_conteudos_dificeis" in sinais


def test_faltas_do_plano_entram_como_sinal():
    dados = {
        "faltas": ["2026-01-05", "2026-01-06", "2026-01-07"],
        "resultados_exercicios": [acertos("Crase", 5, 10)],
    }
    relatorio = detectar(cadeia(dados), hoje=HOJE)
    assert "faltas_no_cronograma" in {s["sinal"] for s in relatorio["sinais_de_sobrecarga"]}


# --------------------------------------------------------------------------- #
# Velocidade, evolução e risco
# --------------------------------------------------------------------------- #


def test_velocidade_de_aprendizagem_compara_real_com_estimado():
    dados = {
        "resultados_exercicios": [acertos("Crase", 5, 10)],
        "historico_sessoes": [{"conteudo": "Crase", "tempo_gasto_min": 300}],
    }
    relatorio = detectar(cadeia(dados), hoje=HOJE)
    velocidade = relatorio["resumo_geral"]["velocidade_de_aprendizagem"]

    assert velocidade["razao_tempo_real_sobre_estimado"] == 2.0
    assert velocidade["leitura"] == "acima do previsto"


def test_sem_tempo_registrado_a_velocidade_fica_indisponivel():
    relatorio = detectar(cadeia(), hoje=HOJE)
    velocidade = relatorio["resumo_geral"]["velocidade_de_aprendizagem"]

    assert velocidade["razao_tempo_real_sobre_estimado"] is None
    assert velocidade["conteudos_medidos"] == 0


def test_evolucao_compara_com_o_relatorio_anterior():
    antes = detectar(
        cadeia({"resultados_exercicios": [acertos("Crase", 2, 10)]}), hoje=HOJE
    )
    depois = detectar(
        cadeia(
            {
                "resultados_exercicios": [acertos("Crase", 9, 10)],
                "relatorio_anterior": antes,
            }
        ),
        hoje=HOJE,
    )
    evolucao = depois["resumo_geral"]["evolucao"]

    assert evolucao["disponivel"] is True
    assert evolucao["tendencia"] == "melhorando"
    assert "Crase" in evolucao["melhoraram"]


def test_sem_relatorio_anterior_a_tendencia_e_indeterminada():
    relatorio = detectar(
        cadeia({"resultados_exercicios": [acertos("Crase", 5, 10)]}), hoje=HOJE
    )
    assert relatorio["resumo_geral"]["tendencia_de_aprendizagem"] == "indeterminada"


def test_risco_de_abandono_exige_fatores_medidos():
    tranquilo = detectar(
        cadeia({"resultados_exercicios": [acertos("Crase", 9, 10)]}), hoje=HOJE
    )
    assert tranquilo["risco_de_abandono"]["nivel"] == "baixo"

    dados = {
        "faltas": ["2026-01-05", "2026-01-06", "2026-01-07"],
        "resultados_exercicios": [
            acertos("Crase", 0, 10),
            acertos("Sintaxe", 0, 10),
            acertos("Conjuntos", 0, 10, disciplina="Estatística"),
        ],
    }
    critico = detectar(cadeia(dados), hoje=HOJE)
    assert critico["risco_de_abandono"]["nivel"] in ("medio", "alto")
    assert critico["risco_de_abandono"]["fatores"]


# --------------------------------------------------------------------------- #
# Reforço e limites de escopo
# --------------------------------------------------------------------------- #


def test_reforco_prioriza_dificuldade_prioridade_e_bloqueio():
    dados = {
        "resultados_exercicios": [
            acertos("Conjuntos", 1, 10, disciplina="Estatística"),
            acertos("Crase", 4, 10),
        ]
    }
    relatorio = detectar(cadeia(dados), hoje=HOJE)
    reforco = relatorio["recomendacoes_de_reforco"]

    assert reforco[0]["topico"] == "Conjuntos"
    assert reforco[0]["bloqueia_conteudos"] == 1
    assert reforco[0]["acao_sugerida"] == "reforço imediato"


def test_conteudo_sem_evidencia_nao_entra_no_reforco():
    dados = {"resultados_exercicios": [acertos("Crase", 4, 10)]}
    relatorio = detectar(cadeia(dados), hoje=HOJE)
    alvos = {r["topico"] for r in relatorio["recomendacoes_de_reforco"]}

    assert alvos == {"Crase"}


def test_relatorio_nao_altera_plano_nem_grafo():
    relatorio = detectar(cadeia(), hoje=HOJE)
    proibidos = {"cronograma", "plano", "nos", "arestas", "sequencia_logica", "exercicios"}

    assert proibidos.isdisjoint(relatorio)
    assert any("não altera o Plano de Estudos" in o for o in relatorio["observacoes"])


def test_disciplina_agrega_criticos_dominados_e_sem_evidencia():
    dados = {
        "resultados_exercicios": [acertos("Crase", 1, 10), acertos("Sintaxe", 10, 10)]
    }
    relatorio = detectar(cadeia(dados), hoje=HOJE)
    portugues = next(
        d for d in relatorio["disciplinas"] if d["disciplina"] == "Português"
    )

    assert portugues["conteudos_criticos"] == ["Crase"]
    assert portugues["conteudos_dominados"] == ["Sintaxe"]
    assert portugues["topicos_medidos"] == 2


def test_saida_declara_os_agentes_consumidores():
    relatorio = detectar(cadeia(), hoje=HOJE)
    assert relatorio["consumido_por"] == [
        "13", "14", "15", "17", "18", "19", "21", "22", "23", "24"
    ]


# --------------------------------------------------------------------------- #
# Integração
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_agente_12_no_fluxo_completo():
    resultado = await MasterOrchestrator().orquestrar(
        "Quero exercícios do meu edital",
        dados_usuario={
            "objetivo": "Passar no concurso fiscal",
            "edital": EDITAL,
            "escolaridade": "Superior completo",
            "horas_por_dia": 3,
            "dias_por_semana": 5,
            "data_prova": "2027-01-01",
            "profissao": "Analista",
            "rotina": "Estudo em casa",
            "experiencia_anterior": "nenhuma",
            "preferencia_estudo": "questões",
            "idade": 30,
            "resultados_exercicios": [
                {"disciplina": "Português", "topico": "Crase", "acertos": 2, "total": 10}
            ],
            "erros": [{"topico": "Crase", "categoria": "aplicacao"}],
        },
    )
    relatorio = resultado.saidas["12"].conteudo

    assert relatorio["resumo_geral"]["indice_geral_de_dificuldade"] is not None
    assert relatorio["recomendacoes_de_reforco"]
    assert resultado.validacao.aprovado is True


@pytest.mark.asyncio
async def test_agente_12_roda_depois_do_diagnostico_e_dos_exercicios():
    resultado = await MasterOrchestrator().orquestrar("Quero exercícios de logaritmo")
    ondas = {
        agente.split()[0]: onda["onda"]
        for onda in resultado.ordem_execucao
        for agente in onda["agentes"]
    }
    assert ondas["03"] < ondas["12"]
    assert ondas["09"] < ondas["12"]
