"""Agente 06 — Roadmap Builder.

Única responsabilidade: transformar o Grafo de Aprendizagem em um Plano de
Estudos com data, sessão e meta. Não ensina, não gera conteúdo, não responde
dúvidas — organiza *quando* cada conteúdo será estudado.

Três decisões estruturais:

* **Só folhas entram na agenda.** Os tempos da árvore se acumulam para cima
  (módulo = soma dos tópicos); agendar pai e filho contaria o mesmo estudo duas
  vezes. As unidades agendáveis são as folhas pendentes.
* **A dependência do agente 05 é intransponível.** Um nó só entra no dia D se
  todos os seus pré-requisitos — e os dos seus ancestrais — já estiverem
  concluídos ou integralmente alocados antes de D.
* **O que não couber não some.** Conteúdo sem espaço até a prova sai em
  ``conteudos_nao_alocados`` com o déficit em horas, nunca descartado em
  silêncio.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from app.studyos.agentes.comum import como_data, como_lista, como_numero, como_texto

# --------------------------------------------------------------------------- #
# Constantes declaradas
# --------------------------------------------------------------------------- #

#: Divisão do tempo diário. A soma é 1.0 e garante as regras "sempre incluir
#: revisão" e "sempre reservar tempo para exercícios".
PROPORCAO_CONTEUDO = 0.60
PROPORCAO_EXERCICIOS = 0.25
PROPORCAO_REVISAO = 0.15

#: Sessão menor que isso vira sobra do dia, não bloco de estudo.
MINIMO_SESSAO_H = 0.25

#: A cada N dias de estudo, o bloco de exercícios vira simulado.
SIMULADO_A_CADA_DIAS_DE_ESTUDO = 14

#: Horizonte máximo quando não há data de prova.
HORIZONTE_MAXIMO_DIAS = 365

#: Faixas de risco de atraso pela fração do conteúdo que coube no prazo.
LIMIAR_RISCO_ALTO = 0.85
LIMIAR_RISCO_MEDIO = 1.0

PESO_DIFICULDADE = {
    "muito_facil": 1,
    "facil": 2,
    "medio": 3,
    "dificil": 4,
    "muito_dificil": 5,
}

#: Acima deste peso, o conteúdo é considerado pesado para alternância.
DIFICULDADE_PESADA = 4

PESO_PRIORIDADE = {"alta": 0, "media": 1, "baixa": 2}

DIAS_SEMANA = ("segunda", "terca", "quarta", "quinta", "sexta", "sabado", "domingo")


def _dias_de_estudo(campos: dict, perfil: dict) -> list[int]:
    """Dias da semana em que há estudo, como índices 0=segunda."""
    declarados = como_lista(campos.get("dias_da_semana"))
    if declarados:
        indices = [
            DIAS_SEMANA.index(nome)
            for nome in (como_texto(d) for d in declarados)
            if nome in DIAS_SEMANA
        ]
        if indices:
            return sorted(set(indices))

    quantidade = int(
        (perfil.get("tempo_disponivel") or {}).get("dias_por_semana_declarados") or 0
    )
    quantidade = max(0, min(7, quantidade))
    # Sem dias nomeados, ocupam-se os primeiros da semana — regra declarada,
    # não preferência inventada para o estudante.
    return list(range(quantidade))


# --------------------------------------------------------------------------- #
# Unidades agendáveis
# --------------------------------------------------------------------------- #


def _unidades(grafo: dict) -> list[dict]:
    """Folhas pendentes do grafo, na ordem da sequência lógica do agente 05."""
    nos = grafo.get("nos", [])
    por_id = {no["id"]: no for no in nos}
    tem_filho = {no["contido_em"] for no in nos if no["contido_em"]}

    ordem_sequencia = {
        item["id"]: item["ordem"] for item in grafo.get("sequencia_logica", [])
    }

    folhas = [
        no
        for no in nos
        if no["id"] not in tem_filho and no["status"] != "concluido"
    ]
    folhas.sort(
        key=lambda no: (
            ordem_sequencia.get(no["id"], 10**6),
            no["ordem_curricular"],
        )
    )

    unidades: list[dict] = []
    for no in folhas:
        unidades.append(
            {
                "id": no["id"],
                "nome": no["nome"],
                "tipo": no["tipo"],
                "disciplina": no["disciplina"],
                "dificuldade": no["dificuldade"] or "medio",
                "importancia": no["importancia"],
                "tempo_total_h": float(no["tempo_estimado_h"] or 0.0),
                "restante_h": float(no["tempo_estimado_h"] or 0.0),
                "pre_requisitos": _pre_requisitos_efetivos(no, por_id),
                "partes": 0,
            }
        )
    return unidades


def _pre_requisitos_efetivos(no: dict, por_id: dict[str, dict]) -> list[str]:
    """Pré-requisitos do nó somados aos dos seus ancestrais."""
    efetivos = list(no["pre_requisitos"])
    pai = no["contido_em"]
    while pai and pai in por_id:
        efetivos.extend(por_id[pai]["pre_requisitos"])
        pai = por_id[pai]["contido_em"]
    return list(dict.fromkeys(efetivos))


def _satisfeito(
    pre_requisito: str, grafo_por_id: dict[str, dict], concluido: set[str]
) -> bool:
    """Um pré-requisito só está satisfeito quando todas as suas folhas estão."""
    alvo = grafo_por_id.get(pre_requisito)
    if alvo is None:
        return True
    if alvo["status"] == "concluido":
        return True

    descendentes = [
        no
        for no in grafo_por_id.values()
        if no["id"] == pre_requisito or no["id"].startswith(f"{pre_requisito}.")
    ]
    folhas = [
        no
        for no in descendentes
        if not any(
            outro["contido_em"] == no["id"] for outro in grafo_por_id.values()
        )
    ]
    return all(
        folha["status"] == "concluido" or folha["id"] in concluido for folha in folhas
    )


# --------------------------------------------------------------------------- #
# Montagem do cronograma
# --------------------------------------------------------------------------- #


def _escolher(
    disponiveis: list[dict], ultima_disciplina: str | None, ultimo_peso: int | None
) -> dict:
    """Alterna disciplina e dificuldade sem quebrar a ordem da sequência."""

    def chave(unidade: dict) -> tuple:
        peso = PESO_DIFICULDADE.get(unidade["dificuldade"], 3)
        mesma_disciplina = unidade["disciplina"] == ultima_disciplina
        # Depois de um bloco pesado, prefere-se um leve — e vice-versa.
        repete_carga = (
            ultimo_peso is not None
            and (peso >= DIFICULDADE_PESADA) == (ultimo_peso >= DIFICULDADE_PESADA)
        )
        # A alternância vem antes da prioridade de propósito: dentro do dia,
        # tudo que está elegível será estudado de qualquer forma, e deixar a
        # prioridade mandar sozinha empilharia a mesma disciplina em blocos
        # seguidos — exatamente a fadiga que a spec manda evitar. A prioridade
        # continua decidindo quem abre o dia e a ordem global.
        return (
            mesma_disciplina,
            repete_carga,
            PESO_PRIORIDADE.get(unidade.get("prioridade_disciplina"), 1),
            unidade["ordem"],
        )

    return min(disponiveis, key=chave)


def _sessao(
    tipo: str,
    disciplina: str | None,
    conteudo: str,
    objetivo: str,
    tempo: float,
    prioridade: str | None = None,
    dificuldade: str | None = None,
    no_id: str | None = None,
    parte: str | None = None,
    origem: str | None = None,
) -> dict:
    return {
        "tipo": tipo,
        "disciplina": disciplina,
        "conteudo": conteudo,
        "objetivo_da_sessao": objetivo,
        "tempo_estimado_h": round(tempo, 2),
        "prioridade": prioridade,
        "dificuldade": dificuldade,
        "no_id": no_id,
        "parte": parte,
        "origem": origem,
    }


def _montar_cronograma(
    unidades: list[dict],
    grafo_por_id: dict[str, dict],
    dias_estudo: list[int],
    capacidade_diaria: float,
    inicio: date,
    fim: date | None,
    faltas: set[date],
) -> tuple[list[dict], set[str]]:
    concluido: set[str] = set()
    estudados: list[str] = []
    cronograma: list[dict] = []

    limite = fim or (inicio + timedelta(days=HORIZONTE_MAXIMO_DIAS))
    dia = inicio
    dias_de_estudo_contados = 0

    while dia <= limite and any(u["restante_h"] > 0 for u in unidades):
        if dia.weekday() not in dias_estudo or dia in faltas:
            dia += timedelta(days=1)
            continue

        dias_de_estudo_contados += 1
        orcamento_conteudo = capacidade_diaria * PROPORCAO_CONTEUDO
        sessoes: list[dict] = []
        disciplinas_do_dia: list[str] = []
        ultima_disciplina: str | None = None
        ultimo_peso: int | None = None

        while orcamento_conteudo >= MINIMO_SESSAO_H:
            disponiveis = [
                u
                for u in unidades
                if u["restante_h"] > 0
                and all(
                    _satisfeito(pre, grafo_por_id, concluido)
                    for pre in u["pre_requisitos"]
                )
            ]
            if not disponiveis:
                break

            escolhida = _escolher(disponiveis, ultima_disciplina, ultimo_peso)
            tempo = min(escolhida["restante_h"], orcamento_conteudo)
            escolhida["restante_h"] = round(escolhida["restante_h"] - tempo, 2)
            escolhida["partes"] += 1

            parcial = escolhida["restante_h"] > 0
            sessoes.append(
                _sessao(
                    "conteudo",
                    escolhida["disciplina"],
                    escolhida["nome"],
                    f"Estudar {escolhida['nome']} ({escolhida['disciplina']})",
                    tempo,
                    prioridade=escolhida.get("prioridade_disciplina"),
                    dificuldade=escolhida["dificuldade"],
                    no_id=escolhida["id"],
                    parte=f"parte {escolhida['partes']}" if parcial or escolhida["partes"] > 1 else None,
                )
            )

            orcamento_conteudo = round(orcamento_conteudo - tempo, 2)
            ultima_disciplina = escolhida["disciplina"]
            ultimo_peso = PESO_DIFICULDADE.get(escolhida["dificuldade"], 3)
            if escolhida["disciplina"] not in disciplinas_do_dia:
                disciplinas_do_dia.append(escolhida["disciplina"])

            if not parcial:
                concluido.add(escolhida["id"])
                estudados.append(escolhida["id"])

        if not sessoes:
            dia += timedelta(days=1)
            dias_de_estudo_contados -= 1
            continue

        # Regra: sempre reservar exercícios e revisão.
        alvo_exercicios = ", ".join(disciplinas_do_dia) or "conteúdo do dia"
        e_simulado = dias_de_estudo_contados % SIMULADO_A_CADA_DIAS_DE_ESTUDO == 0
        sessoes.append(
            _sessao(
                "simulado" if e_simulado else "exercicios",
                None,
                alvo_exercicios,
                (
                    "Simulado cronometrado do conteúdo acumulado"
                    if e_simulado
                    else f"Resolver exercícios de {alvo_exercicios}"
                ),
                capacidade_diaria * PROPORCAO_EXERCICIOS,
                origem="16 Exam Simulator" if e_simulado else "09 Exercise Generator",
            )
        )

        anteriores = [i for i in estudados if i not in {s["no_id"] for s in sessoes}]
        alvo_revisao = (
            ", ".join(grafo_por_id[i]["nome"] for i in anteriores[-3:])
            if anteriores
            else "conteúdo do dia"
        )
        sessoes.append(
            _sessao(
                "revisao",
                None,
                alvo_revisao,
                f"Revisar {alvo_revisao}",
                capacidade_diaria * PROPORCAO_REVISAO,
                origem="reserva provisória até o agente 14 Memory Scheduler",
            )
        )

        cronograma.append(
            {
                "data": dia.isoformat(),
                "dia_semana": DIAS_SEMANA[dia.weekday()],
                "tempo_total_h": round(sum(s["tempo_estimado_h"] for s in sessoes), 2),
                "sessoes": sessoes,
            }
        )
        dia += timedelta(days=1)

    return cronograma, concluido


# --------------------------------------------------------------------------- #
# Metas e indicadores
# --------------------------------------------------------------------------- #


def _metas(cronograma: list[dict], capacidade_diaria: float) -> dict:
    semanais: dict[str, dict] = {}
    mensais: dict[str, dict] = {}

    for dia in cronograma:
        data = date.fromisoformat(dia["data"])
        conteudos = [s["conteudo"] for s in dia["sessoes"] if s["tipo"] == "conteudo"]

        ano, semana, _ = data.isocalendar()
        chave_semana = f"{ano}-S{semana:02d}"
        alvo = semanais.setdefault(
            chave_semana,
            {"semana": chave_semana, "horas": 0.0, "dias": 0, "conteudos": []},
        )
        alvo["horas"] = round(alvo["horas"] + dia["tempo_total_h"], 2)
        alvo["dias"] += 1
        alvo["conteudos"].extend(c for c in conteudos if c not in alvo["conteudos"])

        chave_mes = f"{data.year}-{data.month:02d}"
        alvo_mes = mensais.setdefault(
            chave_mes,
            {"mes": chave_mes, "horas": 0.0, "dias": 0, "disciplinas": []},
        )
        alvo_mes["horas"] = round(alvo_mes["horas"] + dia["tempo_total_h"], 2)
        alvo_mes["dias"] += 1
        for sessao in dia["sessoes"]:
            if sessao["tipo"] == "conteudo" and sessao["disciplina"] not in alvo_mes["disciplinas"]:
                alvo_mes["disciplinas"].append(sessao["disciplina"])

    return {
        "diaria": {
            "horas": round(capacidade_diaria, 2),
            "blocos": ["conteúdo", "exercícios", "revisão"],
            "regra": (
                f"{PROPORCAO_CONTEUDO:.0%} conteúdo, {PROPORCAO_EXERCICIOS:.0%} "
                f"exercícios, {PROPORCAO_REVISAO:.0%} revisão"
            ),
        },
        "semanal": list(semanais.values()),
        "mensal": list(mensais.values()),
    }


def _indicadores(
    unidades: list[dict],
    cronograma: list[dict],
    grafo: dict,
    inicio: date,
    fim: date | None,
) -> dict:
    horas_necessarias = round(sum(u["tempo_total_h"] for u in unidades), 2)
    horas_planejadas = round(
        sum(
            s["tempo_estimado_h"]
            for dia in cronograma
            for s in dia["sessoes"]
            if s["tipo"] == "conteudo"
        ),
        2,
    )
    horas_restantes = round(sum(u["restante_h"] for u in unidades), 2)

    total_nos = grafo.get("totais", {}).get("nos", 0)
    concluidos = grafo.get("totais", {}).get("concluidos", 0)

    fracao = horas_planejadas / horas_necessarias if horas_necessarias else 1.0
    if fracao >= LIMIAR_RISCO_MEDIO:
        risco = "baixo"
    elif fracao >= LIMIAR_RISCO_ALTO:
        risco = "medio"
    else:
        risco = "alto"

    return {
        "percentual_planejado": round(fracao, 4),
        "percentual_concluido": round(concluidos / total_nos, 4) if total_nos else 0.0,
        "horas_necessarias": horas_necessarias,
        "horas_planejadas": horas_planejadas,
        "horas_restantes": horas_restantes,
        "dias_restantes": (fim - inicio).days if fim else None,
        "dias_de_estudo_planejados": len(cronograma),
        "risco_de_atraso": risco,
    }


# --------------------------------------------------------------------------- #
# Entrada principal
# --------------------------------------------------------------------------- #


def construir(entradas: dict[str, Any], hoje: date | None = None) -> dict[str, Any]:
    """Constrói o Plano de Estudos Estruturado."""
    hoje = hoje or date.today()
    dados = entradas.get("dados_usuario", {}) or {}
    campos = {k: v for k, v in dados.items() if k != "perfil"}
    if isinstance(dados.get("perfil"), dict):
        campos = {**campos, **dados["perfil"]}

    anteriores = entradas.get("saidas_anteriores", {})
    perfil = anteriores.get("01", {}) or {}
    mapa_estrategico = anteriores.get("02", {}) or {}
    grafo = anteriores.get("05", {}) or {}

    grafo_por_id = {no["id"]: no for no in grafo.get("nos", [])}
    prioridades = {
        como_texto(p["disciplina"]): p["prioridade"]
        for p in mapa_estrategico.get("prioridade_disciplinas", [])
    }

    unidades = _unidades(grafo)
    for ordem, unidade in enumerate(unidades):
        unidade["ordem"] = ordem
        unidade["prioridade_disciplina"] = prioridades.get(
            como_texto(unidade["disciplina"]), "media"
        )

    # Progresso informado encerra unidades já vencidas fora do plano anterior.
    progresso = {como_texto(p) for p in como_lista(campos.get("progresso"))}
    if progresso:
        for unidade in unidades:
            if como_texto(unidade["nome"]) in progresso or unidade["id"] in progresso:
                unidade["restante_h"] = 0.0

    carga = perfil.get("carga_maxima_diaria") or {}
    capacidade_diaria = como_numero(carga.get("horas")) or 0.0
    dias_estudo = _dias_de_estudo(campos, perfil)

    inicio = como_data(campos.get("data_inicio")) or hoje
    fim = como_data(campos.get("data_prova")) or como_data(
        (mapa_estrategico.get("prazo_final") or {}).get("data")
    )
    faltas = {d for d in (como_data(f) for f in como_lista(campos.get("faltas"))) if d}

    cronograma: list[dict] = []
    if unidades and capacidade_diaria > 0 and dias_estudo:
        cronograma, _ = _montar_cronograma(
            unidades,
            grafo_por_id,
            dias_estudo,
            capacidade_diaria,
            inicio,
            fim,
            faltas,
        )

    nao_alocados = [
        {
            "id": u["id"],
            "nome": u["nome"],
            "disciplina": u["disciplina"],
            "horas_faltantes": u["restante_h"],
            "motivo": (
                "sem espaço no prazo"
                if fim
                else "sem capacidade diária ou dias de estudo definidos"
            ),
        }
        for u in unidades
        if u["restante_h"] > 0
    ]

    indicadores = _indicadores(unidades, cronograma, grafo, inicio, fim)
    metas = _metas(cronograma, capacidade_diaria)

    riscos: list[dict] = []
    if nao_alocados:
        riscos.append(
            {
                "risco": "conteudo_sem_espaco_no_prazo",
                "severidade": "alta",
                "evidencia": (
                    f"{len(nao_alocados)} unidade(s) e "
                    f"{indicadores['horas_restantes']}h fora do cronograma"
                ),
            }
        )
    if faltas:
        riscos.append(
            {
                "risco": "faltas_registradas",
                "severidade": "media",
                "evidencia": f"{len(faltas)} dia(s) de estudo perdido(s) e replanejado(s)",
            }
        )
    if capacidade_diaria and capacidade_diaria * PROPORCAO_CONTEUDO < MINIMO_SESSAO_H:
        riscos.append(
            {
                "risco": "capacidade_diaria_insuficiente",
                "severidade": "alta",
                "evidencia": "o bloco de conteúdo diário fica abaixo da sessão mínima",
            }
        )

    gatilhos = []
    if faltas:
        gatilhos.append("faltas informadas")
    if progresso:
        gatilhos.append("progresso informado")
    if campos.get("data_prova"):
        gatilhos.append("data da prova informada")
    if campos.get("dias_da_semana") or campos.get("horas_por_dia"):
        gatilhos.append("disponibilidade informada")

    observacoes: list[str] = []
    if not grafo.get("nos"):
        observacoes.append(
            "Nenhum Grafo de Aprendizagem recebido do agente 05: não há o que agendar."
        )
    if not capacidade_diaria:
        observacoes.append(
            "Carga máxima diária indisponível no Perfil Cognitivo: informe horas "
            "por dia para que o cronograma possa ser montado."
        )
    if not dias_estudo:
        observacoes.append(
            "Dias de estudo por semana não informados: nenhum dia foi ocupado."
        )
    if not fim:
        observacoes.append(
            "Sem data de prova: o plano vai até o fim do conteúdo, limitado a "
            f"{HORIZONTE_MAXIMO_DIAS} dias."
        )
    if nao_alocados:
        observacoes.append(
            "Conteúdo sem espaço no prazo foi listado em conteudos_nao_alocados, "
            "não descartado. O agente 23 pode reotimizar."
        )
    observacoes.append(
        "As sessões de revisão são reserva provisória: o agente 14 Memory "
        "Scheduler define os intervalos definitivos."
    )

    lacunas: list[str] = []
    if not grafo:
        lacunas.append("grafo_de_aprendizagem_do_agente_05")
    if not perfil:
        lacunas.append("perfil_cognitivo_do_agente_01")
    if not fim:
        lacunas.append("data_prova")

    return {
        "resumo_geral": {
            "data_inicio": inicio.isoformat(),
            "data_conclusao_prevista": (
                cronograma[-1]["data"] if cronograma else None
            ),
            "data_da_prova": fim.isoformat() if fim else None,
            "total_horas_planejadas": round(
                sum(d["tempo_total_h"] for d in cronograma), 2
            ),
            "total_horas_semanais": (
                perfil.get("tempo_disponivel") or {}
            ).get("horas_semanais_efetivas"),
            "total_horas_diarias": round(capacidade_diaria, 2),
            "dias_de_estudo_por_semana": [DIAS_SEMANA[d] for d in dias_estudo],
        },
        "cronograma": cronograma,
        "metas": metas,
        "indicadores": indicadores,
        "conteudos_nao_alocados": nao_alocados,
        "riscos": riscos,
        "replanejamento": {
            "automatico": True,
            "gatilhos_detectados": gatilhos,
            "como": (
                "o plano é recalculado por completo a cada execução, a partir de "
                "data_inicio, faltas, progresso, disponibilidade e data da prova"
            ),
        },
        "consumido_por": [
            "07", "09", "10", "11", "14", "15", "16", "19", "20", "21", "22", "23", "24"
        ],
        "observacoes": observacoes,
        "lacunas": lacunas,
        "confiabilidade": (
            "alta"
            if cronograma and not nao_alocados
            else "media"
            if cronograma
            else "baixa"
        ),
        "constantes_aplicadas": {
            "proporcao_conteudo": PROPORCAO_CONTEUDO,
            "proporcao_exercicios": PROPORCAO_EXERCICIOS,
            "proporcao_revisao": PROPORCAO_REVISAO,
            "minimo_sessao_h": MINIMO_SESSAO_H,
            "simulado_a_cada_dias_de_estudo": SIMULADO_A_CADA_DIAS_DE_ESTUDO,
            "horizonte_maximo_dias": HORIZONTE_MAXIMO_DIAS,
        },
    }


__all__ = ["construir"]
