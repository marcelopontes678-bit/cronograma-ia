"""Agente 10 — Flashcard Generator.

Única responsabilidade: converter conteúdo estudado em flashcards de recuperação
ativa. Não ensina conteúdo novo, não cria cronogramas, não gera simulados, não
avalia desempenho.

Três regras da spec são verificáveis por código e viram recusa, não conselho:

* **uma ideia por cartão** — resposta acima do limite de palavras ou com marcas
  de enumeração é recusada;
* **recuperação ativa** — pergunta que não pergunta (nem lacuna, nem V/F, nem
  associação) é recusada;
* **nada sobre conteúdo não estudado** — mesmo portão do agente 09.

O resto — dificuldade, prioridade, tempo de resposta, tags, localização na
árvore e marcação de revisão frequente — é calculado. Ao modelo cabe a pergunta
e a resposta.
"""

from __future__ import annotations

from typing import Any, Callable

from app.studyos.agentes.comum import como_lista, como_texto, preenchido
from app.studyos.agentes.portoes import conteudo_estudado, localizar_no

# --------------------------------------------------------------------------- #
# Constantes declaradas
# --------------------------------------------------------------------------- #

#: Formatos de cartão e segundos médios de resposta.
TIPOS: tuple[str, ...] = (
    "conceito_definicao",
    "pergunta_resposta",
    "cloze",
    "verdadeiro_ou_falso",
    "termo_explicacao",
    "associacao",
    "sequencia_logica",
)

SEGUNDOS_POR_TIPO: dict[str, int] = {
    "cloze": 8,
    "verdadeiro_ou_falso": 6,
    "conceito_definicao": 12,
    "termo_explicacao": 15,
    "pergunta_resposta": 15,
    "associacao": 20,
    "sequencia_logica": 25,
}

#: Tipos que já são de recuperação ativa por construção — não precisam de "?".
TIPOS_SEM_INTERROGACAO = ("cloze", "verdadeiro_ou_falso", "associacao", "sequencia_logica")

#: Marcador de lacuna aceito no cloze.
MARCADOR_CLOZE = "___"

#: Acima disso, a resposta provavelmente carrega mais de uma ideia.
MAXIMO_PALAVRAS_RESPOSTA = 25

#: Marcas de enumeração que denunciam mais de um conceito no mesmo cartão.
MARCAS_DE_ENUMERACAO = (";", " e também ", " além disso", " por outro lado")

DIFICULDADE_POR_DOMINIO: dict[str, str] = {
    "avancado": "facil",
    "intermediario": "facil",
    "basico": "medio",
    "nao_conhece": "dificil",
    "indeterminado": "medio",
}

PRIORIDADE_POR_IMPORTANCIA: dict[str, str] = {
    "essencial": "alta",
    "alta": "alta",
    "media": "media",
    "baixa": "baixa",
}


class ConteudoNaoEstudado(Exception):
    """Tentativa de montar flashcards de conteúdo ainda não estudado."""


# --------------------------------------------------------------------------- #
# Localização na árvore
# --------------------------------------------------------------------------- #


def _localizacao(no: dict | None, grafo: dict) -> dict:
    """Disciplina, módulo, tópico e subtópico do nó, subindo pela contenção."""
    vazio = {"disciplina": None, "modulo": None, "topico": None, "subtopico": None}
    if no is None:
        return vazio

    por_id = {n["id"]: n for n in grafo.get("nos", [])}
    localizacao = dict(vazio)
    atual: dict | None = no
    while atual is not None:
        if atual["tipo"] in localizacao and localizacao[atual["tipo"]] is None:
            localizacao[atual["tipo"]] = atual["nome"]
        atual = por_id.get(atual.get("contido_em"))

    localizacao["disciplina"] = localizacao["disciplina"] or no.get("disciplina")
    return localizacao


def _classificacao_do_topico(mapa_conhecimento: dict, no: dict | None) -> dict:
    if no is None:
        return {}
    alvo = como_texto(no["nome"])
    for disciplina in mapa_conhecimento.get("disciplinas", []):
        for topico in disciplina.get("topicos", []):
            if como_texto(topico["topico"]) == alvo:
                return topico
    return {}


# --------------------------------------------------------------------------- #
# Slots
# --------------------------------------------------------------------------- #


def _conceitos(aula: dict, exercicios: dict) -> list[str]:
    """Conceitos essenciais: pontos-chave da aula, reforçados pelos exercícios."""
    conceitos = como_lista(aula.get("pontos_chave"))
    vistos = {como_texto(c) for c in conceitos}
    for exercicio in exercicios.get("exercicios", []):
        alvo = exercicio.get("conceito_alvo")
        if preenchido(alvo) and como_texto(alvo) not in vistos:
            conceitos.append(alvo)
            vistos.add(como_texto(alvo))
    return conceitos


