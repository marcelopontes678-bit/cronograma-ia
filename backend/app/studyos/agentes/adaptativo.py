"""Agente 13 — Adaptive Teacher.

Única responsabilidade: adaptar *como* o conteúdo é ensinado. Não cria
cronograma, não define currículo, não altera o Grafo de Aprendizagem e não
reescreve a teoria oficial da aula.

A maior parte deste agente é **decisão**, não redação: estratégia didática,
nível de linguagem, ritmo, profundidade, quantidade de exemplos e a
recomendação final (avançar, revisar, reforçar, repetir exercícios) saem de
tabelas declaradas sobre os dados dos agentes 01, 03 e 12. Só a reexplicação em
si precisa de redator.

Duas regras estruturam o módulo:

* **Toda adaptação carrega justificativa com dado do estudante.** Um ajuste sem
  `justificativa` não é adaptação, é palpite — por isso a justificativa é campo
  obrigatório de cada ajuste, não comentário.
* **Adaptar não é reescrever.** A teoria da aula entra como referência imutável;
  o agente muda a abordagem, nunca o conteúdo conceitual.
"""

from __future__ import annotations

from typing import Any, Callable

from app.studyos.agentes.comum import como_lista, como_texto, preenchido
from app.studyos.agentes.comum import declara_confiabilidade
from app.studyos.agentes.portoes import localizar_no

# --------------------------------------------------------------------------- #
# Constantes declaradas
# --------------------------------------------------------------------------- #

ESTRATEGIAS = (
    "explicacao_direta",
    "analogias",
    "estudos_de_caso",
    "exemplos_progressivos",
    "comparacoes",
    "passo_a_passo",
    "aprendizagem_baseada_em_problemas",
)

#: Estratégias preferidas por tipo de dificuldade (agente 12), em ordem.
ESTRATEGIA_POR_DIFICULDADE: dict[str, tuple[str, ...]] = {
    "conceitual": ("analogias", "comparacoes", "explicacao_direta"),
    "procedimental": ("passo_a_passo", "exemplos_progressivos", "aprendizagem_baseada_em_problemas"),
    "interpretacao": ("estudos_de_caso", "aprendizagem_baseada_em_problemas", "comparacoes"),
    "memorizacao": ("exemplos_progressivos", "comparacoes", "passo_a_passo"),
}

#: Sem dificuldade detectada, a abordagem padrão por nível de domínio.
ESTRATEGIA_POR_NIVEL: dict[str, str] = {
    "iniciante": "exemplos_progressivos",
    "basico": "passo_a_passo",
    "intermediario": "explicacao_direta",
    "avancado": "aprendizagem_baseada_em_problemas",
}

#: Ajuste de estratégia conforme o estilo de aprendizagem (agente 01).
ESTRATEGIA_POR_ESTILO: dict[str, str] = {
    "visual": "comparacoes",
    "auditivo": "explicacao_direta",
    "leitura_escrita": "explicacao_direta",
    "cinestesico": "aprendizagem_baseada_em_problemas",
}

RITMO_POR_NIVEL: dict[str, str] = {
    "iniciante": "lento",
    "basico": "moderado",
    "intermediario": "moderado",
    "avancado": "rapido",
}

PROFUNDIDADE_POR_NIVEL: dict[str, str] = {
    "iniciante": "essencial",
    "basico": "essencial_com_aplicacao",
    "intermediario": "completa",
    "avancado": "completa_com_excecoes",
}

EXEMPLOS_POR_NIVEL: dict[str, int] = {
    "iniciante": 3,
    "basico": 2,
    "intermediario": 1,
    "avancado": 1,
}

ANALOGIAS_POR_NIVEL: dict[str, int] = {
    "iniciante": 2,
    "basico": 1,
    "intermediario": 1,
    "avancado": 0,
}

#: Índice de dificuldade (agente 12) a partir do qual o reforço é acionado.
LIMIAR_ID_REFORCO = 0.6
#: Abaixo disso, o conteúdo é considerado pronto para avançar.
LIMIAR_ID_AVANCO = 0.4
#: Erros no mesmo tópico que caracterizam dificuldade persistente.
LIMIAR_ERROS_PERSISTENTES = 2

