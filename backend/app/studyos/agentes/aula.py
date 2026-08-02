"""Agente 07 — Lesson Generator.

Única responsabilidade: produzir a aula de um microtópico. Não cria cronograma,
não decide ordem de estudo, não avalia desempenho, não gera exercícios,
flashcards ou simulados.

Este é o primeiro agente cuja saída é **conteúdo didático** — e conteúdo
didático não sai de código determinístico sem virar invenção, que é justamente
o que a regra "nunca utilizar informações sem fundamento" proíbe. Por isso o
módulo separa duas coisas:

* **O que precisa ser código:** o portão de pré-requisitos, o nível do
  estudante, a estrutura das seções, as fontes que não podem ser contrariadas e
  o que já foi estudado. Nada disso pode depender de um modelo se comportar
  bem — ``montar`` revalida o portão mesmo quando a redação vem de fora.
* **O que precisa de um modelo:** a redação das seções. Sem redator conectado,
  elas voltam ``None`` com o briefing pronto, nunca com prosa fabricada.
"""

from __future__ import annotations

from typing import Any, Callable

from app.studyos.agentes.comum import como_lista, como_texto, preenchido
from app.studyos.agentes.comum import declara_confiabilidade

# --------------------------------------------------------------------------- #
# Estrutura declarada da aula
# --------------------------------------------------------------------------- #

#: Seções redigidas pelo modelo, na ordem da spec (4b a 4i). O objetivo (4a) é
#: determinístico: vem do objetivo de aprendizagem da Árvore Curricular.
SECOES: tuple[dict[str, str], ...] = (
    {
        "chave": "introducao",
        "etapa": "b. Contextualização",
        "instrucao": (
            "Situar o conteúdo: por que ele existe, onde aparece no objetivo do "
            "estudante e como se conecta ao que ele já estudou."
        ),
    },
    {
        "chave": "desenvolvimento",
        "etapa": "c. Conceitos fundamentais + d. Explicação passo a passo",
        "instrucao": (
            "Definir os conceitos fundamentais e desenvolvê-los em progressão "
            "lógica, um passo de cada vez, destacando os termos importantes."
        ),
    },
    {
        "chave": "exemplos",
        "etapa": "e. Exemplos práticos",
        "instrucao": (
            "Exemplos variados e resolvidos, do mais simples ao mais completo. "
            "Usar analogia quando o conceito for abstrato."
        ),
    },
    {
        "chave": "aplicacoes",
        "etapa": "f. Aplicações no mundo real",
        "instrucao": "Onde este conteúdo aparece na prática e na prova do objetivo.",
    },
    {
        "chave": "erros_comuns",
        "etapa": "g. Erros mais comuns",
        "instrucao": "Os erros que o estudante tende a cometer e como evitá-los.",
    },
    {
        "chave": "dicas",
        "etapa": "h. Dicas de memorização",
        "instrucao": "Recursos de fixação: mnemônicos, padrões, regras práticas.",
    },
    {
        "chave": "resumo",
        "etapa": "i. Resumo",
        "instrucao": "Síntese fechada do que foi ensinado, em poucos parágrafos.",
    },
    {
        "chave": "pontos_chave",
        "etapa": "i. Pontos-chave",
        "instrucao": (
            "Lista dos termos e fatos essenciais, prontos para virar flashcards "
            "(agente 10) e resumos (agente 11)."
        ),
    },
)

CHAVES_DE_SECAO = tuple(secao["chave"] for secao in SECOES)

NIVEIS = ("iniciante", "basico", "intermediario", "avancado")

#: Nível de linguagem a partir do domínio medido pelo agente 03.
NIVEL_POR_DOMINIO: dict[str, str] = {
    "nao_conhece": "iniciante",
    "basico": "basico",
    "intermediario": "intermediario",
    "avancado": "avancado",
}

#: Nível de partida a partir da estimativa geral do agente 01, quando o tópico
#: não tem medição própria.
NIVEL_POR_ESTIMATIVA_GERAL: dict[str, str] = {
    "iniciante": "iniciante",
    "intermediario": "basico",
    "avancado": "intermediario",
}

#: Sem nenhuma evidência, a aula começa do começo — é o erro barato.
NIVEL_PADRAO = "iniciante"

#: Ajuste de formato conforme o estilo de aprendizagem do agente 01.
DIRETRIZ_POR_ESTILO: dict[str, str] = {
    "visual": "Apoiar as explicações em esquemas, tabelas e descrições visuais.",
    "auditivo": "Escrever em tom de explicação falada, com repetição estruturada.",
    "leitura_escrita": "Priorizar texto estruturado, definições e listas.",
    "cinestesico": "Ancorar cada conceito em um exemplo resolvido passo a passo.",
}


