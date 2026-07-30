"""Agente 08 — Example Generator.

Única responsabilidade: criar exemplos didáticos do conteúdo que o agente 07
ensinou. Não cria aulas, não cria cronogramas, não gera exercícios, flashcards
ou simulados, não avalia o estudante.

O portão deste agente é a **teoria**. A regra "nunca criar exemplos que
contradigam a teoria apresentada" só é verificável se a teoria existir: sem aula
redigida, não há o que não contradizer, e o agente não gera. É o mesmo raciocínio
do agente 07 com pré-requisitos — a diferença é o que está faltando.

Como no 07, a estrutura é código e a redação é do modelo: sem redator conectado,
os slots voltam ``None`` com o briefing pronto.
"""

from __future__ import annotations

from typing import Any, Callable

from app.studyos.agentes.comum import como_lista, preenchido

# --------------------------------------------------------------------------- #
# Estrutura declarada do conjunto de exemplos
# --------------------------------------------------------------------------- #

SLOTS: tuple[dict[str, Any], ...] = (
    {
        "chave": "exemplo_introdutorio",
        "nivel": "basico",
        "condicional": False,
        "instrucao": (
            "Exemplo mínimo, com o conceito isolado e nenhum detalhe supérfluo. "
            "É o primeiro contato: clareza acima de completude."
        ),
    },
    {
        "chave": "exemplo_pratico",
        "nivel": "intermediario",
        "condicional": False,
        "instrucao": (
            "Exemplo resolvido passo a passo, em situação típica do conteúdo, "
            "mostrando a aplicação do conceito do começo ao fim."
        ),
    },
    {
        "chave": "exemplo_avancado",
        "nivel": "avancado",
        "condicional": True,
        "instrucao": (
            "Caso com nuance ou exceção, do tipo que a prova cobra para separar "
            "quem decorou de quem entendeu."
        ),
    },
    {
        "chave": "exemplo_aplicado_ao_mundo_real",
        "nivel": "aplicado",
        "condicional": False,
        "instrucao": (
            "Situação do cotidiano ou do contexto do estudante em que o conceito "
            "aparece de verdade — não uma versão escolar disfarçada."
        ),
    },
    {
        "chave": "analogia",
        "nivel": "conceitual",
        "condicional": True,
        "instrucao": (
            "Analogia com algo familiar, explicitando onde ela vale e onde ela "
            "deixa de valer — analogia sem limite declarado vira erro futuro."
        ),
    },
    {
        "chave": "contraexemplo",
        "nivel": "diagnostico",
        "condicional": False,
        "instrucao": (
            "Caso que parece se encaixar no conceito mas não se encaixa, "
            "atacando diretamente os erros comuns listados na aula."
        ),
    },
)

CHAVES_DE_SLOT = tuple(slot["chave"] for slot in SLOTS)
CHAVES_OBRIGATORIAS = tuple(s["chave"] for s in SLOTS if not s["condicional"])

#: Dificuldades a partir das quais o exemplo avançado passa a ser aplicável.
DIFICULDADES_QUE_PEDEM_AVANCADO = ("dificil", "muito_dificil")

#: Níveis do estudante que tornam o exemplo avançado aplicável.
NIVEIS_QUE_PEDEM_AVANCADO = ("intermediario", "avancado")

#: Níveis do estudante para os quais a analogia é considerada útil.
NIVEIS_QUE_PEDEM_ANALOGIA = ("iniciante", "basico")


class TeoriaAusente(Exception):
    """Tentativa de montar exemplos sem a aula do agente 07 redigida."""


# --------------------------------------------------------------------------- #
# Portão: a teoria precisa existir
# --------------------------------------------------------------------------- #


def _portao(aula: dict) -> dict | None:
    if not aula:
        return {
            "motivo": "aula_ausente",
            "detalhe": "Nenhuma aula recebida do agente 07.",
            "acao": "Gerar a aula antes: o exemplo se ancora na teoria dela.",
        }

    status = aula.get("status")
    if status == "bloqueada_por_pre_requisito":
        return {
            "motivo": "aula_bloqueada_por_pre_requisito",
            "detalhe": (
                "A aula não foi gerada porque depende de: "
                + ", ".join(
                    (aula.get("bloqueio") or {}).get("pre_requisitos_pendentes", [])
                    or (aula.get("bloqueio") or {}).get("pendentes_por_ancestral", [])
                )
            ),
            "acao": "Estudar os pré-requisitos antes.",
        }
    if status != "gerada":
        return {
            "motivo": "teoria_nao_redigida",
            "detalhe": (
                "A aula existe em estrutura, mas as seções ainda não foram "
                "redigidas. Exemplo sem teoria não tem como não contradizê-la."
            ),
            "acao": "Conectar um redator ao agente 07 e gerar a aula.",
        }
    return None