NIVEIS_PRONTOS_PARA_AVANCAR = ("intermediario", "avancado")

SLOTS: tuple[dict[str, Any], ...] = (
    {
        "chave": "explicacao_personalizada",
        "condicional": False,
        "instrucao": (
            "Reexplicar o conteúdo pela estratégia escolhida, no nível de "
            "linguagem indicado. Mesma teoria da aula, abordagem diferente."
        ),
    },
    {
        "chave": "exemplos_adicionais",
        "condicional": True,
        "instrucao": (
            "Exemplos extras na quantidade indicada, distintos dos que o agente "
            "08 já produziu."
        ),
    },
    {
        "chave": "analogias",
        "condicional": True,
        "instrucao": (
            "Analogias na quantidade indicada, cada uma declarando onde deixa "
            "de valer."
        ),
    },
    {
        "chave": "pontos_de_atencao",
        "condicional": False,
        "instrucao": (
            "O que observar durante o estudo deste conteúdo, a partir dos sinais "
            "de confusão detectados."
        ),
    },
)

CHAVES_DE_SLOT = tuple(slot["chave"] for slot in SLOTS)


class PreRequisitoPendente(Exception):
    """Tentativa de adaptar ensino de conteúdo com pré-requisito não concluído."""


# --------------------------------------------------------------------------- #
# Leitura dos dados do estudante
# --------------------------------------------------------------------------- #


def _portao(no: dict | None, grafo: dict, aula: dict) -> dict | None:
    if no is None and not aula:
        return {
            "motivo": "conteudo_ausente",
            "detalhe": "Nenhum conteúdo identificado no grafo nem aula recebida.",
            "acao": "Indicar o conteúdo ou gerar a aula.",
        }
    if no is not None and no.get("status") == "bloqueado":
        por_id = {n["id"]: n["nome"] for n in grafo.get("nos", [])}
        pendentes = [por_id.get(pre, pre) for pre in no.get("bloqueado_por", [])]
        return {
            "motivo": "pre_requisitos_nao_concluidos",
            "detalhe": "Pré-requisitos pendentes: " + ", ".join(pendentes),
            "acao": "Estudar os pré-requisitos antes de adaptar o ensino.",
        }
    return None


def _dificuldade_do_topico(relatorio: dict, no: dict | None, aula: dict) -> dict:
    alvo = como_texto(
        (no or {}).get("nome") or (aula.get("conteudo") or {}).get("nome") or ""
    )
    for topico in relatorio.get("topicos", []):
        if como_texto(topico["topico"]) == alvo:
            return topico
    return {}


def _sinais_de_confusao(medicao: dict, dificuldade: dict) -> list[dict]:
    """Só o que tem evidência — confusão presumida não vira reexplicação."""
    sinais: list[dict] = []

    indice = (dificuldade.get("dificuldade") or {}).get("indice")
    if indice is not None and indice >= LIMIAR_ID_REFORCO:
        sinais.append(
            {
                "sinal": "indice_de_dificuldade_alto",
                "evidencia": f"índice {indice:.0%} (agente 12)",
                "severidade": "alta",
            }
        )

    if dificuldade.get("frequencia_de_erros", 0) >= LIMIAR_ERROS_PERSISTENTES:
        sinais.append(
            {
                "sinal": "erros_persistentes",
                "evidencia": f"{dificuldade['frequencia_de_erros']} erros no tópico",
                "severidade": "alta",
            }
        )

    componentes = (dificuldade.get("dificuldade") or {}).get("componentes", {})
    if "tempo" in componentes and componentes["tempo"].get("razao", 0) > 1.5:
        sinais.append(
            {
                "sinal": "tempo_acima_do_previsto",
                "evidencia": componentes["tempo"]["base"],
                "severidade": "media",
            }
        )

    if medicao.get("esquecido") or dificuldade.get("esquecido"):
        sinais.append(
            {
                "sinal": "conteudo_esquecido",
                "evidencia": "retenção abaixo do limiar (agente 03)",
                "severidade": "media",
            }
        )

    taxa = medicao.get("taxa_acerto")
    if taxa is not None and taxa < 0.5:
        sinais.append(
            {
                "sinal": "taxa_de_acerto_baixa",
                "evidencia": f"{taxa:.0%} de acerto medido",
                "severidade": "alta",
            }
        )
    return sinais