class AulaBloqueada(Exception):
    """Tentativa de montar aula de conteúdo com pré-requisito pendente."""


# --------------------------------------------------------------------------- #
# Seleção do conteúdo e portão de pré-requisitos
# --------------------------------------------------------------------------- #


def _localizar(grafo: dict, solicitado: Any, plano: dict) -> dict | None:
    nos = grafo.get("nos", [])
    if not nos:
        return None

    if preenchido(solicitado):
        alvo = como_texto(solicitado)
        for no in nos:
            if no["id"] == solicitado or como_texto(no["nome"]) == alvo:
                return no
        return None

    # Sem pedido explícito, a aula é a do próximo conteúdo do Plano de Estudos.
    for dia in plano.get("cronograma", []):
        for sessao in dia.get("sessoes", []):
            if sessao.get("tipo") == "conteudo" and sessao.get("no_id"):
                for no in nos:
                    if no["id"] == sessao["no_id"]:
                        return no

    disponiveis = [no for no in nos if no["status"] == "disponivel"]
    return disponiveis[0] if disponiveis else None


def _portao(no: dict, grafo: dict) -> dict | None:
    """Bloqueia a aula quando algum pré-requisito não está concluído."""
    por_id = {n["id"]: n for n in grafo.get("nos", [])}
    pendentes = [
        por_id[pre]["nome"]
        for pre in no.get("bloqueado_por", [])
        if pre in por_id
    ]
    ancestrais = [
        por_id[pre]["nome"]
        for ancestral in no.get("bloqueado_por_ancestral", [])
        for pre in por_id.get(ancestral, {}).get("bloqueado_por", [])
        if pre in por_id
    ]
    if not pendentes and not ancestrais:
        return None

    return {
        "motivo": "pre_requisitos_nao_concluidos",
        "pre_requisitos_pendentes": pendentes,
        "pendentes_por_ancestral": ancestrais,
        "acao": (
            "Estudar os pré-requisitos antes. A aula não é gerada: ensinar aqui "
            "quebraria a progressão lógica."
        ),
    }


# --------------------------------------------------------------------------- #
# Adaptação ao estudante
# --------------------------------------------------------------------------- #


def _nivel_do_estudante(no: dict, mapa_conhecimento: dict, perfil: dict) -> dict:
    for disciplina in mapa_conhecimento.get("disciplinas", []):
        for topico in disciplina.get("topicos", []):
            if como_texto(topico["topico"]) in (
                como_texto(no["nome"]),
                como_texto(no.get("topico_pai", "")),
            ):
                classificacao = topico.get("classificacao")
                if classificacao in NIVEL_POR_DOMINIO:
                    return {
                        "nivel": NIVEL_POR_DOMINIO[classificacao],
                        "base": f"domínio medido no tópico: {classificacao}",
                        "confianca": topico.get("confianca", "media"),
                    }

    estimativa = (perfil.get("nivel_conhecimento_geral") or {}).get("estimativa")
    if estimativa in NIVEL_POR_ESTIMATIVA_GERAL:
        return {
            "nivel": NIVEL_POR_ESTIMATIVA_GERAL[estimativa],
            "base": (
                f"sem medição do tópico; derivado da estimativa geral "
                f"'{estimativa}' do agente 01, com um nível de folga"
            ),
            "confianca": "baixa",
        }

    return {
        "nivel": NIVEL_PADRAO,
        "base": "sem medição do tópico nem estimativa geral",
        "confianca": "nenhuma",
    }


def _coerencia(grafo: dict, no: dict) -> dict:
    """O que a aula pode pressupor e o que não pode."""
    nos = grafo.get("nos", [])
    concluidos = [n["nome"] for n in nos if n["status"] == "concluido"]
    pendentes = [
        n["nome"]
        for n in nos
        if n["status"] != "concluido" and n["id"] != no["id"] and n["tipo"] == no["tipo"]
    ]
    return {
        "pode_pressupor": concluidos,
        "nao_pode_pressupor": pendentes,
        "regra": (
            "Só é permitido apoiar-se em conteúdo já concluído. Conteúdo pendente "
            "não pode ser usado como base da explicação."
        ),
    }


def _fontes(campos: dict) -> dict:
    bibliografia = como_lista(campos.get("bibliografia"))
    materiais = como_lista(campos.get("materiais_obrigatorios"))
    oficiais = bibliografia + materiais
    return {
        "materiais_oficiais": oficiais,
        "restricao": (
            "Não contradizer os materiais oficiais listados; em divergência, "
            "prevalece o material oficial."
            if oficiais
            else "Nenhum material oficial informado: ater-se ao consenso "
            "estabelecido da área e não afirmar o que não puder ser fundamentado."
        ),
    }


