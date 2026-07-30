"""Agente 04 — Curriculum Builder.

Única responsabilidade: transformar o objetivo em uma Árvore Curricular
Inteligente — disciplina → módulo → tópico → subtópico → microtópico. Não
ensina, não cria cronograma, não gera aulas, exercícios ou resumos.

Duas decisões estruturais:

* **A ordem do edital é lei.** Nada é reordenado; a ordem de aparição vira
  ``ordem_recomendada``.
* **Nível não informado não é inventado.** Se o edital para no tópico, os
  subtópicos e microtópicos ficam vazios e o nó entra em
  ``pendencias_de_detalhamento`` — do mesmo jeito que o agente 03 pede
  diagnóstico em vez de estimar nível.
"""

from __future__ import annotations

from typing import Any

from app.studyos.agentes.comum import (
    como_lista,
    como_texto,
    filhos_estruturais as _filhos,
    preenchido,
)

# --------------------------------------------------------------------------- #
# Constantes declaradas
# --------------------------------------------------------------------------- #

#: Tempo médio para aprender uma unidade de cada nível, quando não há
#: detalhamento abaixo dela para somar.
HORAS_POR_MICROTOPICO = 0.5
HORAS_POR_SUBTOPICO_SEM_DETALHE = 1.0
HORAS_POR_TOPICO_SEM_DETALHE = 2.5

DIFICULDADES = ("muito_facil", "facil", "medio", "dificil", "muito_dificil")

#: Ponto de partida da dificuldade conforme o domínio medido pelo agente 03.
DIFICULDADE_POR_DOMINIO: dict[str, str] = {
    "avancado": "muito_facil",
    "intermediario": "facil",
    "basico": "medio",
    "nao_conhece": "dificil",
    "indeterminado": "medio",
}

IMPORTANCIAS = ("baixa", "media", "alta", "essencial")

#: Importância da disciplina conforme a prioridade vinda do agente 02.
IMPORTANCIA_POR_PRIORIDADE: dict[str, str] = {
    "alta": "essencial",
    "media": "alta",
    "baixa": "media",
}

STATUS_POR_DOMINIO: dict[str, str] = {
    "avancado": "dominado",
    "intermediario": "em_andamento",
    "basico": "em_andamento",
    "nao_conhece": "nao_iniciado",
    "indeterminado": "nao_iniciado",
}

def _ajustar(escala: tuple[str, ...], valor: str, passos: int) -> str:
    indice = escala.index(valor) if valor in escala else len(escala) // 2
    return escala[max(0, min(len(escala) - 1, indice + passos))]


# --------------------------------------------------------------------------- #
# Leitura da estrutura declarada
# --------------------------------------------------------------------------- #


def _fonte_da_disciplina(nome: str, edital: Any, matriz: Any) -> tuple[Any, str]:
    """Localiza o bloco bruto da disciplina no edital ou na matriz curricular."""
    chave = como_texto(nome)
    for fonte, rotulo in ((edital, "edital"), (matriz, "matriz_curricular")):
        if isinstance(fonte, dict):
            if preenchido(fonte.get("disciplinas")):
                achado, _ = _fonte_da_disciplina(nome, fonte["disciplinas"], None)
                if achado is not None:
                    return achado, rotulo
            for candidato, conteudo in fonte.items():
                if como_texto(candidato) == chave:
                    return conteudo, rotulo
        elif isinstance(fonte, (list, tuple)):
            for item in fonte:
                if isinstance(item, dict):
                    candidato = (
                        item.get("nome") or item.get("disciplina") or item.get("materia")
                    )
                    if candidato and como_texto(candidato) == chave:
                        return item, rotulo
    return None, "ausente"


# --------------------------------------------------------------------------- #
# Índices vindos do agente 03
# --------------------------------------------------------------------------- #


def _indice_conhecimento(mapa: dict) -> dict[str, dict]:
    """`disciplina|topico` -> dados do tópico medidos pelo agente 03."""
    indice: dict[str, dict] = {}
    for disciplina in mapa.get("disciplinas", []):
        chave_disciplina = como_texto(disciplina["disciplina"])
        indice[chave_disciplina] = {
            "percentual_dominio": disciplina.get("percentual_dominio"),
            "grau_dificuldade": (disciplina.get("grau_dificuldade") or {}).get("grau"),
        }
        for topico in disciplina.get("topicos", []):
            indice[f"{chave_disciplina}|{como_texto(topico['topico'])}"] = topico
    return indice