def _estrategia(
    tipo_de_dificuldade: str | None,
    nivel: str,
    estilo: str | None,
    ja_usadas: list[str],
) -> dict:
    """Escolhe a abordagem — e evita repetir a que já não funcionou."""
    if tipo_de_dificuldade in ESTRATEGIA_POR_DIFICULDADE:
        candidatas = list(ESTRATEGIA_POR_DIFICULDADE[tipo_de_dificuldade])
        base = f"dificuldade {tipo_de_dificuldade} detectada pelo agente 12"
    else:
        candidatas = [ESTRATEGIA_POR_NIVEL.get(nivel, "explicacao_direta")]
        base = f"nível de domínio '{nivel}', sem tipo de dificuldade isolado"

    do_estilo = ESTRATEGIA_POR_ESTILO.get(estilo or "")
    if do_estilo and do_estilo not in candidatas:
        candidatas.append(do_estilo)

    restantes = [c for c in candidatas if c not in ja_usadas]
    escolhida = restantes[0] if restantes else candidatas[0]

    return {
        "estrategia": escolhida,
        "justificativa": base
        + (
            f"; abordagens já tentadas ({', '.join(ja_usadas)}) foram evitadas"
            if ja_usadas
            else ""
        ),
        "alternativas": [c for c in candidatas if c != escolhida],
        "influencia_do_estilo": estilo,
    }


def _ajustes(nivel: str, sinais: list[dict], estilo: str | None, indice: float | None) -> list[dict]:
    """Cada ajuste sai com a justificativa colada — regra da spec."""
    intensificar = any(s["severidade"] == "alta" for s in sinais)

    exemplos = EXEMPLOS_POR_NIVEL.get(nivel, 2) + (1 if intensificar else 0)
    analogias = ANALOGIAS_POR_NIVEL.get(nivel, 1) + (1 if intensificar else 0)
    ritmo = RITMO_POR_NIVEL.get(nivel, "moderado")
    if intensificar and ritmo == "rapido":
        ritmo = "moderado"
    elif intensificar and ritmo == "moderado":
        ritmo = "lento"

    justificativa_sinais = (
        "; ".join(f"{s['sinal']} ({s['evidencia']})" for s in sinais)
        if sinais
        else "nenhum sinal de confusão medido"
    )

    return [
        {
            "dimensao": "linguagem",
            "valor": nivel,
            "justificativa": f"domínio medido do conteúdo: {nivel}",
        },
        {
            "dimensao": "complexidade",
            "valor": PROFUNDIDADE_POR_NIVEL.get(nivel, "completa"),
            "justificativa": f"profundidade compatível com o nível '{nivel}'",
        },
        {
            "dimensao": "ritmo",
            "valor": ritmo,
            "justificativa": (
                f"ritmo reduzido por sinal de confusão: {justificativa_sinais}"
                if intensificar
                else f"ritmo padrão do nível '{nivel}'"
            ),
        },
        {
            "dimensao": "quantidade_de_exemplos",
            "valor": exemplos,
            "justificativa": (
                f"{EXEMPLOS_POR_NIVEL.get(nivel, 2)} do nível"
                + (" + 1 por sinal de confusão de severidade alta" if intensificar else "")
            ),
        },
        {
            "dimensao": "quantidade_de_analogias",
            "valor": analogias,
            "justificativa": (
                f"{ANALOGIAS_POR_NIVEL.get(nivel, 1)} do nível"
                + (" + 1 por sinal de confusão de severidade alta" if intensificar else "")
                + (f"; estilo {estilo} favorece analogia" if estilo == "visual" else "")
            ),
        },
        {
            "dimensao": "profundidade",
            "valor": PROFUNDIDADE_POR_NIVEL.get(nivel, "completa"),
            "justificativa": (
                f"índice de dificuldade em {indice:.0%} (agente 12)"
                if indice is not None
                else "sem índice de dificuldade medido"
            ),
        },
    ]