def _slots(
    conceitos: list[str],
    localizacao: dict,
    dificuldade: str,
    prioridade: str,
    revisao_frequente: bool,
    identificador_base: str,
) -> list[dict]:
    slots: list[dict] = []
    for indice, conceito in enumerate(conceitos, start=1):
        tipo = TIPOS[(indice - 1) % len(TIPOS)]
        slots.append(
            {
                "id": f"fc-{identificador_base}-{indice:02d}",
                "numero": indice,
                "conceito": conceito,
                "tipo": tipo,
                "dificuldade": dificuldade,
                "prioridade": prioridade,
                "revisao_frequente": revisao_frequente,
                "tempo_medio_resposta_s": SEGUNDOS_POR_TIPO[tipo],
                "tags": _tags(localizacao, conceito, tipo),
                "instrucao": _instrucao(tipo, conceito),
                **localizacao,
            }
        )
    return slots


def _tags(localizacao: dict, conceito: str, tipo: str) -> list[str]:
    tags = [v for v in localizacao.values() if preenchido(v)]
    tags.append(tipo)
    tags.append(conceito)
    return tags


def _instrucao(tipo: str, conceito: str) -> str:
    instrucoes = {
        "conceito_definicao": f"Frente com o conceito '{conceito}', verso com a definição enxuta.",
        "pergunta_resposta": f"Pergunta direta sobre '{conceito}', respondível de memória em uma frase.",
        "cloze": f"Frase sobre '{conceito}' com a informação central substituída por {MARCADOR_CLOZE}.",
        "verdadeiro_ou_falso": f"Afirmação sobre '{conceito}' que force decisão, sem pegadinha gratuita.",
        "termo_explicacao": f"Termo técnico de '{conceito}' na frente, explicação curta no verso.",
        "associacao": f"Dois conjuntos ligados a '{conceito}' para o estudante parear.",
        "sequencia_logica": f"Etapas de '{conceito}' fora de ordem, para o estudante ordenar.",
    }
    return instrucoes[tipo]


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
    aula = anteriores.get("07", {}) or {}
    exemplos = anteriores.get("08", {}) or {}
    exercicios = anteriores.get("09", {}) or {}

    no = localizar_no(grafo, aula, campos.get("conteudo_solicitado"))
    bloqueio = conteudo_estudado(aula, no, grafo)
    if bloqueio:
        return {"bloqueio": bloqueio, "conteudo": None, "slots": []}

    localizacao = _localizacao(no, grafo)
    medicao = _classificacao_do_topico(mapa_conhecimento, no)

    dificuldade = DIFICULDADE_POR_DOMINIO.get(
        medicao.get("classificacao", "indeterminado"), "medio"
    )
    prioridade = PRIORIDADE_POR_IMPORTANCIA.get(
        (no or {}).get("importancia") or "media", "media"
    )
    # Cartão difícil, prioritário ou de conteúdo já esquecido precisa voltar
    # mais vezes — é esta marca que o agente 14 consome.
    revisao_frequente = (
        dificuldade == "dificil" or prioridade == "alta" or bool(medicao.get("esquecido"))
    )

    conceitos = _conceitos(aula, exercicios)
    identificador = (no or {}).get("id", "sem-no").replace(".", "-")
    slots = _slots(
        conceitos, localizacao, dificuldade, prioridade, revisao_frequente, identificador
    )

    conteudo = aula.get("conteudo") or (
        {"id": no["id"], "nome": no["nome"], "disciplina": no["disciplina"]}
        if no
        else None
    )

    return {
        "bloqueio": None,
        "conteudo": conteudo,
        "localizacao": localizacao,
        "conceitos_essenciais": conceitos,
        "slots": slots,
        "dificuldade": dificuldade,
        "prioridade": prioridade,
        "revisao_frequente": revisao_frequente,
        "referencia": {
            "aula": {
                "desenvolvimento": aula.get("desenvolvimento"),
                "pontos_chave": como_lista(aula.get("pontos_chave")),
                "erros_comuns": aula.get("erros_comuns"),
            },
            "exemplos": {
                chave: exemplos.get(chave)
                for chave in ("exemplo_pratico", "contraexemplo")
                if exemplos.get(chave)
            },
            "regra": (
                "O flashcard resume o que a aula ensinou. Ele não substitui a "
                "aula nem introduz conteúdo que ela não trouxe."
            ),
        },
        "categorias_a_extrair": [
            "definições", "fórmulas", "datas", "regras", "processos",
            "exceções", "palavras-chave",
        ],
        "limites": {
            "maximo_palavras_resposta": MAXIMO_PALAVRAS_RESPOSTA,
            "uma_ideia_por_cartao": True,
            "marcador_cloze": MARCADOR_CLOZE,
        },
        "diretrizes": [
            "Uma única ideia por cartão — se precisar de 'e', são dois cartões.",
            f"Resposta em até {MAXIMO_PALAVRAS_RESPOSTA} palavras.",
            "A frente precisa exigir recuperação ativa, não reconhecimento.",
            "Linguagem clara e objetiva, sem rodeio.",
        ],
        "proibicoes": [
            "não ensinar conteúdo novo (agente 07)",
            "não substituir a aula pelo flashcard",
            "não criar cronograma (agentes 06, 14, 15)",
            "não gerar simulados (agente 16)",
            "não avaliar desempenho (agentes 17, 18, 21)",
        ],
    }


