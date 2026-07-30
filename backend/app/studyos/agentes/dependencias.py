"""Agente 05 — Dependency Mapper.

Única responsabilidade: transformar a Árvore Curricular em um Grafo de
Aprendizagem. Não ensina, não cria cronograma, não gera exercícios, não
responde dúvidas.

Duas decisões que governam o módulo:

* **Aresta só existe onde há pré-requisito declarado.** Ordem no edital é
  ordem, não dependência: tratar irmãos consecutivos como pré-requisitos
  inventaria dependências e destruiria todo o paralelismo. A ordem curricular
  sobrevive como critério de desempate na sequência sugerida.
* **Contenção não é pré-requisito.** Um tópico não depende do módulo que o
  contém; mas se o pai está bloqueado, o filho herda o bloqueio — registrado
  como bloqueio por ancestral, sem criar aresta nova.
"""

from __future__ import annotations

from typing import Any

from app.studyos.agentes.comum import como_lista, como_texto

TIPOS = ("disciplina", "modulo", "topico", "subtopico", "microtopico")

STATUS_CONCLUIDO = "concluido"
STATUS_DISPONIVEL = "disponivel"
STATUS_BLOQUEADO = "bloqueado"

#: Quantidade de caminhos alternativos reportados além do principal.
MAXIMO_CAMINHOS_ALTERNATIVOS = 5


# --------------------------------------------------------------------------- #
# Achatamento da árvore em nós
# --------------------------------------------------------------------------- #


def _no(
    identificador: str,
    nome: str,
    tipo: str,
    pai: str | None,
    ordem: int,
    disciplina: str,
    *,
    dificuldade: str | None = None,
    importancia: str | None = None,
    obrigatorio: bool = True,
    tempo: float = 0.0,
    status_curricular: str = "nao_iniciado",
    pre_requisitos_nomes: list[str] | None = None,
) -> dict:
    return {
        "id": identificador,
        "nome": nome,
        "tipo": tipo,
        "disciplina": disciplina,
        "contido_em": pai,
        "ordem_curricular": ordem,
        "dificuldade": dificuldade,
        "importancia": importancia,
        "obrigatorio": obrigatorio,
        "tempo_estimado_h": tempo,
        "status_curricular": status_curricular,
        "pre_requisitos_nomes": pre_requisitos_nomes or [],
        "pre_requisitos": [],
        "dependentes": [],
    }


