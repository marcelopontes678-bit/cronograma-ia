"""Agente 09 — Exercise Generator.

Única responsabilidade: gerar exercícios do conteúdo já estudado. Não ensina
conteúdo novo, não cria cronogramas, não gera simulados completos, não avalia
desempenho histórico.

Aqui a fronteira entre código e modelo cai mais para o lado do código do que nos
agentes 07 e 08: **quantidade, distribuição por categoria, formato, cobertura
dos conceitos, pontuação e tempo são calculáveis** a partir do nível do
estudante e do tempo disponível. O modelo escreve o enunciado, a resposta e a
explicação — e nada entra no conjunto sem gabarito e explicação, porque isso é
regra, não preferência.
"""

from __future__ import annotations

from typing import Any, Callable

from app.studyos.agentes.comum import como_lista, como_numero, como_texto, preenchido

# --------------------------------------------------------------------------- #
# Categorias, formatos e custos declarados
# --------------------------------------------------------------------------- #

#: Categorias em ordem crescente de exigência cognitiva.
CATEGORIAS: tuple[str, ...] = (
    "fixacao",
    "compreensao",
    "aplicacao",
    "analise",
    "sintese",
    "desafio",
)

#: Minutos médios por questão e pontuação sugerida, por categoria.
CUSTO_MINUTOS: dict[str, float] = {
    "fixacao": 1.5,
    "compreensao": 2.0,
    "aplicacao": 3.0,
    "analise": 4.0,
    "sintese": 6.0,
    "desafio": 8.0,
}

PONTOS_POR_CATEGORIA: dict[str, int] = {
    "fixacao": 1,
    "compreensao": 1,
    "aplicacao": 2,
    "analise": 3,
    "sintese": 3,
    "desafio": 5,
}

#: Formatos adequados a cada categoria, na ordem de preferência.
FORMATOS_POR_CATEGORIA: dict[str, tuple[str, ...]] = {
    "fixacao": ("completar_lacunas", "verdadeiro_ou_falso", "associacao"),
    "compreensao": ("multipla_escolha", "resposta_curta", "verdadeiro_ou_falso"),
    "aplicacao": ("resolucao_de_problemas", "multipla_escolha"),
    "analise": ("estudo_de_caso", "questao_discursiva"),
    "sintese": ("questao_discursiva", "estudo_de_caso"),
    "desafio": ("resolucao_de_problemas", "estudo_de_caso"),
}

COMPETENCIA_POR_CATEGORIA: dict[str, str] = {
    "fixacao": "Recuperar o conceito da memória",
    "compreensao": "Explicar o conceito com as próprias palavras",
    "aplicacao": "Usar o conceito em uma situação nova",
    "analise": "Decompor um caso e identificar o que se aplica",
    "sintese": "Combinar conceitos em uma resposta própria",
    "desafio": "Resolver caso não rotineiro com o conceito",
}

#: Distribuição das categorias por nível do estudante — proporção do tempo.
#: Quem está começando não recebe desafio; quem domina não perde tempo com
#: fixação pura.
DISTRIBUICAO_POR_NIVEL: dict[str, dict[str, float]] = {
    "iniciante": {"fixacao": 0.5, "compreensao": 0.35, "aplicacao": 0.15},
    "basico": {"fixacao": 0.3, "compreensao": 0.35, "aplicacao": 0.25, "analise": 0.10},
    "intermediario": {
        "fixacao": 0.1,
        "compreensao": 0.2,
        "aplicacao": 0.35,
        "analise": 0.25,
        "sintese": 0.10,
    },
    "avancado": {
        "compreensao": 0.1,
        "aplicacao": 0.3,
        "analise": 0.3,
        "sintese": 0.15,
        "desafio": 0.15,
    },
}

#: Tempo padrão de uma bateria quando o Plano de Estudos não informa nada.
TEMPO_PADRAO_MIN = 30.0
#: Nenhuma bateria passa disso sem pedido explícito — exercício demais vira fadiga.
TEMPO_MAXIMO_MIN = 120.0
#: Mínimo de questões por categoria selecionada.
MINIMO_POR_CATEGORIA = 1