def montar(
    briefing: dict[str, Any], cartoes: dict[Any, Any] | None = None
) -> dict[str, Any]:
    """Monta o baralho — recusando cartão com mais de uma ideia ou sem recall."""
    bloqueio = briefing.get("bloqueio")
    if bloqueio and cartoes:
        raise ConteudoNaoEstudado(bloqueio["detalhe"])

    if bloqueio:
        return {
            "gerado": False,
            "bloqueio": bloqueio,
            "status": "bloqueado",
            "flashcards": [],
            "resumo": _resumo([], []),
            "briefing": None,
            "consumido_por": CONSUMIDORES,
            "observacoes": [f"Flashcards não gerados: {bloqueio['detalhe']}"],
            "lacunas": ["conteudo_estudado"],
        }

    redigidos = _por_numero(cartoes or {})
    flashcards: list[dict] = []
    invalidos: list[dict] = []
    duplicados: list[dict] = []
    pendentes: list[int] = []
    vistos: dict[str, int] = {}

    for slot in briefing["slots"]:
        bruto = redigidos.get(slot["numero"])
        if not preenchido(bruto):
            pendentes.append(slot["numero"])
            continue

        problema = _validar(bruto, slot)
        if problema:
            invalidos.append(
                {"numero": slot["numero"], "id": slot["id"], "motivo": problema}
            )
            continue

        chave = como_texto(bruto["pergunta"])
        if chave in vistos:
            duplicados.append(
                {
                    "numero": slot["numero"],
                    "igual_a": vistos[chave],
                    "motivo": "pergunta repetida no baralho",
                }
            )
            continue
        vistos[chave] = slot["numero"]

        flashcards.append(
            {
                "id": slot["id"],
                "disciplina": slot["disciplina"],
                "modulo": slot["modulo"],
                "topico": slot["topico"],
                "subtopico": slot["subtopico"],
                "tipo": slot["tipo"],
                "pergunta": bruto["pergunta"],
                "resposta": bruto["resposta"],
                "explicacao_complementar": bruto.get("explicacao_complementar"),
                "conceito": slot["conceito"],
                "nivel_dificuldade": slot["dificuldade"],
                "prioridade": slot["prioridade"],
                "revisao_frequente": slot["revisao_frequente"],
                "tempo_medio_resposta_s": slot["tempo_medio_resposta_s"],
                "tags": slot["tags"],
            }
        )

    completo = bool(cartoes) and not pendentes and not invalidos

    return {
        "gerado": completo,
        "bloqueio": None,
        "conteudo": briefing["conteudo"],
        "flashcards": flashcards,
        "resumo": _resumo(flashcards, briefing["conceitos_essenciais"]),
        "cartoes_pendentes": pendentes,
        "cartoes_invalidos": invalidos,
        "cartoes_duplicados": duplicados,
        "status": "gerado" if completo else "pendente_de_redacao",
        "briefing": briefing,
        "consumido_por": CONSUMIDORES,
        "observacoes": _observacoes(
            pendentes, invalidos, duplicados, flashcards, briefing
        ),
        "lacunas": [] if briefing["conceitos_essenciais"] else ["pontos_chave_da_aula"],
    }


def _por_numero(cartoes: dict) -> dict[int, dict]:
    normalizados: dict[int, dict] = {}
    for chave, valor in cartoes.items():
        try:
            numero = int(chave)
        except (TypeError, ValueError):
            continue
        if isinstance(valor, dict):
            normalizados[numero] = valor
    return normalizados