def _proximo(grafo: dict, no: dict) -> dict | None:
    sequencia = grafo.get("sequencia_logica", [])
    for indice, item in enumerate(sequencia):
        if item["id"] == no["id"] and indice + 1 < len(sequencia):
            seguinte = sequencia[indice + 1]
            return {"id": seguinte["id"], "nome": seguinte["nome"]}
    return None


# --------------------------------------------------------------------------- #
# Briefing e montagem
# --------------------------------------------------------------------------- #


def montar_briefing(entradas: dict[str, Any]) -> dict[str, Any]:
    """Tudo que o redator precisa — e tudo que ele não pode violar."""
    dados = entradas.get("dados_usuario", {}) or {}
    campos = {k: v for k, v in dados.items() if k != "perfil"}
    if isinstance(dados.get("perfil"), dict):
        campos = {**campos, **dados["perfil"]}

    anteriores = entradas.get("saidas_anteriores", {})
    perfil = anteriores.get("01", {}) or {}
    mapa_conhecimento = anteriores.get("03", {}) or {}
    arvore = anteriores.get("04", {}) or {}
    grafo = anteriores.get("05", {}) or {}
    plano = anteriores.get("06", {}) or {}

    solicitado = campos.get("conteudo_solicitado") or entradas.get("conteudo_solicitado")
    no = _localizar(grafo, solicitado, plano)

    if no is None:
        return {
            "no": None,
            "bloqueio": None,
            "erro": (
                "Conteúdo solicitado não encontrado no Grafo de Aprendizagem"
                if preenchido(solicitado)
                else "Nenhum conteúdo disponível para aula"
            ),
        }

    bloqueio = _portao(no, grafo)
    nivel = _nivel_do_estudante(no, mapa_conhecimento, perfil)
    estilo = (perfil.get("estilo_aprendizagem") or {}).get("predominante")

    objetivo = _objetivo_da_arvore(arvore, no) or (
        f"Dominar {no['nome']} no contexto de {no['disciplina']}"
    )

    diretrizes = [
        f"Linguagem de nível {nivel['nivel']} ({nivel['base']}).",
        "Progressão lógica: nenhum conceito antes do que ele exige.",
        "Destacar os termos importantes para reuso pelos agentes 10 e 11.",
    ]
    if estilo and estilo in DIRETRIZ_POR_ESTILO:
        diretrizes.append(DIRETRIZ_POR_ESTILO[estilo])

    return {
        "no": {
            "id": no["id"],
            "nome": no["nome"],
            "tipo": no["tipo"],
            "disciplina": no["disciplina"],
        },
        "bloqueio": bloqueio,
        "titulo": f"{no['nome']} — {no['disciplina']}",
        "objetivo": objetivo,
        "tempo_estimado_h": no.get("tempo_estimado_h"),
        "nivel_dificuldade": no.get("dificuldade"),
        "nivel_do_estudante": nivel,
        "estilo_de_aprendizagem": estilo,
        "pre_requisitos": _nomes_de_pre_requisitos(no, grafo),
        "secoes": [dict(secao) for secao in SECOES],
        "diretrizes": diretrizes,
        "fontes": _fontes(campos),
        "coerencia": _coerencia(grafo, no),
        "proibicoes": [
            "não gerar exercícios (agente 09)",
            "não gerar flashcards (agente 10)",
            "não gerar simulados (agente 16)",
            "não criar cronograma (agente 06)",
            "não avaliar desempenho (agentes 17, 18, 21)",
        ],
        "proximo_conteudo_recomendado": _proximo(grafo, no),
    }


def _objetivo_da_arvore(arvore: dict, no: dict) -> str | None:
    alvo = como_texto(no["nome"])
    for disciplina in arvore.get("disciplinas", []):
        for modulo in disciplina.get("modulos", []):
            for topico in modulo.get("topicos", []):
                for subtopico in topico.get("subtopicos", []):
                    if como_texto(subtopico["nome"]) == alvo:
                        return subtopico.get("objetivo_de_aprendizagem")
    return None


def _nomes_de_pre_requisitos(no: dict, grafo: dict) -> list[str]:
    por_id = {n["id"]: n for n in grafo.get("nos", [])}
    return [por_id[pre]["nome"] for pre in no.get("pre_requisitos", []) if pre in por_id]