# --------------------------------------------------------------------------- #
# Construção da árvore
# --------------------------------------------------------------------------- #


def _microtopicos(
    bruto: Any, mapa_global: dict[str, list[str]], caminho: str, status_herdado: str
) -> list[dict]:
    nomes = [nome for nome, _ in _filhos(bruto)] or como_lista(mapa_global.get(caminho))
    return [
        {
            "nome": nome,
            "status": status_herdado,
            "tempo_estimado_h": HORAS_POR_MICROTOPICO,
        }
        for nome in nomes
    ]


def _subtopicos(
    bruto: Any,
    subtopicos_globais: dict[str, list[str]],
    microtopicos_globais: dict[str, list[str]],
    topico: str,
    status_herdado: str,
    pendencias: list[dict],
    disciplina: str,
) -> list[dict]:
    pares = _filhos(bruto)
    if not pares:
        pares = [
            (nome, None)
            for nome in como_lista(subtopicos_globais.get(como_texto(topico)))
        ]

    if not pares:
        pendencias.append(
            {
                "disciplina": disciplina,
                "topico": topico,
                "nivel_faltante": "subtopicos",
                "acao": "detalhar a partir do edital, da bibliografia ou da matriz curricular",
            }
        )
        return []

    subtopicos: list[dict] = []
    for nome, filhos in pares:
        caminho = f"{como_texto(topico)}|{como_texto(nome)}"
        micro = _microtopicos(filhos, microtopicos_globais, caminho, status_herdado)
        if not micro:
            micro = _microtopicos(
                None, microtopicos_globais, como_texto(nome), status_herdado
            )
        if not micro:
            pendencias.append(
                {
                    "disciplina": disciplina,
                    "topico": topico,
                    "subtopico": nome,
                    "nivel_faltante": "microtopicos",
                    "acao": "detalhar a partir do edital, da bibliografia ou da matriz curricular",
                }
            )

        tempo = (
            round(sum(m["tempo_estimado_h"] for m in micro), 2)
            if micro
            else HORAS_POR_SUBTOPICO_SEM_DETALHE
        )
        subtopicos.append(
            {
                "nome": nome,
                "objetivo_de_aprendizagem": f"Dominar {nome} no contexto de {topico}",
                "tempo_estimado_h": tempo,
                "status": _consolidar_status([m["status"] for m in micro], status_herdado),
                "microtopicos": micro,
                "detalhamento_pendente": not micro,
            }
        )
    return subtopicos


def _consolidar_status(status_filhos: list[str], padrao: str) -> str:
    if not status_filhos:
        return padrao
    if all(s == "dominado" for s in status_filhos):
        return "dominado"
    if any(s in ("dominado", "em_andamento") for s in status_filhos):
        return "em_andamento"
    return "nao_iniciado"


def _dificuldade(medicao: dict | None, percepcao: bool, volume: int) -> dict:
    dominio = (medicao or {}).get("classificacao", "indeterminado")
    grau = DIFICULDADE_POR_DOMINIO.get(dominio, "medio")
    fatores = [f"domínio medido: {dominio}"]

    if percepcao:
        grau = _ajustar(DIFICULDADES, grau, +1)
        fatores.append("dificuldade declarada pelo estudante")
    if (medicao or {}).get("esquecido"):
        # Sem novo agravo: o agente 03 já rebaixou a classificação por
        # esquecimento, e cobrar duas vezes pelo mesmo fato distorceria o grau.
        fatores.append("classificação já rebaixada por esquecimento (agente 03)")
    if volume >= 5:
        grau = _ajustar(DIFICULDADES, grau, +1)
        fatores.append(f"{volume} subtópicos")

    return {
        "grau": grau,
        "fatores": fatores,
        "confianca": "media" if dominio != "indeterminado" else "baixa",
    }


def _importancia_do_topico(
    base: str, nome: str, obrigatorios: set[str], opcionais: set[str]
) -> dict:
    chave = como_texto(nome)
    if chave in obrigatorios:
        return {"importancia": "essencial", "base": "listado como conteúdo obrigatório"}
    if chave in opcionais:
        return {"importancia": "baixa", "base": "listado como conteúdo opcional"}
    return {"importancia": base, "base": "herdada da importância da disciplina"}


