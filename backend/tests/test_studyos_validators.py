import copy

import pytest

from app.studyos.agents import AgentResult, Fase, get_agent
from app.studyos.validators import (
    CAMPOS_OBRIGATORIOS_COMUNS,
    CATEGORIAS,
    GRAVIDADE_BLOQUEANTE,
    GRAVIDADE_RESSALVA,
    INVARIANTES,
    STATUS_APROVADA,
    STATUS_COM_RESSALVAS,
    STATUS_REPROVADA,
    validar,
)
from app.studyos.orchestrator import MasterOrchestrator

EDITAL = {
    "Estatística": {"questoes": 10, "topicos": ["Conjuntos", "Probabilidade"]},
    "Português": {"questoes": 20, "topicos": ["Crase", "Sintaxe"]},
}

DADOS = {
    "objetivo": "Passar no concurso fiscal",
    "edital": EDITAL,
    "escolaridade": "Superior completo",
    "horas_por_dia": 2,
    "dias_por_semana": 5,
    "data_prova": "2026-12-01",
    "nota_corte": 70,
    "resultados_exercicios": [
        {
            "disciplina": "Português",
            "topico": "Crase",
            "acertos": 9,
            "total": 10,
            "data": "2026-07-01",
        }
    ],
}


def saida(codigo, conteudo=None, ok=True, erro=None, lacunas=()):
    """Um AgentResult mínimo, com o contrato de campos que o 24 exige."""
    spec = get_agent(codigo)
    base = {"consumido_por": ["24"], "observacoes": []}
    return AgentResult(
        codigo=codigo,
        nome=spec.nome,
        fase=spec.fase,
        tarefa=spec.tarefa,
        conteudo={**base, **(conteudo or {})} if ok else {},
        erro=erro,
        lacunas=list(lacunas),
    )


def fluxo_minimo(**extras):
    """01, 02 e 24: o mínimo que qualquer fluxo precisa ter."""
    saidas = {"01": saida("01"), "02": saida("02"), **extras}
    return {"01", "02", *extras}, saidas


# --------------------------------------------------------------------------- #
# O validador não toca em nada
# --------------------------------------------------------------------------- #


def test_validar_nao_altera_nenhuma_saida():
    """Se o validador mexer em qualquer saída, este teste falha."""
    selecionados, saidas = fluxo_minimo(
        **{"03": saida("03", {"disciplinas": [], "confiabilidade": "baixa"})}
    )
    antes = copy.deepcopy({c: r.conteudo for c, r in saidas.items()})

    validar(selecionados, saidas)

    assert {c: r.conteudo for c, r in saidas.items()} == antes


def test_laudo_declara_que_nada_foi_alterado():
    selecionados, saidas = fluxo_minimo()
    laudo = validar(selecionados, saidas).to_dict()

    assert laudo["consumido_por"] == ["Master Orchestrator"]
    assert any("não altera nenhuma saída" in o for o in laudo["observacoes"])
    assert any("Somente respostas aprovadas" in o for o in laudo["observacoes"])


def test_campo_ausente_vira_problema_e_nao_valor_padrao():
    spec = get_agent("03")
    incompleta = AgentResult(
        codigo="03", nome=spec.nome, fase=spec.fase, tarefa=spec.tarefa,
        conteudo={"disciplinas": []},
    )
    selecionados, saidas = fluxo_minimo(**{"03": incompleta})
    resultado = validar(selecionados, saidas)

    faltantes = [a for a in resultado.achados if a.campo in CAMPOS_OBRIGATORIOS_COMUNS]
    assert len(faltantes) == len(CAMPOS_OBRIGATORIOS_COMUNS)
    assert all(a.categoria == "estrutural" for a in faltantes)
    assert "consumido_por" not in saidas["03"].conteudo


# --------------------------------------------------------------------------- #
# Status e gravidade
# --------------------------------------------------------------------------- #