STATUS_ESTUDADO = ("concluido", "em_andamento")


class ConteudoNaoEstudado(Exception):
    """Tentativa de montar exercícios de conteúdo ainda não estudado."""


# --------------------------------------------------------------------------- #
# Portão: só se pratica o que já foi estudado
# --------------------------------------------------------------------------- #


def _no_do_grafo(grafo: dict, aula: dict, solicitado: Any) -> dict | None:
    nos = grafo.get("nos", [])
    alvo = como_texto(solicitado) if preenchido(solicitado) else None
    if alvo is None and aula.get("conteudo"):
        alvo = como_texto(aula["conteudo"]["nome"])
    if alvo is None:
        return None
    for no in nos:
        if no["id"] == solicitado or como_texto(no["nome"]) == alvo:
            return no
    return None


def _portao(
    aula: dict, no: dict | None, diagnostico: dict, grafo: dict | None = None
) -> dict | None:
    """Exercício exige conteúdo estudado — pela aula do 07 ou por estudo anterior."""
    aula_gerada = aula.get("status") == "gerada"
    ja_estudado = bool(no) and no.get("status_curricular") in STATUS_ESTUDADO

    if aula_gerada or ja_estudado:
        return None

    if no is not None and no.get("status") == "bloqueado":
        por_id = {n["id"]: n["nome"] for n in (grafo or {}).get("nos", [])}
        pendentes = [por_id.get(pre, pre) for pre in no.get("bloqueado_por", [])]
        return {
            "motivo": "conteudo_bloqueado",
            "detalhe": (
                "O conteúdo depende de pré-requisitos não concluídos: "
                + ", ".join(pendentes)
            ),
            "acao": "Estudar os pré-requisitos antes.",
        }

    if not aula and no is None:
        return {
            "motivo": "conteudo_ausente",
            "detalhe": "Nenhuma aula do agente 07 nem conteúdo identificado no grafo.",
            "acao": "Indicar o conteúdo ou gerar a aula.",
        }

    detalhe = (
        "A aula existe em estrutura, mas não foi redigida, e o conteúdo não "
        "consta como estudado."
        if aula
        else "O conteúdo ainda não foi estudado."
    )
    bloqueio = {
        "motivo": "conteudo_nao_estudado",
        "detalhe": detalhe,
        "acao": "Estudar o conteúdo antes de praticar.",
    }
    if diagnostico.get("necessaria"):
        # O agente 03 pediu medição justamente do que ainda não foi estudado.
        # A regra do 09 é mais forte que o pedido: a tensão fica registrada.
        bloqueio["pedido_de_diagnostico_pendente"] = {
            "origem": "03 Knowledge Analyzer",
            "observacao": (
                "Há pedido de avaliação diagnóstica sobre este conteúdo, mas a "
                "regra do agente 09 proíbe exercitar conteúdo não estudado. "
                "Resolver estudando o conteúdo ou registrando estudo anterior."
            ),
        }
    return bloqueio


# --------------------------------------------------------------------------- #
# Dimensionamento da bateria
# --------------------------------------------------------------------------- #


def _tempo_disponivel(campos: dict, plano: dict) -> tuple[float, str]:
    explicito = como_numero(campos.get("tempo_disponivel_min"))
    if explicito:
        return min(explicito, TEMPO_MAXIMO_MIN), "informado pelo usuário"

    for dia in plano.get("cronograma", []):
        for sessao in dia.get("sessoes", []):
            if sessao.get("tipo") == "exercicios":
                minutos = float(sessao["tempo_estimado_h"]) * 60
                return min(minutos, TEMPO_MAXIMO_MIN), "bloco de exercícios do agente 06"

    return TEMPO_PADRAO_MIN, "padrão (Plano de Estudos não informou bloco de exercícios)"