def _criterios_de_dominio(medicao: dict, dificuldade: dict, sinais: list[dict]) -> list[dict]:
    """Checklist verificável — cada critério diz se foi atendido e com que dado."""
    taxa = medicao.get("taxa_acerto")
    indice = (dificuldade.get("dificuldade") or {}).get("indice")
    erros = dificuldade.get("frequencia_de_erros", 0)
    classificacao = medicao.get("classificacao")
    esquecido = bool(medicao.get("esquecido") or dificuldade.get("esquecido"))

    return [
        {
            # Sem este critério, conteúdo esquecido com acerto histórico alto
            # passaria como "dominado" e o agente mandaria avançar sobre uma
            # base que já se perdeu.
            "criterio": "conteúdo retido (não marcado como esquecido)",
            "atendido": not esquecido,
            "evidencia": (
                "retenção abaixo do limiar (agente 03)" if esquecido else "retenção adequada"
            ),
        },
        {
            "criterio": "domínio medido em nível intermediário ou avançado",
            "atendido": classificacao in NIVEIS_PRONTOS_PARA_AVANCAR,
            "evidencia": f"classificação atual: {classificacao or 'sem medição'}",
        },
        {
            "criterio": f"taxa de acerto igual ou superior a {int(0.7 * 100)}%",
            "atendido": taxa is not None and taxa >= 0.7,
            "evidencia": f"{taxa:.0%} medido" if taxa is not None else "sem medição",
        },
        {
            "criterio": f"índice de dificuldade abaixo de {LIMIAR_ID_AVANCO:.0%}",
            "atendido": indice is not None and indice < LIMIAR_ID_AVANCO,
            "evidencia": f"{indice:.0%}" if indice is not None else "sem índice",
        },
        {
            "criterio": "sem erros persistentes no tópico",
            "atendido": erros < LIMIAR_ERROS_PERSISTENTES,
            "evidencia": f"{erros} erro(s) registrado(s)",
        },
        {
            "criterio": "sem sinal de confusão de severidade alta",
            "atendido": not any(s["severidade"] == "alta" for s in sinais),
            "evidencia": f"{len(sinais)} sinal(is) detectado(s)",
        },
    ]


def _recomendacao(criterios: list[dict], medicao: dict, dificuldade: dict) -> dict:
    atendidos = [c for c in criterios if c["atendido"]]
    indice = (dificuldade.get("dificuldade") or {}).get("indice")
    erros = dificuldade.get("frequencia_de_erros", 0)
    esquecido = medicao.get("esquecido") or dificuldade.get("esquecido")

    if len(atendidos) == len(criterios):
        decisao, motivo = "avancar", "todos os critérios de domínio foram atendidos"
    elif esquecido:
        decisao, motivo = "revisar", "conteúdo marcado como esquecido pelo agente 03"
    elif indice is not None and indice >= LIMIAR_ID_REFORCO:
        decisao, motivo = (
            "reforcar",
            f"índice de dificuldade em {indice:.0%}, acima do limiar de reforço",
        )
    elif erros >= LIMIAR_ERROS_PERSISTENTES:
        decisao, motivo = (
            "repetir_exercicios",
            f"{erros} erros no mesmo tópico indicam prática insuficiente",
        )
    elif not medicao:
        decisao, motivo = (
            "reforcar",
            "sem medição do conteúdo: o avanço não pode ser confirmado",
        )
    else:
        decisao, motivo = (
            "reforcar",
            f"{len(criterios) - len(atendidos)} critério(s) de domínio ainda não atendido(s)",
        )

    return {
        "decisao": decisao,
        "motivo": motivo,
        "criterios_atendidos": len(atendidos),
        "criterios_totais": len(criterios),
    }