def test_fluxo_limpo_e_aprovado():
    selecionados, saidas = fluxo_minimo()
    resultado = validar(selecionados, saidas)

    assert resultado.status == STATUS_APROVADA
    assert resultado.aprovado is True
    assert resultado.problemas == []
    assert resultado.verificacoes


def test_ressalva_aprova_mas_marca():
    selecionados, saidas = fluxo_minimo(
        **{"03": saida("03", {"confiabilidade": "baixa"})}
    )
    resultado = validar(selecionados, saidas)

    assert resultado.status == STATUS_COM_RESSALVAS
    assert resultado.aprovado is True
    assert any(a.gravidade == GRAVIDADE_RESSALVA for a in resultado.achados)


def test_agente_obrigatorio_ausente_reprova():
    resultado = validar({"01"}, {"01": saida("01")})

    assert resultado.status == STATUS_REPROVADA
    assert resultado.aprovado is False
    assert any("02" in p for p in resultado.problemas)


def test_falha_de_agente_reprova_o_fluxo():
    selecionados, saidas = fluxo_minimo(
        **{"03": saida("03", ok=False, erro="estourou")}
    )
    resultado = validar(selecionados, saidas)

    assert resultado.status == STATUS_REPROVADA
    assert any("estourou" in p for p in resultado.problemas)


def test_todo_achado_tem_categoria_gravidade_e_correcao():
    selecionados, saidas = fluxo_minimo(
        **{"03": saida("03", ok=False, erro="x"), "04": saida("04", {"confiabilidade": "baixa"})}
    )
    resultado = validar(selecionados, saidas)

    assert resultado.achados
    for achado in resultado.achados:
        assert achado.categoria in CATEGORIAS
        assert achado.gravidade in (GRAVIDADE_BLOQUEANTE, GRAVIDADE_RESSALVA)
        assert achado.descricao and achado.correcao
        assert achado.agente
        assert achado.id.startswith("v")


# --------------------------------------------------------------------------- #
# Consistência entre agentes
# --------------------------------------------------------------------------- #


def test_invariante_violada_reprova_o_fluxo():
    """Dois agentes discordando sobre o mesmo fato reprovam a entrega."""
    selecionados, saidas = fluxo_minimo(
        **{
            "19": saida("19", {"resumo_geral": {"indice_de_consistencia": 0.7}}),
            "21": saida(
                "21",
                {
                    "indicadores_de_aprendizagem": {
                        "consistencia": {"valor": 0.9}
                    }
                },
            ),
        }
    )
    resultado = validar(selecionados, saidas)

    assert resultado.status == STATUS_REPROVADA
    divergencia = next(
        a for a in resultado.achados if a.categoria == "consistencia"
    )
    assert "índice de consistência diverge" in divergencia.descricao
    assert divergencia.agente == "21"
    assert "reaproveitar o valor do agente 19" in divergencia.correcao


def test_invariante_respeitada_nao_gera_achado():
    selecionados, saidas = fluxo_minimo(
        **{
            "19": saida("19", {"resumo_geral": {"indice_de_consistencia": 0.7}}),
            "21": saida(
                "21",
                {"indicadores_de_aprendizagem": {"consistencia": {"valor": 0.7}}},
            ),
        }
    )
    resultado = validar(selecionados, saidas)

    assert not [a for a in resultado.achados if a.categoria == "consistencia"]
    assert any("invariante" in v for v in resultado.verificacoes)


def test_invariante_com_um_lado_ausente_nao_e_conferida():
    """Ausência de dado não é divergência."""
    selecionados, saidas = fluxo_minimo(
        **{"19": saida("19", {"resumo_geral": {"indice_de_consistencia": 0.7}})}
    )
    resultado = validar(selecionados, saidas)

    assert not [a for a in resultado.achados if a.categoria == "consistencia"]


@pytest.mark.parametrize("invariante", INVARIANTES)
def test_toda_invariante_declara_os_dois_lados(invariante):
    agente_a, caminho_a, agente_b, caminho_b, descricao = invariante

    assert agente_a != agente_b
    assert caminho_a and caminho_b
    assert descricao