def _achatar(arvore: dict, pre_requisitos_globais: dict[str, list[str]]) -> list[dict]:
    nos: list[dict] = []
    ordem = 0

    def declarados(nome: str, ja_declarados: list[str] | None = None) -> list[str]:
        return list(ja_declarados or []) or como_lista(
            pre_requisitos_globais.get(como_texto(nome))
        )

    for indice_d, disciplina in enumerate(arvore.get("disciplinas", []), start=1):
        id_disciplina = f"d{indice_d}"
        ordem += 1
        nos.append(
            _no(
                id_disciplina,
                disciplina["nome"],
                "disciplina",
                None,
                ordem,
                disciplina["nome"],
                importancia=disciplina.get("importancia"),
                tempo=disciplina.get("tempo_estimado_h", 0.0),
                status_curricular=disciplina.get("status", "nao_iniciado"),
                pre_requisitos_nomes=declarados(disciplina["nome"]),
            )
        )

        for indice_m, modulo in enumerate(disciplina.get("modulos", []), start=1):
            id_modulo = f"{id_disciplina}.m{indice_m}"
            ordem += 1
            nos.append(
                _no(
                    id_modulo,
                    modulo["nome"],
                    "modulo",
                    id_disciplina,
                    ordem,
                    disciplina["nome"],
                    importancia=disciplina.get("importancia"),
                    tempo=modulo.get("tempo_estimado_h", 0.0),
                    status_curricular=modulo.get("status", "nao_iniciado"),
                    pre_requisitos_nomes=declarados(modulo["nome"]),
                )
            )

            for indice_t, topico in enumerate(modulo.get("topicos", []), start=1):
                id_topico = f"{id_modulo}.t{indice_t}"
                ordem += 1
                nos.append(
                    _no(
                        id_topico,
                        topico["nome"],
                        "topico",
                        id_modulo,
                        ordem,
                        disciplina["nome"],
                        dificuldade=(topico.get("dificuldade") or {}).get("grau"),
                        importancia=topico.get("importancia"),
                        obrigatorio=topico.get("obrigatorio", True),
                        tempo=topico.get("tempo_estimado_h", 0.0),
                        status_curricular=topico.get("status", "nao_iniciado"),
                        pre_requisitos_nomes=declarados(
                            topico["nome"], topico.get("pre_requisitos")
                        ),
                    )
                )

                for indice_s, subtopico in enumerate(
                    topico.get("subtopicos", []), start=1
                ):
                    id_subtopico = f"{id_topico}.s{indice_s}"
                    ordem += 1
                    nos.append(
                        _no(
                            id_subtopico,
                            subtopico["nome"],
                            "subtopico",
                            id_topico,
                            ordem,
                            disciplina["nome"],
                            dificuldade=(topico.get("dificuldade") or {}).get("grau"),
                            importancia=topico.get("importancia"),
                            obrigatorio=topico.get("obrigatorio", True),
                            tempo=subtopico.get("tempo_estimado_h", 0.0),
                            status_curricular=subtopico.get("status", "nao_iniciado"),
                            pre_requisitos_nomes=declarados(subtopico["nome"]),
                        )
                    )

                    for indice_u, micro in enumerate(
                        subtopico.get("microtopicos", []), start=1
                    ):
                        id_micro = f"{id_subtopico}.u{indice_u}"
                        ordem += 1
                        nos.append(
                            _no(
                                id_micro,
                                micro["nome"],
                                "microtopico",
                                id_subtopico,
                                ordem,
                                disciplina["nome"],
                                dificuldade=(topico.get("dificuldade") or {}).get("grau"),
                                importancia=topico.get("importancia"),
                                obrigatorio=topico.get("obrigatorio", True),
                                tempo=micro.get("tempo_estimado_h", 0.0),
                                status_curricular=micro.get("status", "nao_iniciado"),
                                pre_requisitos_nomes=declarados(micro["nome"]),
                            )
                        )

    return nos


# --------------------------------------------------------------------------- #
# Arestas: só o que foi declarado
# --------------------------------------------------------------------------- #


def _resolver_arestas(nos: list[dict]) -> list[dict]:
    """Liga cada nó aos pré-requisitos declarados, por nome.

    O que não resolve não vira aresta: entra em `nao_resolvidas` para o
    orquestrador reportar, em vez de virar uma dependência inventada.
    """
    por_nome: dict[str, list[dict]] = {}
    for no in nos:
        por_nome.setdefault(como_texto(no["nome"]), []).append(no)

    nao_resolvidas: list[dict] = []
    for no in nos:
        for nome_pre in no["pre_requisitos_nomes"]:
            candidatos = por_nome.get(como_texto(nome_pre), [])
            if not candidatos:
                nao_resolvidas.append(
                    {
                        "no": no["id"],
                        "nome": no["nome"],
                        "pre_requisito": nome_pre,
                        "motivo": "nome não encontrado na Árvore Curricular",
                    }
                )
                continue

            # Preferência: mesmo tipo e mesma disciplina — o pré-requisito de um
            # tópico é outro tópico, não o módulo de nome parecido.
            escolhido = min(
                candidatos,
                key=lambda c: (
                    c["tipo"] != no["tipo"],
                    c["disciplina"] != no["disciplina"],
                    c["ordem_curricular"],
                ),
            )
            if escolhido["id"] == no["id"]:
                nao_resolvidas.append(
                    {
                        "no": no["id"],
                        "nome": no["nome"],
                        "pre_requisito": nome_pre,
                        "motivo": "auto-dependência descartada",
                    }
                )
                continue
            if escolhido["id"] not in no["pre_requisitos"]:
                no["pre_requisitos"].append(escolhido["id"])

    return nao_resolvidas