def _aplicabilidade(aula: dict) -> dict[str, bool]:
    """Decide os slots condicionais — 'quando aplicável' e 'quando útil'."""
    dificuldade = aula.get("nivel_dificuldade")
    nivel = (aula.get("nivel_do_estudante") or {}).get("nivel")

    # Exemplo avançado exige base: para quem ainda não conhece o conteúdo, o
    # caso de exceção só atrapalha — "clareza em vez de complexidade" vale
    # inclusive quando o conteúdo em si é difícil. Sem nível medido, o agente
    # também não arrisca.
    tem_base = nivel in NIVEIS_QUE_PEDEM_AVANCADO
    return {
        "exemplo_avancado": tem_base
        or (nivel == "basico" and dificuldade in DIFICULDADES_QUE_PEDEM_AVANCADO),
        "analogia": (
            dificuldade in DIFICULDADES_QUE_PEDEM_AVANCADO
            or nivel in NIVEIS_QUE_PEDEM_ANALOGIA
        ),
    }


def _contexto_do_estudante(perfil: dict) -> dict:
    academico = perfil.get("perfil_academico") or {}
    return {
        "profissao": academico.get("profissao"),
        "idade": academico.get("idade"),
        "exame_alvo": academico.get("exame_alvo"),
        "estilo_de_aprendizagem": (
            perfil.get("estilo_aprendizagem") or {}
        ).get("predominante"),
        "uso": (
            "Ancorar o exemplo do mundo real no contexto do estudante quando isso "
            "tornar o conceito mais concreto — nunca forçando a conexão."
        ),
    }


# --------------------------------------------------------------------------- #
# Briefing e montagem
# --------------------------------------------------------------------------- #


def montar_briefing(entradas: dict[str, Any]) -> dict[str, Any]:
    """O que o redator precisa para exemplificar sem contradizer a aula."""
    anteriores = entradas.get("saidas_anteriores", {})
    perfil = anteriores.get("01", {}) or {}
    aula = anteriores.get("07", {}) or {}

    bloqueio = _portao(aula)
    if bloqueio:
        return {"aula": None, "bloqueio": bloqueio}

    aplicabilidade = _aplicabilidade(aula)
    slots = [
        {**slot, "aplicavel": aplicabilidade.get(slot["chave"], True)}
        for slot in SLOTS
    ]

    nivel = (aula.get("nivel_do_estudante") or {}).get("nivel")

    return {
        "aula": {
            "conteudo": aula.get("conteudo"),
            "titulo": aula.get("titulo"),
            "objetivo": aula.get("objetivo"),
            "nivel_dificuldade": aula.get("nivel_dificuldade"),
            "nivel_do_estudante": aula.get("nivel_do_estudante"),
        },
        "bloqueio": None,
        "conceito_abordado": aula.get("objetivo"),
        "teoria_de_referencia": {
            "desenvolvimento": aula.get("desenvolvimento"),
            "pontos_chave": como_lista(aula.get("pontos_chave")),
            "erros_comuns": aula.get("erros_comuns"),
            "regra": (
                "Todo exemplo deve ser consistente com este desenvolvimento. Em "
                "qualquer divergência, a teoria da aula prevalece."
            ),
        },
        "slots": slots,
        "slots_aplicaveis": [s["chave"] for s in slots if s["aplicavel"]],
        "diretrizes": _diretrizes(nivel, aula),
        "contexto_do_estudante": _contexto_do_estudante(perfil),
        "fontes": (aula.get("briefing") or {}).get("fontes"),
        "proibicoes": [
            "não criar aulas completas (agente 07)",
            "não criar exercícios nem questões (agente 09)",
            "não criar flashcards (agente 10)",
            "não criar simulados (agente 16)",
            "não avaliar o estudante (agentes 17, 18, 21)",
        ],
    }


def _diretrizes(nivel: str | None, aula: dict) -> list[str]:
    diretrizes = [
        f"Linguagem de nível {nivel or 'iniciante'}, igual à da aula.",
        "Clareza antes de complexidade: exemplo confuso não ensina nada.",
        "Cada exemplo vem acompanhado do porquê ele funciona.",
        "Progressão entre os exemplos: do isolado ao aplicado.",
    ]
    if preenchido(aula.get("erros_comuns")):
        diretrizes.append(
            "O contraexemplo deve atacar os erros comuns já listados na aula."
        )
    return diretrizes