def test_ganho_do_23_precisa_bater_com_o_simulado_do_22():
    selecionados, saidas = fluxo_minimo(
        **{
            "22": saida(
                "22",
                {
                    "simulacoes": [
                        {"acao": "melhora_na_consistencia", "impacto_na_probabilidade": 0.05}
                    ]
                },
            ),
            "23": saida(
                "23",
                {
                    "otimizacoes_recomendadas": [
                        {
                            "acao": "reduzir carga",
                            "evidencias": [{"indicador": "x", "valor": 1, "origem": "21"}],
                            "impacto_esperado": {
                                "alavanca": "melhora_na_consistencia",
                                "ganho_na_probabilidade": 0.42,
                            },
                        }
                    ]
                },
            ),
        }
    )
    resultado = validar(selecionados, saidas)

    assert resultado.status == STATUS_REPROVADA
    assert any("diverge do simulado pelo agente 22" in p for p in resultado.problemas)


def test_dependencia_nao_satisfeita_reprova():
    selecionados = {"01", "02", "03"}
    saidas = {"01": saida("01"), "02": saida("02")}
    saidas["03"] = saida("03")
    del saidas["02"]
    resultado = validar(selecionados, saidas)

    assert resultado.status == STATUS_REPROVADA
    assert any("rodou sem a entrada de 02" in p for p in resultado.problemas)


# --------------------------------------------------------------------------- #
# Técnica
# --------------------------------------------------------------------------- #


def test_ciclo_no_grafo_reprova():
    selecionados, saidas = fluxo_minimo(**{"05": saida("05", {"acilico": False, "nos": []})})
    resultado = validar(selecionados, saidas)

    assert resultado.status == STATUS_REPROVADA
    assert any("ciclo" in p for p in resultado.problemas)


def test_referencia_invalida_no_grafo_reprova():
    grafo = {
        "acilico": True,
        "nos": [{"id": "t1", "nome": "Crase", "pre_requisitos": ["inexistente"]}],
    }
    selecionados, saidas = fluxo_minimo(**{"05": saida("05", grafo)})
    resultado = validar(selecionados, saidas)

    assert any("nó inexistente: inexistente" in p for p in resultado.problemas)


def test_no_duplicado_no_grafo_reprova():
    grafo = {
        "acilico": True,
        "nos": [
            {"id": "t1", "nome": "Crase", "pre_requisitos": []},
            {"id": "t1", "nome": "Outro", "pre_requisitos": []},
        ],
    }
    selecionados, saidas = fluxo_minimo(**{"05": saida("05", grafo)})
    resultado = validar(selecionados, saidas)

    assert any("nó duplicado" in p for p in resultado.problemas)


def test_conteudo_agendado_fora_da_arvore_reprova():
    arvore = {
        "disciplinas": [
            {"nome": "Português", "modulos": [{"nome": "M1", "topicos": [{"nome": "Crase"}]}]}
        ]
    }
    plano = {
        "cronograma": [
            {
                "data": "2026-07-01",
                "sessoes": [{"tipo": "conteudo", "conteudo": "Astrofísica"}],
            }
        ]
    }
    selecionados, saidas = fluxo_minimo(
        **{"04": saida("04", arvore), "06": saida("06", plano)}
    )
    resultado = validar(selecionados, saidas)

    assert any("não existe na árvore: Astrofísica" in p for p in resultado.problemas)


def test_subtopico_agendado_e_conteudo_valido():
    """Um subtópico é conteúdo tão legítimo quanto o tópico que o contém."""
    arvore = {
        "disciplinas": [
            {
                "nome": "Português",
                "modulos": [
                    {
                        "nome": "M1",
                        "topicos": [
                            {"nome": "Crase", "subtopicos": [{"nome": "Casos obrigatórios"}]}
                        ],
                    }
                ],
            }
        ]
    }
    plano = {
        "cronograma": [
            {
                "data": "2026-07-01",
                "sessoes": [{"tipo": "conteudo", "conteudo": "Casos obrigatórios"}],
            }
        ]
    }
    selecionados, saidas = fluxo_minimo(
        **{"04": saida("04", arvore), "06": saida("06", plano)}
    )
    resultado = validar(selecionados, saidas)

    assert resultado.aprovado is True