def _montar_disciplina(
    disciplina: dict,
    prioridade_02: str | None,
    bruto: Any,
    origem: str,
    conhecimento: dict[str, dict],
    subtopicos_globais: dict[str, list[str]],
    microtopicos_globais: dict[str, list[str]],
    pre_requisitos: dict[str, list[str]],
    obrigatorios: set[str],
    opcionais: set[str],
    percepcao_dificuldade: bool,
    pendencias: list[dict],
) -> dict:
    nome = disciplina["nome"]
    chave_disciplina = como_texto(nome)
    importancia_base = IMPORTANCIA_POR_PRIORIDADE.get(prioridade_02 or "media", "alta")

    pares_modulos: list[tuple[str, Any]] = []
    if isinstance(bruto, dict) and preenchido(bruto.get("modulos")):
        pares_modulos = _filhos(bruto["modulos"])
        origem_modulos = origem
    else:
        # Sem modularização declarada, a disciplina é um módulo único: agrupar
        # tópicos por conta própria seria decidir pedagogia, não estrutura.
        conteudo = bruto if preenchido(bruto) else disciplina["topicos"]
        pares_modulos = [(f"{nome} — módulo único", conteudo)]
        origem_modulos = "modulo_unico_por_ausencia_de_modularizacao"

    modulos: list[dict] = []
    for ordem, (nome_modulo, filhos_modulo) in enumerate(pares_modulos, start=1):
        pares_topicos = _filhos(filhos_modulo) or [
            (t, None) for t in disciplina["topicos"]
        ]

        topicos: list[dict] = []
        for nome_topico, filhos_topico in pares_topicos:
            medicao = conhecimento.get(f"{chave_disciplina}|{como_texto(nome_topico)}")
            status_topico = STATUS_POR_DOMINIO.get(
                (medicao or {}).get("classificacao", "indeterminado"), "nao_iniciado"
            )

            subtopicos = _subtopicos(
                filhos_topico,
                subtopicos_globais,
                microtopicos_globais,
                nome_topico,
                status_topico,
                pendencias,
                nome,
            )
            tempo_topico = (
                round(sum(s["tempo_estimado_h"] for s in subtopicos), 2)
                if subtopicos
                else HORAS_POR_TOPICO_SEM_DETALHE
            )
            importancia = _importancia_do_topico(
                importancia_base, nome_topico, obrigatorios, opcionais
            )

            topicos.append(
                {
                    "nome": nome_topico,
                    "pre_requisitos": como_lista(
                        pre_requisitos.get(como_texto(nome_topico))
                    ),
                    "dificuldade": _dificuldade(
                        medicao, percepcao_dificuldade, len(subtopicos)
                    ),
                    "importancia": importancia["importancia"],
                    "base_da_importancia": importancia["base"],
                    "obrigatorio": importancia["importancia"] != "baixa"
                    or como_texto(nome_topico) in obrigatorios,
                    "status": _consolidar_status(
                        [s["status"] for s in subtopicos], status_topico
                    ),
                    "tempo_estimado_h": tempo_topico,
                    "origem": origem if origem != "ausente" else "agente_02",
                    "subtopicos": subtopicos,
                    "detalhamento_pendente": not subtopicos,
                }
            )

        modulos.append(
            {
                "nome": nome_modulo,
                "ordem_recomendada": ordem,
                "tempo_estimado_h": round(sum(t["tempo_estimado_h"] for t in topicos), 2),
                "status": _consolidar_status(
                    [t["status"] for t in topicos], "nao_iniciado"
                ),
                "origem": origem_modulos,
                "topicos": topicos,
            }
        )

    todos_topicos = [t for m in modulos for t in m["topicos"]]
    tempo_total = round(sum(m["tempo_estimado_h"] for m in modulos), 2)
    tempo_pendente = round(
        sum(t["tempo_estimado_h"] for t in todos_topicos if t["status"] != "dominado"), 2
    )

    return {
        "nome": nome,
        "importancia": importancia_base,
        "peso": disciplina.get("peso") or disciplina.get("questoes"),
        "tempo_estimado_h": tempo_total,
        "tempo_pendente_h": tempo_pendente,
        "prioridade_do_agente_02": prioridade_02,
        "percentual_dominio_do_agente_03": (
            conhecimento.get(chave_disciplina, {}).get("percentual_dominio")
        ),
        "origem_da_estrutura": origem,
        "status": _consolidar_status([m["status"] for m in modulos], "nao_iniciado"),
        "modulos": modulos,
    }