def montar(
    briefing: dict[str, Any], exemplos: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Monta o conjunto — revalidando o portão da teoria."""
    bloqueio = briefing.get("bloqueio")
    if bloqueio and exemplos:
        raise TeoriaAusente(bloqueio["detalhe"])

    if bloqueio:
        return {
            "gerado": False,
            "bloqueio": bloqueio,
            "status": "bloqueado",
            "conceito_abordado": None,
            **{chave: None for chave in CHAVES_DE_SLOT},
            "observacoes_importantes": [],
            "briefing": None,
            "consumido_por": CONSUMIDORES,
            "observacoes": [f"Exemplos não gerados: {bloqueio['detalhe']}"],
            "lacunas": ["aula_do_agente_07"],
        }

    redigidos = dict(exemplos or {})
    observacoes_importantes = como_lista(redigidos.pop("observacoes_importantes", []))
    desconhecidos = sorted(set(redigidos) - set(CHAVES_DE_SLOT))

    aplicaveis = set(briefing["slots_aplicaveis"])
    obrigatorios = [c for c in CHAVES_OBRIGATORIAS if c in aplicaveis]
    faltantes = [
        chave for chave in obrigatorios if not preenchido(redigidos.get(chave))
    ]

    conjunto: dict[str, Any] = {
        "gerado": bool(exemplos) and not faltantes,
        "bloqueio": None,
        "conteudo": briefing["aula"]["conteudo"],
        "conceito_abordado": briefing["conceito_abordado"],
        "nivel_do_estudante": briefing["aula"]["nivel_do_estudante"],
    }

    for slot in briefing["slots"]:
        chave = slot["chave"]
        if not slot["aplicavel"]:
            conjunto[chave] = None
            continue
        conjunto[chave] = _normalizar(redigidos.get(chave), slot)

    conjunto.update(
        {
            "observacoes_importantes": observacoes_importantes,
            "slots_nao_aplicaveis": [
                s["chave"] for s in briefing["slots"] if not s["aplicavel"]
            ],
            "slots_pendentes": faltantes,
            "slots_ignorados": desconhecidos,
            "status": "gerado" if exemplos and not faltantes else "pendente_de_redacao",
            "briefing": briefing,
            "consumido_por": CONSUMIDORES,
            "observacoes": _observacoes(faltantes, desconhecidos, briefing),
            "lacunas": [],
        }
    )
    return conjunto


def _normalizar(valor: Any, slot: dict) -> dict | None:
    """Aceita texto puro ou `{enunciado, por_que_funciona}`."""
    if not preenchido(valor):
        return None
    if isinstance(valor, dict):
        enunciado = valor.get("enunciado") or valor.get("exemplo")
        porque = valor.get("por_que_funciona") or valor.get("explicacao")
    else:
        enunciado, porque = valor, None
    if not preenchido(enunciado):
        return None
    return {
        "nivel": slot["nivel"],
        "enunciado": enunciado,
        "por_que_funciona": porque,
    }


CONSUMIDORES = ["09", "10", "11", "13", "24"]


def _observacoes(faltantes: list[str], desconhecidos: list[str], briefing: dict) -> list[str]:
    observacoes: list[str] = []
    if faltantes:
        observacoes.append(
            f"{len(faltantes)} exemplo(s) sem redação. Exemplo é conteúdo: exige "
            "um redator conectado, não foi preenchido por invenção."
        )
    if desconhecidos:
        observacoes.append(
            "Itens fora da estrutura foram descartados: " + ", ".join(desconhecidos)
        )
    nao_aplicaveis = [s["chave"] for s in briefing["slots"] if not s["aplicavel"]]
    if nao_aplicaveis:
        observacoes.append(
            "Slots não aplicáveis a este conteúdo: " + ", ".join(nao_aplicaveis)
        )
    if not preenchido(briefing["teoria_de_referencia"]["erros_comuns"]):
        observacoes.append(
            "A aula não trouxe erros comuns: o contraexemplo não tem alvo "
            "declarado para atacar."
        )
    return observacoes


# --------------------------------------------------------------------------- #
# Entrada principal
# --------------------------------------------------------------------------- #


def gerar(
    entradas: dict[str, Any],
    redator: Callable[[dict], dict] | None = None,
) -> dict[str, Any]:
    """Gera o conjunto de exemplos do conteúdo ensinado pelo agente 07."""
    briefing = montar_briefing(entradas)
    if briefing.get("bloqueio") or redator is None:
        return montar(briefing)
    return montar(briefing, redator(briefing))


__all__ = [
    "CHAVES_DE_SLOT",
    "CHAVES_OBRIGATORIAS",
    "SLOTS",
    "TeoriaAusente",
    "gerar",
    "montar",
    "montar_briefing",
]
