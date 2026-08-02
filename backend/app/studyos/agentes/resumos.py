"""Agente 11 — Summary Generator.

Única responsabilidade: sintetizar conteúdo estudado em resumos de revisão. Não
ensina conteúdo novo, não cria cronogramas, não gera exercícios ou simulados,
não avalia desempenho.

Duas regras da spec são verificáveis e viram recusa:

* **"Resumo de 1 minuto"** que não cabe em um minuto não é resumo de um minuto.
  O limite sai da velocidade de leitura declarada e é conferido por contagem de
  palavras.
* **"Nunca remover conceitos essenciais"** — cada conceito-chave precisa
  aparecer no resumo completo; o que sumir é listado.

Mapa mental, checklist de revisão, conceitos-chave, erros comuns e próximos
conteúdos são **derivados** das saídas anteriores, não redigidos: a estrutura já
existe na Árvore Curricular e no Grafo, e os erros comuns já foram escritos pela
aula. Copiar em vez de regerar é o que mantém a consistência com o original.
"""

from __future__ import annotations

from typing import Any, Callable

from app.studyos.agentes.comum import como_lista, como_texto, preenchido
from app.studyos.agentes.comum import declara_confiabilidade
from app.studyos.agentes.portoes import conteudo_estudado, localizar_no

# --------------------------------------------------------------------------- #
# Constantes declaradas
# --------------------------------------------------------------------------- #

#: Velocidade de leitura usada para converter minutos em palavras.
PALAVRAS_POR_MINUTO = 200

#: Folga aceita sobre o limite antes de recusar — o corte não é ao milímetro.
TOLERANCIA_DE_TAMANHO = 1.15

#: Orçamento de palavras de cada nível de resumo.
LIMITES_DE_PALAVRAS: dict[str, int] = {
    "resumo_1min": int(1 * PALAVRAS_POR_MINUTO * TOLERANCIA_DE_TAMANHO),
    "resumo_5min": int(5 * PALAVRAS_POR_MINUTO * TOLERANCIA_DE_TAMANHO),
}

#: Termos que indicam que o conteúdo tem fórmulas a destacar.
MARCAS_DE_FORMULA = ("formula", "equacao", "=", "teorema", "calculo", "%")

SECOES: tuple[dict[str, Any], ...] = (
    {
        "chave": "resumo_1min",
        "condicional": False,
        "limite_palavras": LIMITES_DE_PALAVRAS["resumo_1min"],
        "instrucao": (
            "O essencial absoluto: se o estudante só ler isto na véspera, o que "
            "ele não pode ter deixado de ver."
        ),
    },
    {
        "chave": "resumo_5min",
        "condicional": False,
        "limite_palavras": LIMITES_DE_PALAVRAS["resumo_5min"],
        "instrucao": (
            "Revisão de verdade: conceitos centrais com o encadeamento entre "
            "eles, na mesma ordem lógica da aula."
        ),
    },
    {
        "chave": "resumo_completo",
        "condicional": False,
        "limite_palavras": None,
        "instrucao": (
            "Síntese integral do que a aula ensinou, sem redundância e sem "
            "acrescentar nada que ela não trouxe. Todos os conceitos-chave "
            "precisam aparecer."
        ),
    },
    {
        "chave": "definicoes_importantes",
        "condicional": False,
        "limite_palavras": None,
        "instrucao": "Lista de termo → definição enxuta, tal como a aula definiu.",
    },
    {
        "chave": "formulas",
        "condicional": True,
        "limite_palavras": None,
        "instrucao": "Fórmulas com o significado de cada símbolo e quando aplicar.",
    },
    {
        "chave": "processos_passo_a_passo",
        "condicional": False,
        "limite_palavras": None,
        "instrucao": "Procedimentos em etapas numeradas, na ordem de execução.",
    },
    {
        "chave": "armadilhas_frequentes",
        "condicional": False,
        "limite_palavras": None,
        "instrucao": (
            "O que costuma derrubar o estudante na hora da prova — a partir dos "
            "erros comuns da aula e do contraexemplo dos exemplos."
        ),
    },
)