def test_topico_duplicado_na_arvore_e_ressalva():
    arvore = {
        "disciplinas": [
            {
                "nome": "Português",
                "modulos": [
                    {"nome": "M1", "topicos": [{"nome": "Crase"}, {"nome": "Crase"}]}
                ],
            }
        ]
    }
    selecionados, saidas = fluxo_minimo(**{"04": saida("04", arvore)})
    resultado = validar(selecionados, saidas)

    assert resultado.aprovado is True
    assert any("duplicado na árvore" in a.descricao for a in resultado.achados)


# --------------------------------------------------------------------------- #
# Pedagógica
# --------------------------------------------------------------------------- #


def test_conteudo_antes_do_pre_requisito_reprova():
    grafo = {
        "acilico": True,
        "nos": [
            {"id": "t1", "nome": "Conjuntos", "pre_requisitos": []},
            {"id": "t2", "nome": "Probabilidade", "pre_requisitos": ["t1"]},
        ],
    }
    plano = {
        "cronograma": [
            {
                "data": "2026-07-01",
                "sessoes": [{"tipo": "conteudo", "conteudo": "Probabilidade"}],
            },
            {
                "data": "2026-07-02",
                "sessoes": [{"tipo": "conteudo", "conteudo": "Conjuntos"}],
            },
        ]
    }
    selecionados, saidas = fluxo_minimo(
        **{"05": saida("05", grafo), "06": saida("06", plano)}
    )
    resultado = validar(selecionados, saidas)

    assert resultado.status == STATUS_REPROVADA
    achado = next(a for a in resultado.achados if a.categoria == "pedagogica")
    assert "antes do pré-requisito" in achado.descricao
    assert achado.agente == "06"


def test_ordem_correta_de_pre_requisitos_e_verificada():
    grafo = {
        "acilico": True,
        "nos": [
            {"id": "t1", "nome": "Conjuntos", "pre_requisitos": []},
            {"id": "t2", "nome": "Probabilidade", "pre_requisitos": ["t1"]},
        ],
    }
    plano = {
        "cronograma": [
            {"data": "2026-07-01", "sessoes": [{"tipo": "conteudo", "conteudo": "Conjuntos"}]},
            {"data": "2026-07-02", "sessoes": [{"tipo": "conteudo", "conteudo": "Probabilidade"}]},
        ]
    }
    selecionados, saidas = fluxo_minimo(
        **{"05": saida("05", grafo), "06": saida("06", plano)}
    )
    resultado = validar(selecionados, saidas)

    assert resultado.aprovado is True
    assert any("pré-requisitos do grafo" in v for v in resultado.verificacoes)


# --------------------------------------------------------------------------- #
# Segurança: afirmação sem lastro
# --------------------------------------------------------------------------- #


def test_projecao_sem_intervalo_reprova():
    previsao = {
        "resumo_geral": {
            "probabilidade_de_atingir_o_objetivo": {"estimativa": 0.8, "intervalo": None}
        }
    }
    selecionados, saidas = fluxo_minimo(**{"22": saida("22", previsao)})
    resultado = validar(selecionados, saidas)

    assert resultado.status == STATUS_REPROVADA
    assert any("sem intervalo de incerteza" in p for p in resultado.problemas)


def test_projecao_com_intervalo_passa():
    previsao = {
        "resumo_geral": {
            "probabilidade_de_atingir_o_objetivo": {
                "estimativa": 0.8,
                "intervalo": [0.65, 0.95],
            }
        }
    }
    selecionados, saidas = fluxo_minimo(**{"22": saida("22", previsao)})
    resultado = validar(selecionados, saidas)

    assert resultado.aprovado is True
    assert any("intervalo" in v for v in resultado.verificacoes)