def _solicitacoes(recomendacao: dict, sinais: list[dict], conteudo: dict | None) -> list[dict]:
    """Pedidos aos agentes responsáveis — este agente não executa nenhum deles."""
    nome = (conteudo or {}).get("nome", "o conteúdo")
    pedidos: list[dict] = []

    if recomendacao["decisao"] == "revisar":
        pedidos.append(
            {
                "agente": "15 Revision Planner",
                "pedido": f"antecipar revisão de {nome}",
                "motivo": recomendacao["motivo"],
            }
        )
        pedidos.append(
            {
                "agente": "14 Memory Scheduler",
                "pedido": f"encurtar o intervalo de repetição de {nome}",
                "motivo": recomendacao["motivo"],
            }
        )
    if recomendacao["decisao"] == "repetir_exercicios":
        pedidos.append(
            {
                "agente": "09 Exercise Generator",
                "pedido": f"nova bateria de {nome} na mesma faixa de dificuldade",
                "motivo": recomendacao["motivo"],
            }
        )
    if recomendacao["decisao"] == "reforcar" and any(
        s["severidade"] == "alta" for s in sinais
    ):
        pedidos.append(
            {
                "agente": "23 Optimization Agent",
                "pedido": f"realocar tempo de estudo para {nome}",
                "motivo": "dificuldade persistente com sinal de severidade alta",
            }
        )
    return pedidos


# --------------------------------------------------------------------------- #
# Briefing e montagem
# --------------------------------------------------------------------------- #


def montar_briefing(entradas: dict[str, Any]) -> dict[str, Any]:
    dados = entradas.get("dados_usuario", {}) or {}
    campos = {k: v for k, v in dados.items() if k != "perfil"}
    if isinstance(dados.get("perfil"), dict):
        campos = {**campos, **dados["perfil"]}

    anteriores = entradas.get("saidas_anteriores", {})
    perfil = anteriores.get("01", {}) or {}
    mapa_conhecimento = anteriores.get("03", {}) or {}
    grafo = anteriores.get("05", {}) or {}
    aula = anteriores.get("07", {}) or {}
    exemplos = anteriores.get("08", {}) or {}
    exercicios = anteriores.get("09", {}) or {}
    flashcards = anteriores.get("10", {}) or {}
    resumos = anteriores.get("11", {}) or {}
    relatorio = anteriores.get("12", {}) or {}

    no = localizar_no(grafo, aula, campos.get("conteudo_solicitado"))
    bloqueio = _portao(no, grafo, aula)
    if bloqueio:
        return {"bloqueio": bloqueio, "conteudo": None, "slots": []}

    conteudo = aula.get("conteudo") or (
        {"id": no["id"], "nome": no["nome"], "disciplina": no["disciplina"]}
        if no
        else None
    )

    medicao = _medicao_do_topico(mapa_conhecimento, conteudo)
    dificuldade = _dificuldade_do_topico(relatorio, no, aula)
    sinais = _sinais_de_confusao(medicao, dificuldade)

    nivel = (aula.get("nivel_do_estudante") or {}).get("nivel") or _nivel_por_classificacao(
        medicao.get("classificacao")
    )
    estilo = (perfil.get("estilo_aprendizagem") or {}).get("predominante")
    tipo = (dificuldade.get("tipos_de_dificuldade") or {}).get("predominante")
    indice = (dificuldade.get("dificuldade") or {}).get("indice")

    estrategia = _estrategia(tipo, nivel, estilo, como_lista(campos.get("estrategias_ja_usadas")))
    ajustes = _ajustes(nivel, sinais, estilo, indice)
    criterios = _criterios_de_dominio(medicao, dificuldade, sinais)
    recomendacao = _recomendacao(criterios, medicao, dificuldade)

    quantidade_exemplos = next(
        a["valor"] for a in ajustes if a["dimensao"] == "quantidade_de_exemplos"
    )
    quantidade_analogias = next(
        a["valor"] for a in ajustes if a["dimensao"] == "quantidade_de_analogias"
    )
    slots = [
        {
            **slot,
            "aplicavel": (
                True
                if not slot["condicional"]
                else (
                    quantidade_exemplos > 0
                    if slot["chave"] == "exemplos_adicionais"
                    else quantidade_analogias > 0
                )
            ),
            "quantidade": (
                quantidade_exemplos
                if slot["chave"] == "exemplos_adicionais"
                else quantidade_analogias
                if slot["chave"] == "analogias"
                else None
            ),
        }
        for slot in SLOTS
    ]

    return {
        "bloqueio": None,
        "conteudo": conteudo,
        "objetivo_da_sessao": aula.get("objetivo"),
        "perfil_de_aprendizagem": {
            "estilo_predominante": estilo,
            "base": (perfil.get("estilo_aprendizagem") or {}).get("base"),
        },
        "nivel_de_dominio": {
            "nivel": nivel,
            "classificacao_medida": medicao.get("classificacao"),
            "taxa_de_acerto": medicao.get("taxa_acerto"),
        },
        "estrategia_didatica": estrategia,
        "ajustes": ajustes,
        "sinais_de_confusao": sinais,
        "criterios_para_dominio": criterios,
        "recomendacao": recomendacao,
        "solicitacoes": _solicitacoes(recomendacao, sinais, conteudo),
        "slots": slots,
        "slots_aplicaveis": [s["chave"] for s in slots if s["aplicavel"]],
        "teoria_de_referencia": {
            "aula": {
                "desenvolvimento": aula.get("desenvolvimento"),
                "pontos_chave": como_lista(aula.get("pontos_chave")),
                "erros_comuns": aula.get("erros_comuns"),
            },
            "exemplos_ja_usados": [
                exemplos.get(chave, {}).get("enunciado")
                for chave in ("exemplo_introdutorio", "exemplo_pratico", "analogia")
                if isinstance(exemplos.get(chave), dict)
            ],
            "resumo_disponivel": bool(resumos.get("resumo_1min")),
            "flashcards_disponiveis": len(flashcards.get("flashcards", [])),
            "exercicios_disponiveis": len(exercicios.get("exercicios", [])),
            "regra": (
                "A teoria da aula é imutável. Adaptar é mudar a abordagem, o "
                "ritmo e os exemplos — nunca o conteúdo conceitual."
            ),
        },
        "proibicoes": [
            "não alterar o conteúdo conceitual da aula (agente 07)",
            "não modificar o currículo (agente 04)",
            "não modificar o Grafo de Dependências (agente 05)",
            "não modificar o cronograma (agente 06)",
        ],
    }