CHAVES_DE_SECAO = tuple(secao["chave"] for secao in SECOES)


class ConteudoNaoEstudado(Exception):
    """Tentativa de montar resumo de conteúdo ainda não estudado."""


# --------------------------------------------------------------------------- #
# Material derivado (sem redator)
# --------------------------------------------------------------------------- #


def _conceitos(aula: dict, flashcards: dict, exercicios: dict) -> list[str]:
    conceitos = como_lista(aula.get("pontos_chave"))
    vistos = {como_texto(c) for c in conceitos}
    for origem in (
        (c.get("conceito") for c in flashcards.get("flashcards", [])),
        (e.get("conceito_alvo") for e in exercicios.get("exercicios", [])),
    ):
        for conceito in origem:
            if preenchido(conceito) and como_texto(conceito) not in vistos:
                conceitos.append(conceito)
                vistos.add(como_texto(conceito))
    return conceitos


def _mapa_mental(arvore: dict, no: dict | None, conceitos: list[str]) -> str:
    """Estrutura em texto — vem da Árvore Curricular, não da imaginação."""
    if no is None:
        return ""

    alvo = como_texto(no["nome"])
    linhas: list[str] = []
    for disciplina in arvore.get("disciplinas", []):
        for modulo in disciplina.get("modulos", []):
            for topico in modulo.get("topicos", []):
                if como_texto(topico["nome"]) != alvo and not any(
                    como_texto(s["nome"]) == alvo for s in topico.get("subtopicos", [])
                ):
                    continue
                linhas.append(disciplina["nome"])
                linhas.append(f"└── {modulo['nome']}")
                linhas.append(f"    └── {topico['nome']}")
                for subtopico in topico.get("subtopicos", []):
                    marca = "◀" if como_texto(subtopico["nome"]) == alvo else " "
                    linhas.append(f"        ├── {subtopico['nome']} {marca}".rstrip())
                    for micro in subtopico.get("microtopicos", []):
                        linhas.append(f"        │   ├── {micro['nome']}")
                for conceito in conceitos:
                    linhas.append(f"        • {conceito}")
                return "\n".join(linhas)
    return ""


def _checklist(conceitos: list[str], flashcards: dict) -> list[dict]:
    """Uma pergunta de autoverificação por conceito — derivada, não inventada."""
    checklist = [
        {
            "item": f"Consigo explicar '{conceito}' sem consultar o material?",
            "conceito": conceito,
        }
        for conceito in conceitos
    ]
    frequentes = [
        c["conceito"]
        for c in flashcards.get("flashcards", [])
        if c.get("revisao_frequente")
    ]
    for item in checklist:
        item["revisao_frequente"] = item["conceito"] in frequentes
    return checklist


def _erros_comuns(aula: dict, exemplos: dict, exercicios: dict) -> dict:
    """Copiados da aula e dos exemplos — regerar arriscaria contradizê-los."""
    do_gabarito = sorted(
        {
            item["erro_comum_associado"]
            for item in exercicios.get("gabarito", [])
            if preenchido(item.get("erro_comum_associado"))
        }
    )
    return {
        "da_aula": aula.get("erros_comuns"),
        "contraexemplo": (exemplos.get("contraexemplo") or {}).get("enunciado"),
        "detectados_pelos_exercicios": do_gabarito,
        "origem": "copiados da aula, dos exemplos e do gabarito, sem reescrita",
    }


def _proximos(grafo: dict, no: dict | None) -> list[dict]:
    if no is None:
        return []
    por_id = {n["id"]: n for n in grafo.get("nos", [])}
    proximos = [
        {"id": identificador, "nome": por_id[identificador]["nome"], "relacao": "depende deste"}
        for identificador in no.get("dependentes", [])
        if identificador in por_id
    ]
    sequencia = grafo.get("sequencia_logica", [])
    for indice, item in enumerate(sequencia):
        if item["id"] == no["id"] and indice + 1 < len(sequencia):
            seguinte = sequencia[indice + 1]
            if all(p["id"] != seguinte["id"] for p in proximos):
                proximos.append(
                    {
                        "id": seguinte["id"],
                        "nome": seguinte["nome"],
                        "relacao": "próximo na sequência de estudo",
                    }
                )
    return proximos