def test_recomendacao_sem_evidencia_reprova():
    otimizacao = {
        "otimizacoes_recomendadas": [{"acao": "reduzir carga", "evidencias": []}]
    }
    selecionados, saidas = fluxo_minimo(**{"23": saida("23", otimizacao)})
    resultado = validar(selecionados, saidas)

    assert resultado.status == STATUS_REPROVADA
    assert any("sem evidência declarada" in p for p in resultado.problemas)


def test_erro_com_causa_sem_evidencia_reprova():
    relatorio = {
        "erros": [{"topico": "Crase", "causa_provavel": "desatenção", "evidencias": []}]
    }
    selecionados, saidas = fluxo_minimo(**{"17": saida("17", relatorio)})
    resultado = validar(selecionados, saidas)

    assert resultado.status == STATUS_REPROVADA
    assert any("causa a um erro sem evidência" in p for p in resultado.problemas)


def test_mensagem_sem_dado_citado_reprova():
    acompanhamento = {
        "mensagens": [{"tipo": "incentivo", "texto": "siga em frente", "dados_citados": []}]
    }
    selecionados, saidas = fluxo_minimo(**{"19": saida("19", acompanhamento)})
    resultado = validar(selecionados, saidas)

    assert resultado.status == STATUS_REPROVADA
    assert any("sem citar nenhum dado" in p for p in resultado.problemas)


def test_texto_recusado_pelo_agente_vira_ressalva():
    """Recusar é o comportamento correto — mas a tentativa fica registrada."""
    acompanhamento = {
        "mensagens": [],
        "mensagens_recusadas": [{"chave": "x", "motivo_da_recusa": "genérica"}],
    }
    selecionados, saidas = fluxo_minimo(**{"19": saida("19", acompanhamento)})
    resultado = validar(selecionados, saidas)

    assert resultado.aprovado is True
    assert any("recusou 1 texto" in a.descricao for a in resultado.achados)


# --------------------------------------------------------------------------- #
# Qualidade, lacunas e índices
# --------------------------------------------------------------------------- #


def test_status_pendente_vira_ressalva():
    selecionados, saidas = fluxo_minimo(
        **{"07": saida("07", {"status": "pendente_de_geracao"})}
    )
    resultado = validar(selecionados, saidas)

    assert resultado.status == STATUS_COM_RESSALVAS
    assert any("pendente_de_geracao" in a.descricao for a in resultado.achados)


def test_lacuna_declarada_vira_alerta_e_nao_problema():
    """Lacuna é o agente sendo honesto, não errando."""
    selecionados, saidas = fluxo_minimo(
        **{"03": saida("03", lacunas=["historico"])}
    )
    resultado = validar(selecionados, saidas)

    assert resultado.aprovado is True
    assert any("informação ausente do usuário" in a for a in resultado.alertas)
    assert not any("historico" in p for p in resultado.problemas)


def test_indices_declaram_a_base():
    selecionados, saidas = fluxo_minimo()
    indices = validar(selecionados, saidas).indices

    for nome in (
        "indice_de_qualidade",
        "indice_de_consistencia",
        "indice_de_confiabilidade",
        "indice_de_completude",
    ):
        assert indices[nome]["base"]
        assert indices[nome]["valor"] is None or 0 <= indices[nome]["valor"] <= 1


def test_mais_problemas_derrubam_o_indice():
    limpo, saidas_limpas = fluxo_minimo()
    sujo, saidas_sujas = fluxo_minimo(
        **{"05": saida("05", {"acilico": False, "nos": []})}
    )

    assert (
        validar(sujo, saidas_sujas).indices["indice_de_consistencia"]["valor"]
        < validar(limpo, saidas_limpas).indices["indice_de_consistencia"]["valor"]
    )


def test_completude_conta_saidas_com_lacuna():
    selecionados, saidas = fluxo_minimo(
        **{"03": saida("03", lacunas=["historico"])}
    )
    completude = validar(selecionados, saidas).indices["indice_de_completude"]

    assert completude["valor"] == round(1 - 1 / 3, 4)
    assert "1 de 3" in completude["base"]