def _validar(cartao: dict, slot: dict) -> str | None:
    pergunta = cartao.get("pergunta")
    resposta = cartao.get("resposta")

    if not preenchido(pergunta):
        return "sem pergunta"
    if not preenchido(resposta):
        return "sem resposta"

    if not _estimula_recall(str(pergunta), slot["tipo"]):
        return (
            "a frente não exige recuperação ativa: não é pergunta, lacuna, "
            "afirmação a julgar nem tarefa de ordenar/parear"
        )

    palavras = len(str(resposta).split())
    if palavras > MAXIMO_PALAVRAS_RESPOSTA:
        return (
            f"resposta com {palavras} palavras (limite {MAXIMO_PALAVRAS_RESPOSTA}): "
            "provável mais de uma ideia no cartão"
        )

    texto = f" {como_texto(resposta)} "
    for marca in MARCAS_DE_ENUMERACAO:
        if como_texto(marca).strip() and como_texto(marca) in texto:
            return f"resposta enumera mais de um conceito (marca: '{marca.strip()}')"

    if slot["tipo"] == "cloze" and MARCADOR_CLOZE not in str(pergunta):
        return f"cloze sem lacuna: falta o marcador {MARCADOR_CLOZE}"

    return None


def _estimula_recall(pergunta: str, tipo: str) -> bool:
    if tipo in TIPOS_SEM_INTERROGACAO:
        return True
    return pergunta.strip().endswith("?") or MARCADOR_CLOZE in pergunta


def _resumo(flashcards: list[dict], conceitos: list[str]) -> dict:
    por_dificuldade: dict[str, int] = {}
    por_disciplina: dict[str, int] = {}
    for cartao in flashcards:
        por_dificuldade[cartao["nivel_dificuldade"]] = (
            por_dificuldade.get(cartao["nivel_dificuldade"], 0) + 1
        )
        chave = cartao["disciplina"] or "sem disciplina"
        por_disciplina[chave] = por_disciplina.get(chave, 0) + 1

    cobertos = {c["conceito"] for c in flashcards if preenchido(c["conceito"])}
    return {
        "total": len(flashcards),
        "distribuicao_por_dificuldade": por_dificuldade,
        "distribuicao_por_disciplina": por_disciplina,
        "conceitos_cobertos": sorted(cobertos),
        "conceitos_descobertos": [c for c in conceitos if c not in cobertos],
        "marcados_para_revisao_frequente": sum(
            1 for c in flashcards if c["revisao_frequente"]
        ),
        "tempo_total_estimado_s": sum(
            c["tempo_medio_resposta_s"] for c in flashcards
        ),
    }


CONSUMIDORES = ["11", "13", "14", "15", "17", "18", "21", "24"]


def _observacoes(
    pendentes: list[int],
    invalidos: list[dict],
    duplicados: list[dict],
    flashcards: list[dict],
    briefing: dict,
) -> list[str]:
    observacoes: list[str] = []
    if pendentes:
        observacoes.append(
            f"{len(pendentes)} cartão(ões) sem redação. Pergunta e resposta são "
            "conteúdo: exigem redator conectado, não foram inventados."
        )
    if invalidos:
        motivos = ", ".join(f"#{i['numero']} ({i['motivo']})" for i in invalidos)
        observacoes.append(f"{len(invalidos)} cartão(ões) recusado(s): {motivos}")
    if duplicados:
        observacoes.append(
            f"{len(duplicados)} cartão(ões) descartado(s) por pergunta repetida."
        )
    if not briefing["conceitos_essenciais"]:
        observacoes.append(
            "A aula não trouxe pontos-chave e os exercícios não indicaram "
            "conceitos: não há do que extrair flashcards."
        )
    if flashcards and briefing["revisao_frequente"]:
        observacoes.append(
            "Baralho marcado para revisão frequente — o agente 14 Memory "
            "Scheduler define os intervalos."
        )
    return observacoes


# --------------------------------------------------------------------------- #
# Entrada principal
# --------------------------------------------------------------------------- #


def gerar(
    entradas: dict[str, Any],
    redator: Callable[[dict], dict] | None = None,
) -> dict[str, Any]:
    """Gera o baralho de flashcards do conteúdo estudado."""
    briefing = montar_briefing(entradas)
    if briefing.get("bloqueio") or redator is None:
        return montar(briefing)
    return montar(briefing, redator(briefing))


__all__ = [
    "MAXIMO_PALAVRAS_RESPOSTA",
    "TIPOS",
    "ConteudoNaoEstudado",
    "gerar",
    "montar",
    "montar_briefing",
]