def _tem_formula(aula: dict, conceitos: list[str]) -> bool:
    texto = como_texto(
        " ".join(
            [
                str(aula.get("desenvolvimento") or ""),
                str(aula.get("resumo") or ""),
                " ".join(conceitos),
            ]
        )
    )
    return any(marca in texto for marca in MARCAS_DE_FORMULA)


# --------------------------------------------------------------------------- #
# Briefing e montagem
# --------------------------------------------------------------------------- #


def montar_briefing(entradas: dict[str, Any]) -> dict[str, Any]:
    dados = entradas.get("dados_usuario", {}) or {}
    campos = {k: v for k, v in dados.items() if k != "perfil"}
    if isinstance(dados.get("perfil"), dict):
        campos = {**campos, **dados["perfil"]}

    anteriores = entradas.get("saidas_anteriores", {})
    arvore = anteriores.get("04", {}) or {}
    grafo = anteriores.get("05", {}) or {}
    aula = anteriores.get("07", {}) or {}
    exemplos = anteriores.get("08", {}) or {}
    exercicios = anteriores.get("09", {}) or {}
    flashcards = anteriores.get("10", {}) or {}

    no = localizar_no(grafo, aula, campos.get("conteudo_solicitado"))
    bloqueio = conteudo_estudado(aula, no, grafo)
    if bloqueio:
        return {"bloqueio": bloqueio, "conteudo": None, "secoes": []}

    conceitos = _conceitos(aula, flashcards, exercicios)
    tem_formula = _tem_formula(aula, conceitos)
    secoes = [
        {**secao, "aplicavel": (not secao["condicional"]) or tem_formula}
        for secao in SECOES
    ]

    conteudo = aula.get("conteudo") or (
        {"id": no["id"], "nome": no["nome"], "disciplina": no["disciplina"]}
        if no
        else None
    )

    return {
        "bloqueio": None,
        "conteudo": conteudo,
        "titulo": f"Resumo — {conteudo['nome']}" if conteudo else "Resumo",
        "objetivo": aula.get("objetivo"),
        "nivel_do_estudante": aula.get("nivel_do_estudante"),
        "conceitos_chave": conceitos,
        "secoes": secoes,
        "secoes_aplicaveis": [s["chave"] for s in secoes if s["aplicavel"]],
        "derivados": {
            "mapa_mental_textual": _mapa_mental(arvore, no, conceitos),
            "checklist_de_revisao": _checklist(conceitos, flashcards),
            "erros_comuns": _erros_comuns(aula, exemplos, exercicios),
            "proximos_conteudos_relacionados": _proximos(grafo, no),
        },
        "fonte": {
            "aula": {
                "desenvolvimento": aula.get("desenvolvimento"),
                "resumo": aula.get("resumo"),
                "pontos_chave": como_lista(aula.get("pontos_chave")),
                "erros_comuns": aula.get("erros_comuns"),
            },
            "exemplos": {
                chave: exemplos.get(chave)
                for chave in ("exemplo_pratico", "contraexemplo")
                if exemplos.get(chave)
            },
            "regra": (
                "O resumo só pode conter o que a aula ensinou. Nada de novo, "
                "nada de fora — sintetizar não é acrescentar."
            ),
        },
        "limites": {
            "palavras_por_minuto": PALAVRAS_POR_MINUTO,
            "resumo_1min": LIMITES_DE_PALAVRAS["resumo_1min"],
            "resumo_5min": LIMITES_DE_PALAVRAS["resumo_5min"],
            "tolerancia": TOLERANCIA_DE_TAMANHO,
        },
        "diretrizes": [
            "Eliminar redundância, preservar todos os conceitos essenciais.",
            "Manter a mesma sequência lógica da aula.",
            "Cada nível de resumo cabe no tempo que promete.",
            "Todos os conceitos-chave aparecem no resumo completo.",
        ],
        "proibicoes": [
            "não ensinar conteúdo novo (agente 07)",
            "não criar exercícios (agente 09)",
            "não criar cronograma (agente 06)",
            "não gerar simulados (agente 16)",
            "não avaliar desempenho (agentes 17, 18, 21)",
        ],
    }