# --------------------------------------------------------------------------- #
# Plano de correção
# --------------------------------------------------------------------------- #


def test_sem_bloqueante_nao_ha_reexecucao_a_pedir():
    selecionados, saidas = fluxo_minimo()
    plano = validar(selecionados, saidas).plano_de_correcao

    assert plano["agentes_a_reexecutar"] == []
    assert "nenhum problema bloqueante" in plano["base"]


def test_plano_lista_agentes_ordem_e_campos():
    grafo = {
        "acilico": True,
        "nos": [
            {"id": "t1", "nome": "Conjuntos", "pre_requisitos": []},
            {"id": "t2", "nome": "Probabilidade", "pre_requisitos": ["t1"]},
        ],
    }
    plano_de_estudos = {
        "cronograma": [
            {"data": "2026-07-01", "sessoes": [{"tipo": "conteudo", "conteudo": "Probabilidade"}]},
            {"data": "2026-07-02", "sessoes": [{"tipo": "conteudo", "conteudo": "Conjuntos"}]},
        ]
    }
    selecionados, saidas = fluxo_minimo(
        **{"05": saida("05", grafo), "06": saida("06", plano_de_estudos)}
    )
    correcao = validar(selecionados, saidas).plano_de_correcao

    assert correcao["agentes_a_reexecutar"] == ["06"]
    assert correcao["ordem_de_reexecucao"] == [["06"]]
    assert "06.cronograma" in correcao["campos_a_corrigir"]
    assert correcao["criterios_para_nova_validacao"]


def test_ordem_de_reexecucao_respeita_o_grafo():
    """Quem falhou e quem rodou sem a entrada dele voltam juntos, em ordem.

    Reexecutar só o agente que falhou deixaria de pé as saídas que foram
    produzidas sem a entrada dele — corretas por acidente, no melhor caso.
    """
    selecionados = {"01", "02", "03", "04"}
    saidas = {
        "01": saida("01", ok=False, erro="x"),
        "02": saida("02"),
        "03": saida("03"),
        "04": saida("04"),
    }
    correcao = validar(selecionados, saidas).plano_de_correcao

    assert correcao["agentes_a_reexecutar"] == ["01", "02", "03", "04"]
    assert correcao["ordem_de_reexecucao"] == [["01"], ["02"], ["03"], ["04"]]


# --------------------------------------------------------------------------- #
# Integração com o orquestrador
# --------------------------------------------------------------------------- #


async def test_fluxo_real_completo_e_auditado():
    resultado = await MasterOrchestrator().orquestrar(
        "quero um plano completo de estudos", dados_usuario=DADOS
    )
    validacao = resultado.validacao

    assert validacao.status in (STATUS_APROVADA, STATUS_COM_RESSALVAS)
    assert validacao.verificacoes
    assert validacao.indices["indice_de_consistencia"]["valor"] is not None
    for achado in validacao.achados:
        assert achado.gravidade == GRAVIDADE_RESSALVA


async def test_laudo_do_24_aparece_como_saida_do_fluxo():
    resultado = await MasterOrchestrator().orquestrar(
        "diagnóstico", dados_usuario=DADOS
    )
    laudo = resultado.saidas["24"].conteudo

    assert laudo["status"] in (STATUS_APROVADA, STATUS_COM_RESSALVAS, STATUS_REPROVADA)
    assert laudo["resumo_geral"]["status_da_validacao"] == laudo["status"]
    assert "plano_de_correcao" in laudo


async def test_invariantes_do_sistema_valem_no_fluxo_real():
    """As invariantes não são teoria: rodam contra a cadeia inteira."""
    resultado = await MasterOrchestrator().orquestrar(
        "como está meu desempenho e o que otimizar", dados_usuario=DADOS
    )

    divergencias = [
        a
        for a in resultado.validacao.achados
        if a.categoria == "consistencia" and a.gravidade == GRAVIDADE_BLOQUEANTE
    ]
    assert divergencias == []
    assert any("invariante" in v for v in resultado.validacao.verificacoes)