def _medicao_do_topico(mapa_conhecimento: dict, conteudo: dict | None) -> dict:
    if not conteudo:
        return {}
    alvo = como_texto(conteudo["nome"])
    for disciplina in mapa_conhecimento.get("disciplinas", []):
        for topico in disciplina.get("topicos", []):
            if como_texto(topico["topico"]) == alvo:
                return topico
    return {}


def _nivel_por_classificacao(classificacao: str | None) -> str:
    return {
        "nao_conhece": "iniciante",
        "basico": "basico",
        "intermediario": "intermediario",
        "avancado": "avancado",
    }.get(classificacao or "", "iniciante")


def montar(briefing: dict[str, Any], textos: dict[str, Any] | None = None) -> dict[str, Any]:
    """Monta a experiência adaptada — revalidando o portão de pré-requisitos."""
    bloqueio = briefing.get("bloqueio")
    if bloqueio and textos:
        raise PreRequisitoPendente(bloqueio["detalhe"])

    if bloqueio:
        return {
            "adaptada": False,
            "bloqueio": bloqueio,
            "status": "bloqueada",
            "objetivo_da_sessao": None,
            "estrategia_didatica": None,
            "ajustes": [],
            "recomendacao": None,
            **{chave: None for chave in CHAVES_DE_SLOT},
            "briefing": None,
            "consumido_por": CONSUMIDORES,
            "observacoes": [f"Ensino não adaptado: {bloqueio['detalhe']}"],
            "lacunas": ["pre_requisitos_concluidos"],
        }

    redigidos = dict(textos or {})
    desconhecidos = sorted(set(redigidos) - set(CHAVES_DE_SLOT))
    aplicaveis = {s["chave"] for s in briefing["slots"] if s["aplicavel"]}
    pendentes = [
        chave for chave in aplicaveis if not preenchido(redigidos.get(chave))
    ]

    experiencia = {
        "adaptada": bool(textos) and not pendentes,
        "bloqueio": None,
        "conteudo": briefing["conteudo"],
        "objetivo_da_sessao": briefing["objetivo_da_sessao"],
        "estrategia_didatica": briefing["estrategia_didatica"],
        "nivel_de_linguagem": briefing["nivel_de_dominio"]["nivel"],
        "perfil_de_aprendizagem": briefing["perfil_de_aprendizagem"],
        "ajustes": briefing["ajustes"],
        "sinais_de_confusao": briefing["sinais_de_confusao"],
        "criterios_para_dominio": briefing["criterios_para_dominio"],
        "recomendacao": briefing["recomendacao"],
        "solicitacoes": briefing["solicitacoes"],
    }
    for chave in CHAVES_DE_SLOT:
        valor = redigidos.get(chave)
        experiencia[chave] = valor if chave in aplicaveis and preenchido(valor) else None

    experiencia.update(
        {
            "slots_pendentes": pendentes,
            "slots_ignorados": desconhecidos,
            "slots_nao_aplicaveis": [
                s["chave"] for s in briefing["slots"] if not s["aplicavel"]
            ],
            "status": "adaptada" if experiencia["adaptada"] else "pendente_de_redacao",
            "briefing": briefing,
            "consumido_por": CONSUMIDORES,
            "observacoes": _observacoes(pendentes, desconhecidos, briefing),
            "lacunas": _lacunas(briefing),
        }
    )
    return experiencia