def montar(
    briefing: dict[str, Any], secoes: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Monta o resumo — conferindo tamanho prometido e conceitos preservados."""
    bloqueio = briefing.get("bloqueio")
    if bloqueio and secoes:
        raise ConteudoNaoEstudado(bloqueio["detalhe"])

    if bloqueio:
        return {
            "gerado": False,
            "bloqueio": bloqueio,
            "status": "bloqueado",
            "titulo": None,
            **{chave: None for chave in CHAVES_DE_SECAO},
            "conceitos_chave": [],
            "checklist_de_revisao": [],
            "mapa_mental_textual": "",
            "proximos_conteudos_relacionados": [],
            "briefing": None,
            "consumido_por": CONSUMIDORES,
            "observacoes": [f"Resumo não gerado: {bloqueio['detalhe']}"],
            "lacunas": ["conteudo_estudado"],
        }

    redigidas = dict(secoes or {})
    desconhecidas = sorted(set(redigidas) - set(CHAVES_DE_SECAO))
    aplicaveis = set(briefing["secoes_aplicaveis"])

    excedidas: list[dict] = []
    pendentes: list[str] = []
    conteudo_das_secoes: dict[str, Any] = {}

    for secao in briefing["secoes"]:
        chave = secao["chave"]
        if chave not in aplicaveis:
            conteudo_das_secoes[chave] = None
            continue

        valor = redigidas.get(chave)
        if not preenchido(valor):
            pendentes.append(chave)
            conteudo_das_secoes[chave] = None
            continue

        limite = secao["limite_palavras"]
        palavras = _palavras(valor)
        if limite and palavras > limite:
            excedidas.append(
                {
                    "secao": chave,
                    "palavras": palavras,
                    "limite": limite,
                    "motivo": (
                        f"{palavras} palavras excedem o orçamento de {limite} "
                        f"({palavras / PALAVRAS_POR_MINUTO:.1f} min de leitura): "
                        "não cabe no tempo prometido"
                    ),
                }
            )
            conteudo_das_secoes[chave] = None
            continue

        conteudo_das_secoes[chave] = valor

    ausentes = _conceitos_ausentes(
        briefing["conceitos_chave"], conteudo_das_secoes.get("resumo_completo")
    )
    progressao = _progressao(conteudo_das_secoes)
    completo = (
        bool(secoes) and not pendentes and not excedidas and not ausentes and progressao
    )

    derivados = briefing["derivados"]
    resumo = {
        "gerado": completo,
        "bloqueio": None,
        "conteudo": briefing["conteudo"],
        "titulo": briefing["titulo"],
        "objetivo": briefing["objetivo"],
        **conteudo_das_secoes,
        "erros_comuns": derivados["erros_comuns"],
        "conceitos_chave": briefing["conceitos_chave"],
        "checklist_de_revisao": derivados["checklist_de_revisao"],
        "mapa_mental_textual": derivados["mapa_mental_textual"],
        "proximos_conteudos_relacionados": derivados["proximos_conteudos_relacionados"],
        "tempo_estimado_de_leitura_min": _tempo_de_leitura(conteudo_das_secoes),
        "secoes_pendentes": pendentes,
        "secoes_excedidas": excedidas,
        "secoes_ignoradas": desconhecidas,
        "secoes_nao_aplicaveis": [
            s["chave"] for s in briefing["secoes"] if not s["aplicavel"]
        ],
        "conceitos_ausentes_no_resumo": ausentes,
        "progressao_de_tamanho_ok": progressao,
        "status": "gerado" if completo else "pendente_de_redacao",
        "briefing": briefing,
        "consumido_por": CONSUMIDORES,
        "lacunas": [] if briefing["conceitos_chave"] else ["pontos_chave_da_aula"],
    }
    resumo["observacoes"] = _observacoes(
        pendentes, excedidas, desconhecidas, ausentes, progressao, briefing
    )
    return resumo


def _palavras(valor: Any) -> int:
    if isinstance(valor, (list, tuple)):
        return sum(_palavras(item) for item in valor)
    if isinstance(valor, dict):
        return sum(_palavras(item) for item in valor.values())
    return len(str(valor).split())


def _conceitos_ausentes(conceitos: list[str], resumo_completo: Any) -> list[str]:
    if not preenchido(resumo_completo):
        return list(conceitos)
    texto = como_texto(resumo_completo)
    return [c for c in conceitos if como_texto(c) not in texto]


def _progressao(secoes: dict[str, Any]) -> bool:
    """1 min ⊂ 5 min ⊂ completo — em tamanho, na ordem que a spec promete."""
    tamanhos = [
        _palavras(secoes.get(chave))
        for chave in ("resumo_1min", "resumo_5min", "resumo_completo")
        if preenchido(secoes.get(chave))
    ]
    if len(tamanhos) < 2:
        return True
    return all(anterior <= seguinte for anterior, seguinte in zip(tamanhos, tamanhos[1:]))


def _tempo_de_leitura(secoes: dict[str, Any]) -> dict[str, float]:
    return {
        chave: round(_palavras(secoes.get(chave)) / PALAVRAS_POR_MINUTO, 1)
        for chave in ("resumo_1min", "resumo_5min", "resumo_completo")
        if preenchido(secoes.get(chave))
    }


CONSUMIDORES = ["13", "14", "15", "16", "17", "18", "21", "24"]


def _observacoes(
    pendentes: list[str],
    excedidas: list[dict],
    desconhecidas: list[str],
    ausentes: list[str],
    progressao: bool,
    briefing: dict,
) -> list[str]:
    observacoes: list[str] = []
    if pendentes:
        observacoes.append(
            f"{len(pendentes)} seção(ões) sem redação. Resumo é conteúdo: exige "
            "redator conectado, não foi preenchido por invenção."
        )
    for excedida in excedidas:
        observacoes.append(f"{excedida['secao']}: {excedida['motivo']}")
    if ausentes:
        observacoes.append(
            "Conceitos essenciais ausentes do resumo completo: "
            + ", ".join(ausentes)
            + " — a spec proíbe removê-los."
        )
    if not progressao:
        observacoes.append(
            "Os níveis de resumo não crescem em tamanho: o de 1 minuto deveria "
            "ser o mais curto e o completo, o mais longo."
        )
    if desconhecidas:
        observacoes.append(
            "Seções fora da estrutura foram descartadas: " + ", ".join(desconhecidas)
        )
    if not briefing["derivados"]["mapa_mental_textual"]:
        observacoes.append(
            "Mapa mental vazio: o conteúdo não foi localizado na Árvore "
            "Curricular do agente 04."
        )
    nao_aplicaveis = [s["chave"] for s in briefing["secoes"] if not s["aplicavel"]]
    if nao_aplicaveis:
        observacoes.append(
            "Seções não aplicáveis a este conteúdo: " + ", ".join(nao_aplicaveis)
        )
    return observacoes


# --------------------------------------------------------------------------- #
# Entrada principal
# --------------------------------------------------------------------------- #


@declara_confiabilidade
def gerar(
    entradas: dict[str, Any],
    redator: Callable[[dict], dict] | None = None,
) -> dict[str, Any]:
    """Gera o conjunto de resumos do conteúdo estudado."""
    briefing = montar_briefing(entradas)
    if briefing.get("bloqueio") or redator is None:
        return montar(briefing)
    return montar(briefing, redator(briefing))


__all__ = [
    "CHAVES_DE_SECAO",
    "LIMITES_DE_PALAVRAS",
    "PALAVRAS_POR_MINUTO",
    "ConteudoNaoEstudado",
    "gerar",
    "montar",
    "montar_briefing",
]