def _eliminar_ciclos(nos: list[dict]) -> list[dict]:
    """Quebra cada ciclo removendo a aresta que volta no currículo.

    A dependência mantida é sempre a que respeita a ordem do edital; a que
    aponta para frente é a anomalia, e sai registrada.
    """
    por_id = {no["id"]: no for no in nos}
    removidas: list[dict] = []

    while True:
        ciclo = _encontrar_ciclo(por_id)
        if not ciclo:
            return removidas

        # Aresta a→b significa "a depende de b". Dentro do ciclo, remove-se a
        # que mais avança contra a ordem curricular.
        pior = max(
            (
                (origem, destino)
                for origem, destino in zip(ciclo, ciclo[1:] + ciclo[:1])
            ),
            key=lambda par: por_id[par[1]]["ordem_curricular"]
            - por_id[par[0]]["ordem_curricular"],
        )
        origem, destino = pior
        por_id[origem]["pre_requisitos"].remove(destino)
        removidas.append(
            {
                "de": origem,
                "para": destino,
                "nomes": f"{por_id[origem]['nome']} → {por_id[destino]['nome']}",
                "ciclo": [por_id[i]["nome"] for i in ciclo],
                "motivo": "dependência circular; mantida a ordem do currículo",
            }
        )


def _encontrar_ciclo(por_id: dict[str, dict]) -> list[str]:
    estado: dict[str, int] = {}
    pilha: list[str] = []

    def visitar(identificador: str) -> list[str]:
        estado[identificador] = 1
        pilha.append(identificador)
        for pre in por_id[identificador]["pre_requisitos"]:
            if pre not in por_id:
                continue
            if estado.get(pre) == 1:
                return pilha[pilha.index(pre) :]
            if estado.get(pre, 0) == 0:
                achado = visitar(pre)
                if achado:
                    return achado
        pilha.pop()
        estado[identificador] = 2
        return []

    for identificador in por_id:
        if estado.get(identificador, 0) == 0:
            achado = visitar(identificador)
            if achado:
                return achado
    return []


# --------------------------------------------------------------------------- #
# Métricas do grafo
# --------------------------------------------------------------------------- #


def _mesma_linhagem(um: str, outro: str) -> bool:
    """Um dos nós contém o outro? Os IDs são hierárquicos (`d1.m1.t1`)."""
    return um.startswith(f"{outro}.") or outro.startswith(f"{um}.")


def _ondas(nos: list[dict]) -> list[list[str]]:
    """Níveis do DAG: tudo na mesma onda pode ser estudado em paralelo."""
    pendentes = {no["id"]: set(no["pre_requisitos"]) for no in nos}
    concluidos: set[str] = set()
    ondas: list[list[str]] = []

    while pendentes:
        onda = [
            identificador
            for identificador, pres in pendentes.items()
            if pres <= concluidos
        ]
        if not onda:  # inalcançável: os ciclos já foram eliminados
            break
        ondas.append(sorted(onda, key=lambda i: i))
        concluidos.update(onda)
        for identificador in onda:
            del pendentes[identificador]

    return ondas


def _transitivos(nos: list[dict]) -> dict[str, set[str]]:
    """Dependentes transitivos de cada nó."""
    dependentes: dict[str, set[str]] = {no["id"]: set() for no in nos}
    diretos: dict[str, list[str]] = {no["id"]: [] for no in nos}
    for no in nos:
        for pre in no["pre_requisitos"]:
            if pre in diretos:
                diretos[pre].append(no["id"])

    def acumular(identificador: str, visitados: set[str]) -> set[str]:
        if dependentes[identificador]:
            return dependentes[identificador]
        total: set[str] = set()
        for filho in diretos[identificador]:
            if filho in visitados:
                continue
            total.add(filho)
            total |= acumular(filho, visitados | {filho})
        dependentes[identificador] = total
        return total

    for no in nos:
        acumular(no["id"], {no["id"]})
    return dependentes


def _caminhos(nos: list[dict], por_id: dict[str, dict]) -> list[dict]:
    """Cadeias maximais de pré-requisitos, ordenadas por tempo acumulado."""
    memo: dict[str, tuple[float, list[str]]] = {}

    def melhor(identificador: str) -> tuple[float, list[str]]:
        if identificador in memo:
            return memo[identificador]
        no = por_id[identificador]
        tempo = no["tempo_estimado_h"] if no["status_curricular"] != "dominado" else 0.0
        melhor_tempo, melhor_caminho = 0.0, []
        for pre in no["pre_requisitos"]:
            if pre not in por_id:
                continue
            t, caminho = melhor(pre)
            if t > melhor_tempo:
                melhor_tempo, melhor_caminho = t, caminho
        resultado = (tempo + melhor_tempo, melhor_caminho + [identificador])
        memo[identificador] = resultado
        return resultado

    # Só folhas do grafo de dependências encerram cadeia.
    tem_dependente = {pre for no in nos for pre in no["pre_requisitos"]}
    cadeias = [
        {
            "tempo_h": round(tempo, 2),
            "nos": caminho,
            "nomes": [por_id[i]["nome"] for i in caminho],
        }
        for no in nos
        if no["id"] not in tem_dependente
        for tempo, caminho in [melhor(no["id"])]
        if len(caminho) > 1
    ]
    cadeias.sort(key=lambda c: (-c["tempo_h"], -len(c["nos"])))
    return cadeias