def _distribuir(nivel: str | None, minutos: float) -> list[dict]:
    """Converte tempo disponível em quantidade de questões por categoria."""
    distribuicao = DISTRIBUICAO_POR_NIVEL.get(nivel or "iniciante")

    plano: list[dict] = []
    for categoria in CATEGORIAS:
        fracao = distribuicao.get(categoria)
        if not fracao:
            continue
        minutos_da_categoria = minutos * fracao
        quantidade = max(
            MINIMO_POR_CATEGORIA, int(minutos_da_categoria // CUSTO_MINUTOS[categoria])
        )
        plano.append(
            {
                "categoria": categoria,
                "quantidade": quantidade,
                "minutos_estimados": round(quantidade * CUSTO_MINUTOS[categoria], 1),
            }
        )
    return plano


def _slots(distribuicao: list[dict], conceitos: list[str], erros: Any) -> list[dict]:
    """Um slot por questão, já com categoria, formato, conceito e pontuação."""
    slots: list[dict] = []
    numero = 1
    indice_conceito = 0

    for bloco in distribuicao:
        categoria = bloco["categoria"]
        formatos = FORMATOS_POR_CATEGORIA[categoria]
        for posicao in range(bloco["quantidade"]):
            conceito = (
                conceitos[indice_conceito % len(conceitos)] if conceitos else None
            )
            indice_conceito += 1
            slots.append(
                {
                    "numero": numero,
                    "categoria": categoria,
                    "ordem_dificuldade": CATEGORIAS.index(categoria) + 1,
                    "formato": formatos[posicao % len(formatos)],
                    "conceito_alvo": conceito,
                    "competencia": COMPETENCIA_POR_CATEGORIA[categoria],
                    "tempo_estimado_min": CUSTO_MINUTOS[categoria],
                    "pontos": PONTOS_POR_CATEGORIA[categoria],
                    "erro_comum_alvo": erros if preenchido(erros) else None,
                }
            )
            numero += 1
    return slots


# --------------------------------------------------------------------------- #
# Briefing e montagem
# --------------------------------------------------------------------------- #


def montar_briefing(entradas: dict[str, Any]) -> dict[str, Any]:
    dados = entradas.get("dados_usuario", {}) or {}
    campos = {k: v for k, v in dados.items() if k != "perfil"}
    if isinstance(dados.get("perfil"), dict):
        campos = {**campos, **dados["perfil"]}

    anteriores = entradas.get("saidas_anteriores", {})
    mapa_conhecimento = anteriores.get("03", {}) or {}
    grafo = anteriores.get("05", {}) or {}
    plano = anteriores.get("06", {}) or {}
    aula = anteriores.get("07", {}) or {}
    exemplos = anteriores.get("08", {}) or {}

    solicitado = campos.get("conteudo_solicitado")
    no = _no_do_grafo(grafo, aula, solicitado)
    diagnostico = mapa_conhecimento.get("avaliacao_diagnostica", {}) or {}

    bloqueio = _portao(aula, no, diagnostico, grafo)
    if bloqueio:
        return {"bloqueio": bloqueio, "conteudo": None}

    nivel = (aula.get("nivel_do_estudante") or {}).get("nivel")
    conceitos = como_lista(aula.get("pontos_chave"))
    minutos, origem_do_tempo = _tempo_disponivel(campos, plano)
    distribuicao = _distribuir(nivel, minutos)
    slots = _slots(distribuicao, conceitos, aula.get("erros_comuns"))

    conteudo = aula.get("conteudo") or (
        {"id": no["id"], "nome": no["nome"], "disciplina": no["disciplina"]}
        if no
        else None
    )

    return {
        "bloqueio": None,
        "conteudo": conteudo,
        "titulo_da_atividade": f"Exercícios — {conteudo['nome']}" if conteudo else "Exercícios",
        "objetivo": aula.get("objetivo"),
        "nivel_do_estudante": aula.get("nivel_do_estudante"),
        "nivel_de_dificuldade": aula.get("nivel_dificuldade"),
        "tempo_disponivel_min": round(minutos, 1),
        "origem_do_tempo": origem_do_tempo,
        "distribuicao": distribuicao,
        "slots": slots,
        "conceitos_a_cobrir": conceitos,
        "referencia": {
            "aula": {
                "desenvolvimento": aula.get("desenvolvimento"),
                "pontos_chave": conceitos,
                "erros_comuns": aula.get("erros_comuns"),
            },
            "exemplos": {
                chave: exemplos.get(chave)
                for chave in ("exemplo_pratico", "contraexemplo")
                if exemplos.get(chave)
            },
            "regra": (
                "Todo exercício deve ser respondível com o que a aula e os "
                "exemplos apresentaram. Em divergência, a aula prevalece."
            ),
        },
        "fontes": (aula.get("briefing") or {}).get("fontes"),
        "obrigatorio_por_questao": ["enunciado", "resposta", "explicacao"],
        "diretrizes": [
            f"Nível {nivel or 'iniciante'}: mesma linguagem da aula.",
            "Ordem crescente de dificuldade — os slots já vêm ordenados.",
            "Nenhuma questão pode ensinar conteúdo novo.",
            "Nenhum enunciado repetido dentro da bateria.",
            "Cada questão declara qual erro comum pretende detectar.",
        ],
        "proibicoes": [
            "não ensinar conteúdo novo (agente 07)",
            "não montar simulado completo (agente 16)",
            "não criar cronograma (agente 06)",
            "não avaliar desempenho histórico (agentes 17, 18, 21)",
        ],
    }


def montar(
    briefing: dict[str, Any], questoes: dict[Any, Any] | None = None
) -> dict[str, Any]:
    """Monta a bateria — recusando questão sem gabarito e sem explicação."""
    bloqueio = briefing.get("bloqueio")
    if bloqueio and questoes:
        raise ConteudoNaoEstudado(bloqueio["detalhe"])

    if bloqueio:
        return {
            "gerado": False,
            "bloqueio": bloqueio,
            "status": "bloqueado",
            "titulo_da_atividade": None,
            "exercicios": [],
            "gabarito": [],
            "cobertura_dos_conceitos": {},
            "pontuacao_sugerida": 0,
            "briefing": None,
            "consumido_por": CONSUMIDORES,
            "observacoes": [f"Exercícios não gerados: {bloqueio['detalhe']}"],
            "lacunas": ["conteudo_estudado"],
        }

    redigidas = _por_numero(questoes or {})
    exercicios: list[dict] = []
    gabarito: list[dict] = []
    invalidas: list[dict] = []
    duplicadas: list[dict] = []
    pendentes: list[int] = []
    vistos: dict[str, int] = {}

    for slot in briefing["slots"]:
        bruta = redigidas.get(slot["numero"])
        if not preenchido(bruta):
            pendentes.append(slot["numero"])
            continue

        problema = _validar(bruta)
        if problema:
            invalidas.append({"numero": slot["numero"], "motivo": problema})
            continue

        chave = como_texto(bruta["enunciado"])
        if chave in vistos:
            duplicadas.append(
                {
                    "numero": slot["numero"],
                    "igual_a": vistos[chave],
                    "motivo": "enunciado repetido na bateria",
                }
            )
            continue
        vistos[chave] = slot["numero"]

        exercicios.append(
            {
                "numero": slot["numero"],
                "categoria": slot["categoria"],
                "ordem_dificuldade": slot["ordem_dificuldade"],
                "formato": slot["formato"],
                "enunciado": bruta["enunciado"],
                "alternativas": bruta.get("alternativas"),
                "conceito_alvo": slot["conceito_alvo"],
                "competencia_avaliada": slot["competencia"],
                "tempo_estimado_min": slot["tempo_estimado_min"],
                "pontos": slot["pontos"],
            }
        )
        gabarito.append(
            {
                "numero": slot["numero"],
                "resposta": bruta["resposta"],
                "explicacao": bruta["explicacao"],
                "competencia_avaliada": slot["competencia"],
                "erro_comum_associado": bruta.get("erro_comum_alvo")
                or slot["erro_comum_alvo"],
                "pontos": slot["pontos"],
            }
        )

    cobertura = _cobertura(briefing["conceitos_a_cobrir"], exercicios)
    completa = bool(questoes) and not pendentes and not invalidas

    return {
        "gerado": completa,
        "bloqueio": None,
        "conteudo": briefing["conteudo"],
        "titulo_da_atividade": briefing["titulo_da_atividade"],
        "objetivo": briefing["objetivo"],
        "nivel_de_dificuldade": briefing["nivel_de_dificuldade"],
        "nivel_do_estudante": briefing["nivel_do_estudante"],
        "tempo_estimado_min": round(
            sum(e["tempo_estimado_min"] for e in exercicios), 1
        ),
        "tempo_disponivel_min": briefing["tempo_disponivel_min"],
        "distribuicao_por_categoria": briefing["distribuicao"],
        "exercicios": exercicios,
        "gabarito": gabarito,
        "pontuacao_sugerida": sum(e["pontos"] for e in exercicios),
        "cobertura_dos_conceitos": cobertura,
        "questoes_pendentes": pendentes,
        "questoes_invalidas": invalidas,
        "questoes_duplicadas": duplicadas,
        "status": "gerado" if completa else "pendente_de_redacao",
        "briefing": briefing,
        "consumido_por": CONSUMIDORES,
        "observacoes": _observacoes(pendentes, invalidas, duplicadas, cobertura),
        "lacunas": [] if briefing["conceitos_a_cobrir"] else ["pontos_chave_da_aula"],
    }


def _por_numero(questoes: dict) -> dict[int, dict]:
    normalizadas: dict[int, dict] = {}
    for chave, valor in questoes.items():
        numero = como_numero(chave)
        if numero is not None and isinstance(valor, dict):
            normalizadas[int(numero)] = valor
    return normalizadas


def _validar(questao: dict) -> str | None:
    if not preenchido(questao.get("enunciado")):
        return "sem enunciado"
    if not preenchido(questao.get("resposta")):
        return "sem gabarito"
    if not preenchido(questao.get("explicacao")):
        return "sem explicação da resposta"
    return None


def _cobertura(conceitos: list[str], exercicios: list[dict]) -> dict:
    if not conceitos:
        return {"conceitos": [], "cobertos": [], "descobertos": [], "completa": False}

    cobertos = {
        e["conceito_alvo"] for e in exercicios if preenchido(e["conceito_alvo"])
    }
    descobertos = [c for c in conceitos if c not in cobertos]
    return {
        "conceitos": conceitos,
        "cobertos": sorted(cobertos),
        "descobertos": descobertos,
        "completa": not descobertos,
    }


CONSUMIDORES = ["10", "11", "13", "16", "17", "18", "21", "24"]


def _observacoes(
    pendentes: list[int], invalidas: list[dict], duplicadas: list[dict], cobertura: dict
) -> list[str]:
    observacoes: list[str] = []
    if pendentes:
        observacoes.append(
            f"{len(pendentes)} questão(ões) sem redação. Enunciado é conteúdo: "
            "exige redator conectado, não foi preenchido por invenção."
        )
    if invalidas:
        motivos = ", ".join(f"#{i['numero']} ({i['motivo']})" for i in invalidas)
        observacoes.append(
            f"{len(invalidas)} questão(ões) recusada(s) — gabarito e explicação "
            f"são obrigatórios: {motivos}"
        )
    if duplicadas:
        observacoes.append(
            f"{len(duplicadas)} questão(ões) descartada(s) por enunciado repetido."
        )
    if cobertura["conceitos"] and not cobertura["completa"]:
        observacoes.append(
            "Conceitos sem exercício: " + ", ".join(cobertura["descobertos"])
        )
    if not cobertura["conceitos"]:
        observacoes.append(
            "A aula não trouxe pontos-chave: não há como verificar cobertura de "
            "conceitos nesta bateria."
        )
    return observacoes


# --------------------------------------------------------------------------- #
# Entrada principal
# --------------------------------------------------------------------------- #


def gerar(
    entradas: dict[str, Any],
    redator: Callable[[dict], dict] | None = None,
) -> dict[str, Any]:
    """Gera a bateria de exercícios do conteúdo estudado."""
    briefing = montar_briefing(entradas)
    if briefing.get("bloqueio") or redator is None:
        return montar(briefing)
    return montar(briefing, redator(briefing))


__all__ = [
    "CATEGORIAS",
    "ConteudoNaoEstudado",
    "DISTRIBUICAO_POR_NIVEL",
    "gerar",
    "montar",
    "montar_briefing",
]
