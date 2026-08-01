"""Agente 18 — Weakness Finder.

Única responsabilidade: dizer exatamente **quais conteúdos impedem o estudante
de evoluir**, e em que ordem recuperá-los. Não ensina, não gera exercício, não
altera plano nem currículo.

A pergunta que separa este agente do 12 e do 17: eles medem o que está
difícil e o que deu errado; aqui a medida é **fragilidade com consequência**.
Um tópico mal dominado que não bloqueia nada e vale 2% do edital é um problema
menor que um tópico igualmente mal dominado que trava outros cinco. Por isso o
grafo do agente 05 entra dentro do índice, e não como enfeite ao lado dele.

Três decisões estruturais:

* **Sem evidência não há fraqueza.** Conteúdo sem nenhuma medição não recebe
  índice: vai para `conteudos_sem_evidencia`. Índice zero seria dizer "está
  estável", que é uma afirmação sobre o estudante que ninguém mediu.
* **Maior fraqueza e maior urgência são listas diferentes.** A primeira ordena
  por índice; a segunda pondera o índice pelo que o calendário e o grafo
  impõem. O conteúdo mais frágil nem sempre é o próximo a tratar.
* **Frequência de esquecimento só cresce com observação nova.** Ela é contada
  ao longo dos mapas, não deduzida de um retrato só.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from app.studyos.agentes.comum import (
    como_data,
    como_lista_de_dicts,
    como_numero,
    como_texto,
    preenchido,
)

# --------------------------------------------------------------------------- #
# Constantes declaradas
# --------------------------------------------------------------------------- #

#: Peso de cada sintoma de fragilidade. Componente ausente não entra e o peso é
#: redistribuído entre os presentes — o mesmo critério do agente 12.
PESOS_DO_INDICE: dict[str, float] = {
    "dominio": 0.45,
    "erro": 0.35,
    "esquecimento": 0.20,
}

#: Quanto o bloqueio no grafo amplia o índice, no máximo.
#:
#: Bloqueio **não é um componente da média** e sim um amplificador: travar
#: outros conteúdos não é um sintoma de fragilidade a mais, é o que transforma
#: a fragilidade em obstáculo. Entrando na média ele diluiria — um tópico com
#: domínio `nao_conhece` (1.0) e bloqueio parcial (0.2) sairia *menos* frágil
#: do que o mesmo tópico sem bloqueio nenhum, que é o contrário do que a
#: identidade do agente diz.
AMPLIFICACAO_MAXIMA_DO_BLOQUEIO = 0.30

#: Classificação do agente 03 → quanto ela pesa como fragilidade.
VALOR_POR_CLASSIFICACAO: dict[str, float] = {
    "nao_conhece": 1.00,
    "basico": 0.70,
    "intermediario": 0.35,
    "avancado": 0.10,
}

#: Faixas do Índice de Fraqueza → nível de prioridade.
FAIXAS: tuple[tuple[float, str], ...] = (
    (0.25, "estavel"),
    (0.50, "atencao"),
    (0.75, "critico"),
)
NIVEL_MAXIMO = "prioridade_maxima"
NIVEIS = ("estavel", "atencao", "critico", NIVEL_MAXIMO)

#: Conteúdos bloqueados a partir dos quais o componente de bloqueio satura.
#: Acima disso o tópico já é um gargalo estrutural; a diferença entre travar
#: seis ou dez conteúdos não muda a decisão.
BLOQUEIO_MAXIMO = 5

#: Retenção abaixo da qual há decaimento relevante (mesmo limiar do agente 12,
#: para os dois não discordarem sobre o que é esquecimento).
LIMIAR_DECAIMENTO_RELEVANTE = 0.9

#: Tamanho dos rankings.
TAMANHO_DO_RANKING = 10

#: Variação do índice geral a partir da qual a tendência deixa de ser estável.
LIMIAR_VARIACAO_RELEVANTE = 0.05

#: Dias até a prova que aumentam a urgência de tudo que ainda está frágil.
DIAS_PARA_RETA_FINAL = 30

#: Nível → ação recomendada. É recomendação para os agentes 19 e 23, não
#: execução: este agente não marca revisão nem mexe no cronograma.
ACAO_POR_NIVEL: dict[str, str] = {
    "estavel": "manter",
    "atencao": "revisar",
    "critico": "reforcar",
    NIVEL_MAXIMO: "reestudar",
}

#: A ação de avançar é a única que não sai do nível: ela exige domínio medido
#: alto e nenhum sinal de esquecimento.
ACAO_AVANCAR = "avancar"
ACOES = ("manter", "revisar", "reforcar", "reestudar", ACAO_AVANCAR)


def _nivel(indice: float) -> str:
    for limite, nome in FAIXAS:
        if indice < limite:
            return nome
    return NIVEL_MAXIMO


# --------------------------------------------------------------------------- #
# Consolidação das fontes
# --------------------------------------------------------------------------- #


def _posicao_curricular(arvore: dict) -> dict[str, dict]:
    """Disciplina e módulo de cada tópico, para o mapa localizar o conteúdo."""
    posicao: dict[str, dict] = {}
    for disciplina in arvore.get("disciplinas", []):
        for modulo in disciplina.get("modulos", []):
            for topico in modulo.get("topicos", []):
                posicao[como_texto(topico["nome"])] = {
                    "topico": topico["nome"],
                    "disciplina": disciplina["nome"],
                    "modulo": modulo["nome"],
                    "status": topico.get("status"),
                    "obrigatorio": topico.get("obrigatorio", True),
                }
    return posicao


def _posicao_no_grafo(grafo: dict) -> dict[str, dict]:
    """Quantos conteúdos cada tópico trava, e quais são."""
    bloqueados: dict[str, list[str]] = {}
    for no in grafo.get("nos", []):
        for pre in no.get("pre_requisitos", []):
            bloqueados.setdefault(pre, []).append(no["nome"])

    return {
        como_texto(no["nome"]): {
            "conteudos_bloqueados": no.get("dependentes_transitivos", 0),
            "dependentes_diretos": bloqueados.get(no["id"], []),
            "profundidade": no.get("profundidade", 0),
        }
        for no in grafo.get("nos", [])
        if no.get("tipo") in ("topico", "subtopico", "microtopico")
    }


def _erros_por_topico(relatorio_de_erros: dict) -> dict[str, dict]:
    """Contagem, gravidade e competências dos erros do agente 17, por tópico."""
    por_topico: dict[str, dict] = {}
    for erro in relatorio_de_erros.get("erros", []):
        chave = como_texto(erro.get("topico") or "")
        if not chave:
            continue
        registro = por_topico.setdefault(
            chave,
            {
                "quantidade": 0,
                "recorrentes": 0,
                "gravidade_maxima": 0.0,
                "tipos": {},
                "competencias": {},
            },
        )
        registro["quantidade"] += 1
        registro["recorrentes"] += 1 if erro.get("recorrente") else 0
        registro["gravidade_maxima"] = max(
            registro["gravidade_maxima"], (erro.get("gravidade") or {}).get("score", 0.0)
        )
        tipo = erro.get("tipo") or "indeterminado"
        registro["tipos"][tipo] = registro["tipos"].get(tipo, 0) + 1
        competencia = erro.get("competencia_avaliada")
        if preenchido(competencia):
            registro["competencias"][competencia] = (
                registro["competencias"].get(competencia, 0) + 1
            )
    return por_topico


def _medicoes(mapa_conhecimento: dict, relatorio: dict) -> dict[str, dict]:
    """O que os agentes 03 e 12 sabem de cada tópico, num registro só."""
    medicoes: dict[str, dict] = {}

    for disciplina in mapa_conhecimento.get("disciplinas", []):
        for medicao in disciplina.get("topicos", []):
            medicoes[como_texto(medicao["topico"])] = {
                "topico": medicao["topico"],
                "disciplina": disciplina["disciplina"],
                "classificacao": medicao.get("classificacao", "indeterminado"),
                "taxa_acerto": medicao.get("taxa_acerto"),
                "amostra": medicao.get("amostra"),
                "retencao": medicao.get("retencao_estimada"),
                "esquecido": bool(medicao.get("esquecido")),
                "dias_sem_contato": medicao.get("dias_sem_contato"),
            }

    for topico in relatorio.get("topicos", []):
        registro = medicoes.setdefault(
            como_texto(topico["topico"]),
            {
                "topico": topico["topico"],
                "disciplina": topico.get("disciplina"),
                "classificacao": "indeterminado",
            },
        )
        registro["indice_de_dificuldade"] = (topico.get("dificuldade") or {}).get("indice")
        registro["frequencia_de_erros_do_12"] = topico.get("frequencia_de_erros", 0)
        registro["esquecido"] = bool(topico.get("esquecido")) or registro.get("esquecido", False)
        if registro.get("taxa_acerto") is None:
            registro["taxa_acerto"] = topico.get("taxa_de_acertos")
        if registro.get("amostra") is None:
            registro["amostra"] = topico.get("amostra")

    return medicoes


# --------------------------------------------------------------------------- #
# Índice de Fraqueza
# --------------------------------------------------------------------------- #


def _componentes(medicao: dict, erros: dict, grafo: dict) -> dict[str, dict]:
    """Só o que foi medido entra. Ausência de dado não vira valor zero."""
    componentes: dict[str, dict] = {}

    classificacao = medicao.get("classificacao")
    if classificacao in VALOR_POR_CLASSIFICACAO:
        componentes["dominio"] = {
            "valor": VALOR_POR_CLASSIFICACAO[classificacao],
            "base": f"domínio medido pelo agente 03: {classificacao}",
        }

    taxa = medicao.get("taxa_acerto")
    if taxa is not None and medicao.get("amostra"):
        componentes["erro"] = {
            "valor": round(1 - taxa, 4),
            "base": f"{int(medicao['amostra'])} questões, {taxa:.0%} de acerto",
        }
    elif erros.get("quantidade"):
        # Sem taxa, o que se tem é a contagem de erros do agente 17. Ela satura
        # rápido de propósito: contagem sem denominador não vira percentual.
        componentes["erro"] = {
            "valor": round(min(1.0, 0.4 + 0.2 * erros["quantidade"]), 4),
            "base": f"{erros['quantidade']} erro(s) registrados pelo agente 17",
        }

    retencao = medicao.get("retencao")
    if medicao.get("esquecido"):
        componentes["esquecimento"] = {
            "valor": 1.0,
            "base": "conteúdo marcado como esquecido",
        }
    elif retencao is not None and retencao < LIMIAR_DECAIMENTO_RELEVANTE:
        componentes["esquecimento"] = {
            "valor": round(1 - retencao, 4),
            "base": f"retenção estimada de {retencao:.0%}",
        }

    return componentes


def _indice(componentes: dict[str, dict], grafo: dict) -> dict:
    """Média ponderada dos sintomas, amplificada pelo que o conteúdo trava."""
    peso_total = sum(PESOS_DO_INDICE[c] for c in componentes)
    valor = (
        sum(PESOS_DO_INDICE[c] * dados["valor"] for c, dados in componentes.items())
        / peso_total
    )

    bloqueados = grafo.get("conteudos_bloqueados", 0)
    amplificador = None
    if bloqueados:
        fator = 1 + AMPLIFICACAO_MAXIMA_DO_BLOQUEIO * min(
            1.0, bloqueados / BLOQUEIO_MAXIMO
        )
        valor = min(1.0, valor * fator)
        amplificador = {
            "fator": round(fator, 4),
            "base": f"trava {bloqueados} conteúdo(s) no grafo do agente 05",
        }

    return {
        "valor": round(valor, 4),
        "componentes": componentes,
        "amplificador_de_bloqueio": amplificador,
        "base": "; ".join(dados["base"] for dados in componentes.values()),
        "confianca": (
            "alta" if len(componentes) >= 3
            else "media" if len(componentes) == 2
            else "baixa"
        ),
    }


def _impacto(
    indice: float, grafo: dict, peso_da_disciplina: float | None, tempo_h: float | None
) -> dict:
    """Quanto a recuperação deste conteúdo move o desempenho geral.

    É uma estimativa declarada, não uma promessa: combina o peso da disciplina
    no edital com o que o conteúdo destrava. Sem peso do edital, o impacto sai
    apenas do grafo, e a base diz isso.
    """
    destravados = grafo.get("conteudos_bloqueados", 0)
    fatores: list[str] = []
    ganho = indice

    if peso_da_disciplina:
        ganho *= peso_da_disciplina
        fatores.append(f"disciplina com {peso_da_disciplina:.0%} do edital")
    if destravados:
        ganho *= 1 + min(destravados, BLOQUEIO_MAXIMO) / BLOQUEIO_MAXIMO
        fatores.append(f"destrava {destravados} conteúdo(s)")

    return {
        "ganho_estimado": round(ganho, 4),
        "conteudos_destravados": destravados,
        "esforco_estimado_h": tempo_h,
        "fatores": fatores,
        "base": (
            "índice de fraqueza ponderado pelo peso da disciplina e pelo que o "
            "conteúdo destrava"
            if peso_da_disciplina
            else "índice de fraqueza ponderado só pelo grafo; peso do edital não informado"
        ),
    }


def _urgencia(fraqueza: dict, ordem_no_plano: int | None, dias_para_prova: int | None) -> dict:
    """Urgência é o índice mais o que o calendário e o grafo impõem.

    Separada do índice de propósito: o conteúdo mais frágil não é
    necessariamente o próximo a tratar, e misturar as duas coisas esconderia
    justamente a diferença que interessa ao agente 23.
    """
    fatores: list[str] = []
    score = fraqueza["indice_de_fraqueza"]

    bloqueados = fraqueza["conteudos_dependentes_afetados"]
    if bloqueados:
        score *= 1 + 0.15 * min(len(bloqueados), BLOQUEIO_MAXIMO)
        fatores.append(f"{len(bloqueados)} conteúdo(s) dependem deste")

    if ordem_no_plano is not None:
        # Quanto mais cedo no plano, mais cedo o estudante esbarra nele.
        score *= 1 + max(0.0, (10 - ordem_no_plano) / 20)
        fatores.append(f"{ordem_no_plano}º conteúdo do plano de estudos")

    if dias_para_prova is not None and 0 < dias_para_prova <= DIAS_PARA_RETA_FINAL:
        score *= 1.25
        fatores.append(f"{dias_para_prova} dias para a prova")

    return {"score": round(score, 4), "fatores": fatores}


def _recomendacao(fraqueza: dict, medicao: dict, agendado: bool) -> dict:
    """Ação sugerida: a do nível, salvo domínio alto e retido, que é avançar."""
    nivel = fraqueza["nivel_de_prioridade"]
    classificacao = medicao.get("classificacao")

    if (
        nivel == "estavel"
        and classificacao == "avancado"
        and not medicao.get("esquecido")
    ):
        return {
            "acao": ACAO_AVANCAR,
            "base": "domínio avançado medido e nenhum sinal de esquecimento",
            "ja_agendado_para_revisao": agendado,
        }
    return {
        "acao": ACAO_POR_NIVEL[nivel],
        "base": f"nível {nivel} no Índice de Fraqueza",
        "ja_agendado_para_revisao": agendado,
    }


# --------------------------------------------------------------------------- #
# Histórico e continuidade
# --------------------------------------------------------------------------- #


def _do_mapa_anterior(mapa_anterior: dict) -> dict[str, dict]:
    return {
        como_texto(f.get("topico") or ""): f
        for f in mapa_anterior.get("fraquezas", [])
        if preenchido(f.get("topico"))
    }


def _historico_por_topico(campos: dict) -> dict[str, list[dict]]:
    """Desempenho registrado ao longo do tempo, por tópico."""
    por_topico: dict[str, list[dict]] = {}
    for chave in ("historico_desempenho", "resultados_exercicios", "historico_respostas"):
        for bruto in como_lista_de_dicts(campos.get(chave)):
            topico = bruto.get("topico") or bruto.get("conteudo")
            total = como_numero(bruto.get("total") or bruto.get("questoes"))
            acertos = como_numero(bruto.get("acertos"))
            if not preenchido(topico) or not total or acertos is None:
                continue
            por_topico.setdefault(como_texto(topico), []).append(
                {
                    "data": como_data(bruto.get("data")),
                    "taxa_acerto": acertos / total,
                    "amostra": total,
                }
            )
    for registros in por_topico.values():
        registros.sort(key=lambda r: (r["data"] is None, r["data"]))
    return por_topico


def _padrao_de_baixo_desempenho(registros: list[dict]) -> dict | None:
    """Baixo desempenho repetido é padrão; uma medição ruim é uma medição."""
    baixos = [r for r in registros if r["taxa_acerto"] < 0.6]
    if len(baixos) < 2:
        return None
    return {
        "ocorrencias": len(baixos),
        "medicoes": len(registros),
        "base": (
            f"{len(baixos)} de {len(registros)} medições abaixo de 60% de acerto"
        ),
    }


def _tendencia(indice_geral: float | None, mapa_anterior: dict) -> dict:
    anterior = (mapa_anterior.get("resumo_geral") or {}).get("indice_geral_de_fragilidade")
    if indice_geral is None or anterior is None:
        return {
            "disponivel": False,
            "tendencia": "indeterminada",
            "base": "nenhum mapa anterior informado para comparação",
        }
    variacao = indice_geral - anterior
    return {
        "disponivel": True,
        "tendencia": (
            "melhora" if variacao <= -LIMIAR_VARIACAO_RELEVANTE
            else "piora" if variacao >= LIMIAR_VARIACAO_RELEVANTE
            else "estavel"
        ),
        "indice_anterior": anterior,
        "variacao": round(variacao, 4),
        "base": f"índice geral de {anterior} para {indice_geral}",
    }


# --------------------------------------------------------------------------- #
# Entrada principal
# --------------------------------------------------------------------------- #

CONSUMIDORES = ["19", "21", "22", "23", "24"]


def _competencias_comprometidas(fraquezas: list[dict]) -> list[dict]:
    """Competências agregadas dos erros do agente 17, da pior para a melhor."""
    contagem: dict[str, dict] = {}
    for fraqueza in fraquezas:
        for competencia, quantidade in (fraqueza.get("competencias") or {}).items():
            registro = contagem.setdefault(
                competencia, {"competencia": competencia, "erros": 0, "topicos": []}
            )
            registro["erros"] += quantidade
            registro["topicos"].append(fraqueza["topico"])
    return sorted(contagem.values(), key=lambda c: -c["erros"])[:TAMANHO_DO_RANKING]


def _areas_de_risco(fraquezas: list[dict]) -> list[dict]:
    """Disciplinas cujo conjunto de conteúdos está frágil."""
    por_disciplina: dict[str, list[dict]] = {}
    for fraqueza in fraquezas:
        por_disciplina.setdefault(fraqueza["disciplina"] or "sem disciplina", []).append(
            fraqueza
        )

    areas = [
        {
            "disciplina": nome,
            "indice_medio": round(
                sum(f["indice_de_fraqueza"] for f in do_grupo) / len(do_grupo), 4
            ),
            "conteudos_criticos": sum(
                1 for f in do_grupo if f["nivel_de_prioridade"] in ("critico", NIVEL_MAXIMO)
            ),
            "conteudos_medidos": len(do_grupo),
        }
        for nome, do_grupo in por_disciplina.items()
    ]
    return sorted(areas, key=lambda a: -a["indice_medio"])


def _observacoes(
    fraquezas: list[dict], sem_evidencia: list[dict], tendencia: dict, erros: dict
) -> list[str]:
    observacoes: list[str] = []

    if not fraquezas:
        observacoes.append(
            "Nenhum conteúdo com evidência suficiente para receber índice: sem "
            "domínio medido, erro registrado ou dependência no grafo, não há "
            "fraqueza a declarar."
        )
        return observacoes

    if sem_evidencia:
        observacoes.append(
            f"{len(sem_evidencia)} conteúdo(s) ficaram fora do índice por falta de "
            "medição. Ausência de dado não foi lida como conteúdo estável."
        )
    baixa = [f for f in fraquezas if f["indice"]["confianca"] == "baixa"]
    if baixa:
        observacoes.append(
            f"{len(baixa)} índice(s) apoiados num componente só; a confiança de cada "
            "um está declarada em `indice.confianca`."
        )
    if not erros:
        observacoes.append(
            "Nenhum erro do agente 17 informado: a fragilidade foi medida sem o "
            "detalhe de causa, e competências comprometidas ficam vazias."
        )
    if not tendencia["disponivel"]:
        observacoes.append(f"Tendência não declarada: {tendencia['base']}.")
    return observacoes


def mapear(entradas: dict[str, Any], hoje: date | None = None) -> dict[str, Any]:
    """Constrói o Mapa Dinâmico de Fraquezas."""
    hoje = hoje or date.today()
    dados = entradas.get("dados_usuario", {}) or {}
    campos = {k: v for k, v in dados.items() if k != "perfil"}
    if isinstance(dados.get("perfil"), dict):
        campos = {**campos, **dados["perfil"]}

    anteriores = entradas.get("saidas_anteriores", {})
    mapa_estrategico = anteriores.get("02", {}) or {}
    mapa_conhecimento = anteriores.get("03", {}) or {}
    arvore = anteriores.get("04", {}) or {}
    grafo = anteriores.get("05", {}) or {}
    plano = anteriores.get("06", {}) or {}
    relatorio = anteriores.get("12", {}) or {}
    revisoes = anteriores.get("15", {}) or {}
    relatorio_de_erros = anteriores.get("17", {}) or {}

    posicao = _posicao_curricular(arvore)
    no_grafo = _posicao_no_grafo(grafo)
    medicoes = _medicoes(mapa_conhecimento, relatorio)
    erros = _erros_por_topico(relatorio_de_erros)
    historico = _historico_por_topico(campos)
    mapa_anterior = campos.get("mapa_de_fraquezas_anterior") or {}
    anteriores_por_topico = _do_mapa_anterior(mapa_anterior)

    pesos = _pesos_por_disciplina(mapa_estrategico)
    ordem_no_plano = _ordem_no_plano(plano)
    agendados = _agendados(revisoes)
    dias_para_prova = (mapa_estrategico.get("prazo_final") or {}).get("dias_restantes")

    fraquezas: list[dict] = []
    sem_evidencia: list[dict] = []

    for chave in sorted(set(medicoes) | set(posicao) | set(erros)):
        medicao = medicoes.get(chave, {})
        local = posicao.get(chave, {})
        do_grafo = no_grafo.get(chave, {})
        do_erro = erros.get(chave, {})
        nome = medicao.get("topico") or local.get("topico") or chave

        componentes = _componentes(medicao, do_erro, do_grafo)
        if not componentes:
            sem_evidencia.append(
                {
                    "topico": nome,
                    "disciplina": local.get("disciplina") or medicao.get("disciplina"),
                    "motivo": (
                        "sem domínio medido, sem erro registrado e sem dependentes "
                        "no grafo"
                    ),
                }
            )
            continue

        indice = _indice(componentes, do_grafo)
        anterior = anteriores_por_topico.get(chave, {})
        esquecimentos = int(anterior.get("frequencia_de_esquecimento") or 0) + (
            1 if medicao.get("esquecido") else 0
        )

        fraqueza = {
            "id": f"w{len(fraquezas) + 1:03d}",
            "disciplina": local.get("disciplina") or medicao.get("disciplina"),
            "modulo": local.get("modulo"),
            "topico": nome,
            "indice_de_fraqueza": indice["valor"],
            "indice": indice,
            "nivel_de_prioridade": _nivel(indice["valor"]),
            "frequencia_de_erros": do_erro.get("quantidade", 0)
            or medicao.get("frequencia_de_erros_do_12", 0),
            "erros_recorrentes": do_erro.get("recorrentes", 0),
            "tipos_de_erro": do_erro.get("tipos", {}),
            "competencias": do_erro.get("competencias", {}),
            "frequencia_de_esquecimento": esquecimentos,
            "base_do_esquecimento": (
                f"{esquecimentos} observação(ões) de esquecimento acumuladas nos mapas"
                if esquecimentos
                else "nenhuma observação de esquecimento"
            ),
            "conteudos_dependentes_afetados": do_grafo.get("dependentes_diretos", []),
            "padrao_de_baixo_desempenho": _padrao_de_baixo_desempenho(
                historico.get(chave, [])
            ),
            "medicoes_no_historico": len(historico.get(chave, [])),
            "status_curricular": local.get("status"),
        }
        fraqueza["impacto_na_aprendizagem"] = _impacto(
            indice["valor"],
            do_grafo,
            pesos.get(como_texto(fraqueza["disciplina"] or "")),
            _tempo_estimado(arvore, chave),
        )
        fraqueza["urgencia"] = _urgencia(
            fraqueza, ordem_no_plano.get(chave), dias_para_prova
        )
        fraqueza["recomendacao"] = _recomendacao(
            fraqueza, medicao, chave in agendados
        )
        if anterior:
            fraqueza["variacao"] = {
                "indice_anterior": anterior.get("indice_de_fraqueza"),
                "variacao": round(
                    indice["valor"] - (anterior.get("indice_de_fraqueza") or 0), 4
                ),
                "nivel_anterior": anterior.get("nivel_de_prioridade"),
            }
        fraquezas.append(fraqueza)

    por_indice = sorted(fraquezas, key=lambda f: -f["indice_de_fraqueza"])
    por_urgencia = sorted(fraquezas, key=lambda f: -f["urgencia"]["score"])
    criticos = [
        f for f in fraquezas if f["nivel_de_prioridade"] in ("critico", NIVEL_MAXIMO)
    ]
    indice_geral = (
        round(sum(f["indice_de_fraqueza"] for f in fraquezas) / len(fraquezas), 4)
        if fraquezas
        else None
    )
    tendencia = _tendencia(indice_geral, mapa_anterior)

    return {
        "atualizado_em": hoje.isoformat(),
        "resumo_geral": {
            "indice_geral_de_fragilidade": indice_geral,
            "conteudos_avaliados": len(fraquezas),
            "conteudos_criticos": len(criticos),
            "conteudos_sem_evidencia": len(sem_evidencia),
            "distribuicao_por_nivel": {
                nivel: sum(1 for f in fraquezas if f["nivel_de_prioridade"] == nivel)
                for nivel in NIVEIS
                if any(f["nivel_de_prioridade"] == nivel for f in fraquezas)
            },
            "tendencia_de_evolucao": tendencia,
            "principais_areas_de_risco": _areas_de_risco(fraquezas)[:3],
        },
        "fraquezas": por_indice,
        "conteudos_sem_evidencia": sem_evidencia,
        "ranking": {
            "maiores_fraquezas": [
                {
                    "posicao": posicao_no_ranking,
                    "topico": f["topico"],
                    "disciplina": f["disciplina"],
                    "indice_de_fraqueza": f["indice_de_fraqueza"],
                    "nivel": f["nivel_de_prioridade"],
                }
                for posicao_no_ranking, f in enumerate(
                    por_indice[:TAMANHO_DO_RANKING], start=1
                )
            ],
            "mais_urgentes": [
                {
                    "posicao": posicao_no_ranking,
                    "topico": f["topico"],
                    "disciplina": f["disciplina"],
                    "score_de_urgencia": f["urgencia"]["score"],
                    "fatores": f["urgencia"]["fatores"],
                }
                for posicao_no_ranking, f in enumerate(
                    por_urgencia[:TAMANHO_DO_RANKING], start=1
                )
            ],
            "competencias_mais_comprometidas": _competencias_comprometidas(fraquezas),
            "base_das_listas": (
                "maiores fraquezas ordenam pelo índice; mais urgentes ponderam o "
                "índice pelo grafo, pela posição no plano e pelo prazo da prova"
            ),
        },
        "recomendacoes": _recomendacoes_agrupadas(por_urgencia),
        "consumido_por": CONSUMIDORES,
        "observacoes": _observacoes(fraquezas, sem_evidencia, tendencia, erros),
        "lacunas": [] if fraquezas else ["medicoes_de_desempenho"],
        "confiabilidade": (
            "alta" if fraquezas and erros and historico
            else "media" if fraquezas
            else "baixa"
        ),
        "constantes_aplicadas": {
            "pesos_do_indice": PESOS_DO_INDICE,
            "amplificacao_maxima_do_bloqueio": AMPLIFICACAO_MAXIMA_DO_BLOQUEIO,
            "valor_por_classificacao": VALOR_POR_CLASSIFICACAO,
            "faixas": {nome: limite for limite, nome in FAIXAS},
            "bloqueio_maximo": BLOQUEIO_MAXIMO,
            "limiar_decaimento_relevante": LIMIAR_DECAIMENTO_RELEVANTE,
            "limiar_variacao_relevante": LIMIAR_VARIACAO_RELEVANTE,
            "tamanho_do_ranking": TAMANHO_DO_RANKING,
            "acao_por_nivel": ACAO_POR_NIVEL,
        },
    }


def _recomendacoes_agrupadas(por_urgencia: list[dict]) -> dict[str, list[dict]]:
    """Conteúdos agrupados pela ação sugerida, na ordem de urgência."""
    agrupadas: dict[str, list[dict]] = {acao: [] for acao in ACOES}
    for fraqueza in por_urgencia:
        agrupadas[fraqueza["recomendacao"]["acao"]].append(
            {
                "topico": fraqueza["topico"],
                "disciplina": fraqueza["disciplina"],
                "indice_de_fraqueza": fraqueza["indice_de_fraqueza"],
                "base": fraqueza["recomendacao"]["base"],
                "ja_agendado_para_revisao": fraqueza["recomendacao"][
                    "ja_agendado_para_revisao"
                ],
            }
        )
    return {acao: itens for acao, itens in agrupadas.items() if itens}


def _pesos_por_disciplina(mapa_estrategico: dict) -> dict[str, float]:
    pesos = {
        como_texto(d["nome"]): float(d.get("questoes") or d.get("peso") or 0)
        for d in mapa_estrategico.get("disciplinas", [])
    }
    total = sum(pesos.values())
    return {nome: valor / total for nome, valor in pesos.items()} if total else {}


def _ordem_no_plano(plano: dict) -> dict[str, int]:
    """Posição de cada conteúdo na sequência do Plano de Estudos.

    Só sessões de estudo de conteúdo contam: exercícios e revisões do dia
    apontam para a disciplina inteira, não para o tópico, e entrariam como
    conteúdos fantasmas na ordem.
    """
    ordem: dict[str, int] = {}
    for dia in plano.get("cronograma", []):
        for sessao in dia.get("sessoes", []):
            if sessao.get("tipo") != "conteudo":
                continue
            chave = como_texto(sessao.get("conteudo") or "")
            if chave and chave not in ordem:
                ordem[chave] = len(ordem) + 1
    return ordem


def _agendados(revisoes: dict) -> set[str]:
    return {
        como_texto(conteudo.get("topico") or "")
        for sessao in revisoes.get("sessoes", [])
        for conteudo in sessao.get("conteudos", [])
    }


def _tempo_estimado(arvore: dict, chave: str) -> float | None:
    for disciplina in arvore.get("disciplinas", []):
        for modulo in disciplina.get("modulos", []):
            for topico in modulo.get("topicos", []):
                if como_texto(topico["nome"]) == chave:
                    return topico.get("tempo_estimado_h")
    return None


__all__ = [
    "ACAO_POR_NIVEL",
    "AMPLIFICACAO_MAXIMA_DO_BLOQUEIO",
    "BLOQUEIO_MAXIMO",
    "FAIXAS",
    "NIVEIS",
    "NIVEL_MAXIMO",
    "PESOS_DO_INDICE",
    "TAMANHO_DO_RANKING",
    "VALOR_POR_CLASSIFICACAO",
    "mapear",
]