CONSUMIDORES = ["14", "15", "16", "17", "18", "19", "21", "22", "23", "24"]


def _observacoes(pendentes: list[str], desconhecidos: list[str], briefing: dict) -> list[str]:
    observacoes: list[str] = []
    if pendentes:
        observacoes.append(
            f"{len(pendentes)} bloco(s) sem redação. A explicação personalizada é "
            "conteúdo: exige redator conectado."
        )
    if desconhecidos:
        observacoes.append(
            "Blocos fora da estrutura foram descartados: " + ", ".join(desconhecidos)
        )
    if not briefing["sinais_de_confusao"]:
        observacoes.append(
            "Nenhum sinal de confusão medido: a adaptação seguiu apenas o nível "
            "de domínio e o estilo de aprendizagem."
        )
    if not briefing["nivel_de_dominio"]["classificacao_medida"]:
        observacoes.append(
            "Sem domínio medido para este conteúdo: o nível veio da estimativa da "
            "aula, com confiança menor."
        )
    if briefing["solicitacoes"]:
        observacoes.append(
            "Solicitações emitidas a outros agentes — este agente pede, não executa: "
            + "; ".join(f"{s['agente']}: {s['pedido']}" for s in briefing["solicitacoes"])
        )
    return observacoes


def _lacunas(briefing: dict) -> list[str]:
    lacunas: list[str] = []
    if not briefing["nivel_de_dominio"]["classificacao_medida"]:
        lacunas.append("dominio_medido_do_conteudo")
    if not briefing["teoria_de_referencia"]["aula"]["desenvolvimento"]:
        lacunas.append("aula_redigida_do_agente_07")
    return lacunas


# --------------------------------------------------------------------------- #
# Entrada principal
# --------------------------------------------------------------------------- #


@declara_confiabilidade
def adaptar(
    entradas: dict[str, Any],
    redator: Callable[[dict], dict] | None = None,
) -> dict[str, Any]:
    """Adapta a experiência de ensino do conteúdo solicitado."""
    briefing = montar_briefing(entradas)
    if briefing.get("bloqueio") or redator is None:
        return montar(briefing)
    return montar(briefing, redator(briefing))


__all__ = [
    "CHAVES_DE_SLOT",
    "ESTRATEGIA_POR_DIFICULDADE",
    "LIMIAR_ID_AVANCO",
    "LIMIAR_ID_REFORCO",
    "PreRequisitoPendente",
    "adaptar",
    "montar",
    "montar_briefing",
]