# --------------------------------------------------------------------------- #
# Entrada principal
# --------------------------------------------------------------------------- #


def mapear(entradas: dict[str, Any]) -> dict[str, Any]:
    """Constrói o Grafo de Aprendizagem a partir da Árvore Curricular."""
    dados = entradas.get("dados_usuario", {}) or {}
    campos = {k: v for k, v in dados.items() if k != "perfil"}
    if isinstance(dados.get("perfil"), dict):
        campos = {**campos, **dados["perfil"]}

    anteriores = entradas.get("saidas_anteriores", {})
    arvore = anteriores.get("04", {}) or {}
    mapa_conhecimento = anteriores.get("03", {}) or {}

    pre_requisitos_globais = {
        como_texto(chave): como_lista(valor)
        for chave, valor in (campos.get("pre_requisitos") or {}).items()
    } if isinstance(campos.get("pre_requisitos"), dict) else {}

    nos = _achatar(arvore, pre_requisitos_globais)
    nao_resolvidas = _resolver_arestas(nos)
    ciclos_removidos = _eliminar_ciclos(nos)

    por_id = {no["id"]: no for no in nos}
    for no in nos:
        for pre in no["pre_requisitos"]:
            por_id[pre]["dependentes"].append(no["id"])

    ondas = _ondas(nos)
    onda_de = {
        identificador: indice
        for indice, onda in enumerate(ondas, start=1)
        for identificador in onda
    }
    transitivos = _transitivos(nos)

    for no in nos:
        concluido = no["status_curricular"] == "dominado"
        pendentes = [
            pre
            for pre in no["pre_requisitos"]
            if por_id[pre]["status_curricular"] != "dominado"
        ]
        bloqueio_ancestral = []
        pai = no["contido_em"]
        while pai:
            pai_no = por_id[pai]
            if any(
                por_id[pre]["status_curricular"] != "dominado"
                for pre in pai_no["pre_requisitos"]
            ):
                bloqueio_ancestral.append(pai)
            pai = pai_no["contido_em"]

        if concluido:
            status = STATUS_CONCLUIDO
        elif pendentes or bloqueio_ancestral:
            status = STATUS_BLOQUEADO
        else:
            status = STATUS_DISPONIVEL

        onda = onda_de.get(no["id"], 1)
        # Paralelismo real: mesmo nível do grafo, mesmo tipo e sem relação de
        # contenção — estudar um tópico "em paralelo com o módulo que o contém"
        # não é paralelismo, é o mesmo conteúdo contado duas vezes.
        companheiros = [
            outro
            for outro in ondas[onda - 1]
            if outro != no["id"]
            and por_id[outro]["tipo"] == no["tipo"]
            and not _mesma_linhagem(no["id"], outro)
            and por_id[outro]["status_curricular"] != "dominado"
        ]

        no.update(
            {
                "status": status,
                "bloqueado_por": pendentes,
                "bloqueado_por_ancestral": bloqueio_ancestral,
                "profundidade": onda - 1,
                "dependentes_transitivos": len(transitivos[no["id"]]),
                "pode_ser_estudado_em_paralelo": bool(companheiros)
                and status != STATUS_CONCLUIDO,
                "paralelo_com": companheiros,
                "ignoravel_no_planejamento": concluido,
            }
        )

    cadeias = _caminhos(nos, por_id)
    pendentes = [no for no in nos if no["status"] != STATUS_CONCLUIDO]

    bloqueadores = sorted(
        (
            {
                "id": no["id"],
                "nome": no["nome"],
                "tipo": no["tipo"],
                "dependentes_transitivos": no["dependentes_transitivos"],
                "status": no["status"],
                "tempo_estimado_h": no["tempo_estimado_h"],
            }
            for no in pendentes
            if no["dependentes_transitivos"] > 0
        ),
        key=lambda n: (-n["dependentes_transitivos"], n["id"]),
    )

    independentes = [
        no["id"]
        for no in pendentes
        if not no["pre_requisitos"] and not no["dependentes"]
    ]

    # Sequência lógica ideal: ordem topológica com desempate pela ordem do
    # currículo — o grafo manda no "quando pode", o edital manda no "qual antes".
    sequencia = [
        {
            "ordem": indice,
            "id": no["id"],
            "nome": no["nome"],
            "tipo": no["tipo"],
            "onda": onda_de.get(no["id"], 1),
            "tempo_estimado_h": no["tempo_estimado_h"],
        }
        for indice, no in enumerate(
            sorted(
                pendentes,
                key=lambda n: (onda_de.get(n["id"], 1), n["ordem_curricular"]),
            ),
            start=1,
        )
    ]

    observacoes: list[str] = []
    if not arvore.get("disciplinas"):
        observacoes.append(
            "Nenhuma Árvore Curricular recebida do agente 04: não há grafo a montar."
        )
    if nos and not any(no["pre_requisitos"] for no in nos):
        observacoes.append(
            "Nenhum pré-requisito declarado: todos os nós ficam disponíveis e "
            "paralelizáveis. Dependências não foram inferidas da ordem do edital."
        )
    if nao_resolvidas:
        observacoes.append(
            f"{len(nao_resolvidas)} pré-requisito(s) declarado(s) não encontrado(s) "
            "na Árvore Curricular — nenhuma aresta foi criada por aproximação."
        )
    if ciclos_removidos:
        observacoes.append(
            f"{len(ciclos_removidos)} dependência(s) circular(es) eliminada(s), "
            "mantendo a ordem do currículo."
        )

    lacunas: list[str] = []
    if not arvore:
        lacunas.append("arvore_curricular_do_agente_04")
    if not mapa_conhecimento:
        lacunas.append("mapa_de_conhecimento_do_agente_03")
    if not any(no["pre_requisitos_nomes"] for no in nos):
        lacunas.append("pre_requisitos")

    return {
        "objetivo": arvore.get("objetivo"),
        "nos": nos,
        "totais": {
            "nos": len(nos),
            "arestas": sum(len(no["pre_requisitos"]) for no in nos),
            "por_tipo": {
                tipo: sum(1 for no in nos if no["tipo"] == tipo) for tipo in TIPOS
            },
            "concluidos": sum(1 for no in nos if no["status"] == STATUS_CONCLUIDO),
            "disponiveis": sum(1 for no in nos if no["status"] == STATUS_DISPONIVEL),
            "bloqueados": sum(1 for no in nos if no["status"] == STATUS_BLOQUEADO),
        },
        "ondas_de_estudo": [
            {
                "onda": indice,
                "paralelo": len([i for i in onda if por_id[i]["status"] != STATUS_CONCLUIDO]) > 1,
                "nos": onda,
            }
            for indice, onda in enumerate(ondas, start=1)
        ],
        "caminho_principal": cadeias[0] if cadeias else None,
        "caminhos_alternativos": cadeias[1 : 1 + MAXIMO_CAMINHOS_ALTERNATIVOS],
        "nos_criticos": bloqueadores,
        "nos_independentes": independentes,
        "conteudos_opcionais": [
            no["id"] for no in nos if not no["obrigatorio"]
        ],
        "conteudos_ignoraveis": [
            no["id"] for no in nos if no["ignoravel_no_planejamento"]
        ],
        "sequencia_logica": sequencia,
        "ciclos_eliminados": ciclos_removidos,
        "dependencias_nao_resolvidas": nao_resolvidas,
        "profundidade_maxima": max((no["profundidade"] for no in nos), default=0),
        "acilico": True,
        "consumido_por": ["06", "07", "09", "10", "11", "14", "15", "16", "23", "24"],
        "observacoes": observacoes,
        "lacunas": lacunas,
        "confiabilidade": (
            "alta"
            if nos and any(no["pre_requisitos"] for no in nos) and not nao_resolvidas
            else "media"
            if nos
            else "baixa"
        ),
        "constantes_aplicadas": {
            "maximo_caminhos_alternativos": MAXIMO_CAMINHOS_ALTERNATIVOS,
            "origem_das_arestas": "somente pré-requisitos declarados",
        },
    }


__all__ = ["mapear"]