def montar(briefing: dict[str, Any], secoes: dict[str, Any] | None = None) -> dict[str, Any]:
    """Monta a aula final — revalidando o portão, venha a redação de onde vier.

    ``secoes`` traz o texto produzido pelo redator. Sem ele, a aula volta com as
    seções em ``None`` e o briefing pronto: pendente, nunca inventada.
    """
    if briefing.get("erro"):
        return {
            "gerada": False,
            "erro": briefing["erro"],
            "status": "sem_conteudo",
            "briefing": None,
            "consumido_por": CONSUMIDORES,
        }

    bloqueio = briefing.get("bloqueio")
    if bloqueio and secoes:
        # A regra vale para qualquer redator: um modelo não pode "convencer" o
        # agente a ensinar conteúdo com pré-requisito pendente.
        raise AulaBloqueada(
            f"{briefing['no']['nome']} depende de: "
            + ", ".join(bloqueio["pre_requisitos_pendentes"] or bloqueio["pendentes_por_ancestral"])
        )

    redigidas = dict(secoes or {})
    desconhecidas = sorted(set(redigidas) - set(CHAVES_DE_SECAO))
    faltantes = [chave for chave in CHAVES_DE_SECAO if not preenchido(redigidas.get(chave))]

    aula = {
        "gerada": bool(secoes) and not bloqueio and not faltantes,
        "bloqueio": bloqueio,
        "conteudo": briefing["no"],
        "titulo": briefing["titulo"],
        "objetivo": briefing["objetivo"],
        "tempo_estimado_h": briefing["tempo_estimado_h"],
        "nivel_dificuldade": briefing["nivel_dificuldade"],
        "nivel_do_estudante": briefing["nivel_do_estudante"],
        "pre_requisitos": briefing["pre_requisitos"],
        "proximo_conteudo_recomendado": briefing["proximo_conteudo_recomendado"],
    }
    for chave in CHAVES_DE_SECAO:
        valor = redigidas.get(chave)
        aula[chave] = valor if preenchido(valor) else None

    if bloqueio:
        status = "bloqueada_por_pre_requisito"
    elif faltantes:
        status = "pendente_de_redacao"
    else:
        status = "gerada"

    aula.update(
        {
            "status": status,
            "secoes_pendentes": faltantes,
            "secoes_ignoradas": desconhecidas,
            "briefing": briefing,
            "consumido_por": CONSUMIDORES,
            "observacoes": _observacoes(bloqueio, faltantes, desconhecidas, briefing),
            "lacunas": _lacunas(briefing),
        }
    )
    return aula


CONSUMIDORES = ["08", "09", "10", "11", "13", "16", "24"]


def _observacoes(
    bloqueio: dict | None, faltantes: list[str], desconhecidas: list[str], briefing: dict
) -> list[str]:
    observacoes: list[str] = []
    if bloqueio:
        observacoes.append(
            "Aula não gerada: "
            + ", ".join(
                bloqueio["pre_requisitos_pendentes"] or bloqueio["pendentes_por_ancestral"]
            )
            + " ainda não concluído(s)."
        )
    if faltantes and not bloqueio:
        observacoes.append(
            f"{len(faltantes)} seção(ões) sem redação. O conteúdo didático exige "
            "um redator conectado — nada foi preenchido por invenção."
        )
    if desconhecidas:
        observacoes.append(
            "Seções fora da estrutura foram descartadas: " + ", ".join(desconhecidas)
        )
    if not briefing["fontes"]["materiais_oficiais"]:
        observacoes.append(
            "Nenhum material oficial informado: a aula não pode ser conferida "
            "contra bibliografia obrigatória."
        )
    if briefing["nivel_do_estudante"]["confianca"] in ("baixa", "nenhuma"):
        observacoes.append(
            "Nível do estudante estimado com baixa confiança: uma avaliação "
            "diagnóstica (agente 03) tornaria a adaptação mais precisa."
        )
    return observacoes


def _lacunas(briefing: dict) -> list[str]:
    lacunas: list[str] = []
    if not briefing["fontes"]["materiais_oficiais"]:
        lacunas.append("bibliografia_oficial")
    if briefing["nivel_do_estudante"]["confianca"] == "nenhuma":
        lacunas.append("nivel_medido_do_topico")
    return lacunas


# --------------------------------------------------------------------------- #
# Entrada principal
# --------------------------------------------------------------------------- #


@declara_confiabilidade
def gerar(
    entradas: dict[str, Any],
    redator: Callable[[dict], dict] | None = None,
) -> dict[str, Any]:
    """Gera a aula do conteúdo solicitado.

    Sem ``redator``, devolve a aula estruturada com as seções pendentes e o
    briefing pronto para um modelo. Com ``redator``, a redação é dele — mas o
    portão de pré-requisitos e a estrutura continuam sendo deste módulo.
    """
    briefing = montar_briefing(entradas)
    if briefing.get("erro") or briefing.get("bloqueio") or redator is None:
        return montar(briefing)
    return montar(briefing, redator(briefing))


__all__ = ["AulaBloqueada", "CHAVES_DE_SECAO", "SECOES", "gerar", "montar", "montar_briefing"]