# --------------------------------------------------------------------------- #
# Entrada principal
# --------------------------------------------------------------------------- #


def _mapa_de_listas(bruto: Any) -> dict[str, list[str]]:
    if not isinstance(bruto, dict):
        return {}
    return {como_texto(chave): como_lista(valor) for chave, valor in bruto.items()}


def _contar(arvore: list[dict]) -> dict[str, int]:
    modulos = [m for d in arvore for m in d["modulos"]]
    topicos = [t for m in modulos for t in m["topicos"]]
    subtopicos = [s for t in topicos for s in t["subtopicos"]]
    microtopicos = [mt for s in subtopicos for mt in s["microtopicos"]]
    return {
        "disciplinas": len(arvore),
        "modulos": len(modulos),
        "topicos": len(topicos),
        "subtopicos": len(subtopicos),
        "microtopicos": len(microtopicos),
    }


def construir(entradas: dict[str, Any]) -> dict[str, Any]:
    """Constrói a Árvore Curricular Estruturada."""
    dados = entradas.get("dados_usuario", {}) or {}
    campos = {k: v for k, v in dados.items() if k != "perfil"}
    if isinstance(dados.get("perfil"), dict):
        campos = {**campos, **dados["perfil"]}

    anteriores = entradas.get("saidas_anteriores", {})
    perfil = anteriores.get("01", {}) or {}
    mapa_estrategico = anteriores.get("02", {}) or {}
    mapa_conhecimento = anteriores.get("03", {}) or {}

    disciplinas_alvo = mapa_estrategico.get("disciplinas", [])
    prioridades = {
        como_texto(p["disciplina"]): p["prioridade"]
        for p in mapa_estrategico.get("prioridade_disciplinas", [])
    }
    conhecimento = _indice_conhecimento(mapa_conhecimento)

    edital = campos.get("edital")
    matriz = campos.get("matriz_curricular") or campos.get("bibliografia_estruturada")
    subtopicos_globais = _mapa_de_listas(campos.get("subtopicos"))
    microtopicos_globais = _mapa_de_listas(campos.get("microtopicos"))
    pre_requisitos = _mapa_de_listas(campos.get("pre_requisitos"))
    obrigatorios = {como_texto(c) for c in como_lista(campos.get("conteudos_obrigatorios"))}
    opcionais = {como_texto(c) for c in como_lista(campos.get("conteudos_opcionais"))}
    dificuldades_declaradas = {
        como_texto(d) for d in como_lista(campos.get("disciplinas_dificuldade"))
    }

    pendencias: list[dict] = []
    arvore: list[dict] = []
    for disciplina in disciplinas_alvo:
        bruto, origem = _fonte_da_disciplina(disciplina["nome"], edital, matriz)
        arvore.append(
            _montar_disciplina(
                disciplina,
                prioridades.get(como_texto(disciplina["nome"])),
                bruto,
                origem,
                conhecimento,
                subtopicos_globais,
                microtopicos_globais,
                pre_requisitos,
                obrigatorios,
                opcionais,
                como_texto(disciplina["nome"]) in dificuldades_declaradas,
                pendencias,
            )
        )

    # Regra: nenhum conteúdo obrigatório pode sumir na montagem.
    esperados = {
        (como_texto(d["nome"]), como_texto(t))
        for d in disciplinas_alvo
        for t in d["topicos"]
    }
    presentes = {
        (como_texto(d["nome"]), como_texto(t["nome"]))
        for d in arvore
        for m in d["modulos"]
        for t in m["topicos"]
    }
    faltando = sorted(esperados - presentes)

    totais = _contar(arvore)
    todos_topicos = [t for d in arvore for m in d["modulos"] for t in m["topicos"]]

    referencia = "ausente"
    if any(d["origem_da_estrutura"] == "edital" for d in arvore):
        referencia = "edital"
    elif any(d["origem_da_estrutura"] == "matriz_curricular" for d in arvore):
        referencia = "matriz_curricular"
    elif disciplinas_alvo:
        referencia = mapa_estrategico.get("cobertura_das_disciplinas", "agente_02")

    observacoes: list[str] = []
    if not disciplinas_alvo:
        observacoes.append(
            "Nenhuma disciplina recebida do agente 02: não há currículo a montar."
        )
    if referencia not in ("edital", "matriz_curricular") and disciplinas_alvo:
        observacoes.append(
            "Sem edital nem matriz curricular estruturada: a árvore foi montada "
            "apenas com as disciplinas e tópicos conhecidos. Para completar os "
            "níveis inferiores, informe uma referência reconhecida da área."
        )
    if any(d["origem_da_estrutura"] != "ausente" for d in arvore) and all(
        m["origem"] == "modulo_unico_por_ausencia_de_modularizacao"
        for d in arvore
        for m in d["modulos"]
    ):
        observacoes.append(
            "Nenhuma modularização declarada: cada disciplina virou um módulo "
            "único, preservando a ordem original dos tópicos."
        )
    if pendencias:
        observacoes.append(
            f"{len(pendencias)} nó(s) sem detalhamento nos níveis inferiores. "
            "Subtópicos e microtópicos não foram inventados."
        )
    if faltando:
        observacoes.append(
            f"{len(faltando)} tópico(s) obrigatório(s) não entraram na árvore — "
            "verificar a fonte da estrutura."
        )

    lacunas: list[str] = []
    if not mapa_estrategico:
        lacunas.append("mapa_estrategico_do_agente_02")
    if not mapa_conhecimento:
        lacunas.append("mapa_de_conhecimento_do_agente_03")
    if not perfil:
        lacunas.append("perfil_cognitivo_do_agente_01")
    if not preenchido(edital) and not preenchido(matriz):
        lacunas.append("edital_ou_matriz_curricular")
    if not subtopicos_globais:
        lacunas.append("subtopicos")
    if not microtopicos_globais:
        lacunas.append("microtopicos")

    return {
        "objetivo": mapa_estrategico.get("objetivo_principal"),
        "categoria_objetivo": (mapa_estrategico.get("categoria_objetivo") or {}).get(
            "categoria"
        ),
        "referencia_utilizada": referencia,
        "disciplinas": arvore,
        "totais": totais,
        "tempo_total_estimado_h": round(
            sum(d["tempo_estimado_h"] for d in arvore), 2
        ),
        "tempo_pendente_estimado_h": round(
            sum(d["tempo_pendente_h"] for d in arvore), 2
        ),
        "conteudos_obrigatorios": [
            t["nome"] for t in todos_topicos if t["obrigatorio"]
        ],
        "conteudos_opcionais": [
            t["nome"] for t in todos_topicos if not t["obrigatorio"]
        ],
        "conteudos_dominados": [
            t["nome"] for t in todos_topicos if t["status"] == "dominado"
        ],
        "conteudos_pendentes": [
            t["nome"] for t in todos_topicos if t["status"] != "dominado"
        ],
        "pendencias_de_detalhamento": pendencias,
        "integridade": {
            "topicos_esperados": len(esperados),
            "topicos_presentes": len(presentes),
            "faltando": [f"{d} / {t}" for d, t in faltando],
            "ordem_preservada": True,
            "ok": not faltando,
        },
        "consumido_por": ["05", "06", "07", "09", "10", "11", "14", "15", "16", "23"],
        "observacoes": observacoes,
        "lacunas": lacunas,
        "confiabilidade": (
            "alta"
            if referencia == "edital" and not pendencias
            else "media"
            if arvore
            else "baixa"
        ),
        "constantes_aplicadas": {
            "horas_por_microtopico": HORAS_POR_MICROTOPICO,
            "horas_por_subtopico_sem_detalhe": HORAS_POR_SUBTOPICO_SEM_DETALHE,
            "horas_por_topico_sem_detalhe": HORAS_POR_TOPICO_SEM_DETALHE,
            "escala_dificuldade": list(DIFICULDADES),
            "escala_importancia": list(IMPORTANCIAS),
        },
    }


__all__ = ["construir"]
