"""Agente 19 — Coach.

Única responsabilidade: manter o estudante consistente. Não ensina, não cria
cronograma, não gera exercício, não altera o plano.

Este é o primeiro agente cuja saída é **texto endereçado ao estudante**, e é
por isso que as duas regras mais duras da spec precisam virar mecanismo:

* **"Nunca utilizar mensagens motivacionais genéricas."** Só é verificável se
  toda mensagem carregar um dado concreto — um número, uma data, um nome de
  tópico — vindo do registro medido. Uma frase que continuaria verdadeira com
  qualquer outro estudante no lugar é genérica por definição, e aqui ela é
  **recusada**, não suavizada: a mensagem não sai e a recusa fica declarada.
* **"Nunca manipular emocionalmente."** Culpa, medo e comparação social são
  proibidos por lista, e o texto composto passa pelo mesmo filtro antes de
  sair. Alerta é permitido; ameaça não.

A terceira decisão é sobre silêncio: quando não há dado de frequência, o
agente **não estima engajamento**. Ele diz o que falta. Um coach que inventa
consistência a partir de nada é pior que um coach calado.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from app.studyos.agentes.comum import (
    como_data,
    como_lista_de_dicts,
    como_texto,
    preenchido,
)
from app.studyos.agentes.frequencia import (
    consistencia as _consistencia_de,
    dias_estudados as _dias_estudados,
    dias_planejados as _dias_planejados,
    sequencia_ate as _sequencia_atual,
)

# --------------------------------------------------------------------------- #
# Constantes declaradas
# --------------------------------------------------------------------------- #

#: Janela padrão de análise do comportamento, em dias.
JANELA_DE_ANALISE_DIAS = 14

#: Faixas do índice de consistência (dias estudados / dias planejados).
FAIXAS_DE_ENGAJAMENTO: tuple[tuple[float, str], ...] = (
    (0.40, "critico"),
    (0.65, "baixo"),
    (0.85, "regular"),
)
ENGAJAMENTO_MAXIMO = "alto"
NIVEIS_DE_ENGAJAMENTO = ("critico", "baixo", "regular", ENGAJAMENTO_MAXIMO)

#: Dias sem estudar a partir dos quais há sinal de afastamento.
DIAS_DE_AUSENCIA_RELEVANTE = 3

#: Dias planejados mínimos para classificar engajamento. Chamar de "alto" quem
#: cumpriu o único dia planejado da janela é a mesma invenção que declarar
#: tendência a partir de duas medições.
MINIMO_DE_DIAS_PLANEJADOS = 3

#: Dias seguidos de estudo que caracterizam uma sequência digna de nota.
SEQUENCIA_MINIMA_PARA_RECONHECIMENTO = 3

#: Quanto a consistência precisa cair para virar alerta.
QUEDA_RELEVANTE_DE_CONSISTENCIA = 0.15

#: Dias em que uma mensagem já enviada não se repete.
JANELA_ANTIRREPETICAO_DIAS = 7

#: Termos que denunciam mensagem genérica: valeriam para qualquer estudante em
#: qualquer dia. Não são "palavras feias" — são frases sem informação.
TERMOS_GENERICOS: tuple[str, ...] = (
    "voce consegue",
    "acredite em si",
    "so depende de voce",
    "o sucesso e uma jornada",
    "nunca desista",
    "foco forca e fe",
    "bora estudar",
    "vamos la",
    "o esforco compensa",
    "confie no processo",
)

#: Termos de manipulação emocional: culpa, medo e comparação social.
TERMOS_MANIPULATIVOS: tuple[str, ...] = (
    "voce vai reprovar",
    "vai perder a vaga",
    "esta desperdicando",
    "todo mundo consegue",
    "os outros ja",
    "voce deveria ter",
    "que vergonha",
    "e sua culpa",
    "se voce falhar",
    "ninguem vai",
)

#: Tom da comunicação por nível de engajamento. Tom muda a forma, nunca o
#: conteúdo: o dado citado é o mesmo em qualquer tom.
TOM_POR_ENGAJAMENTO: dict[str, str] = {
    "critico": "direto e sem rodeios",
    "baixo": "objetivo e propositivo",
    "regular": "objetivo",
    ENGAJAMENTO_MAXIMO: "objetivo e de reforço",
}

#: Tipos de mensagem que o agente emite.
TIPOS_DE_MENSAGEM = ("incentivo", "alerta", "reconhecimento", "lembrete")

#: Conquista → mensagem que já conta esse mesmo fato. Serve para não dizer duas
#: vezes a mesma coisa com palavras diferentes.
COBERTURA_POR_CONQUISTA: dict[str, str] = {"constancia": "sequencia"}


class MensagemGenerica(Exception):
    """Mensagem sem nenhum dado concreto do estudante."""


class MensagemManipulativa(Exception):
    """Mensagem que usa culpa, medo ou comparação social."""


def _nivel_de_engajamento(consistencia: dict) -> str:
    if consistencia["indice"] is None:
        return "indeterminado"
    if consistencia["dias_planejados"] < MINIMO_DE_DIAS_PLANEJADOS:
        return "indeterminado"
    for limite, nome in FAIXAS_DE_ENGAJAMENTO:
        if consistencia["indice"] < limite:
            return nome
    return ENGAJAMENTO_MAXIMO


# --------------------------------------------------------------------------- #
# Frequência: o que foi observado
# --------------------------------------------------------------------------- #


def _evolucao(estudados: list[date], plano: dict, hoje: date) -> dict:
    """Consistência da janela atual contra a anterior, quando as duas existem."""
    fim_anterior = hoje - timedelta(days=JANELA_DE_ANALISE_DIAS)
    inicio_anterior = fim_anterior - timedelta(days=JANELA_DE_ANALISE_DIAS - 1)

    atual = _consistencia_de(
        estudados,
        _dias_planejados(plano, hoje - timedelta(days=JANELA_DE_ANALISE_DIAS - 1), hoje),
        JANELA_DE_ANALISE_DIAS,
    )
    anterior = _consistencia_de(
        estudados,
        _dias_planejados(plano, inicio_anterior, fim_anterior),
        JANELA_DE_ANALISE_DIAS,
    )

    if atual["indice"] is None or anterior["indice"] is None:
        return {
            "disponivel": False,
            "tendencia": "indeterminada",
            "base": "não há duas janelas planejadas para comparar",
        }

    variacao = atual["indice"] - anterior["indice"]
    return {
        "disponivel": True,
        "tendencia": (
            "melhora" if variacao >= QUEDA_RELEVANTE_DE_CONSISTENCIA
            else "queda" if variacao <= -QUEDA_RELEVANTE_DE_CONSISTENCIA
            else "estavel"
        ),
        "consistencia_anterior": anterior["indice"],
        "variacao": round(variacao, 4),
        "base": f"janela atual ({atual['indice']}) contra a anterior ({anterior['indice']})",
    }


# --------------------------------------------------------------------------- #
# Metas
# --------------------------------------------------------------------------- #


def _metas(campos: dict, plano: dict, estudados: list[date], hoje: date) -> dict:
    """Metas cumpridas e pendentes, comparando o registrado com o planejado."""
    declaradas = como_lista_de_dicts(campos.get("historico_metas"))
    cumpridas: list[dict] = []
    pendentes: list[dict] = []

    for meta in declaradas:
        registro = {
            "meta": meta.get("meta") or meta.get("descricao"),
            "prazo": (como_data(meta.get("prazo")) or hoje).isoformat(),
            "base": "meta informada pelo estudante",
        }
        if meta.get("cumprida"):
            cumpridas.append(registro)
        else:
            pendentes.append(registro)

    #: A meta diária do agente 06 é comparável sem o estudante declarar nada:
    #: ou o dia planejado teve estudo registrado, ou não teve.
    diaria = (plano.get("metas") or {}).get("diaria") or {}
    planejados = _dias_planejados(
        plano, hoje - timedelta(days=JANELA_DE_ANALISE_DIAS - 1), hoje
    )
    estudados_set = set(estudados)
    perdidos = [d for d in planejados if d not in estudados_set]
    if diaria.get("horas") and perdidos:
        pendentes.append(
            {
                "meta": f"{diaria['horas']}h de estudo nos dias planejados",
                "prazo": perdidos[-1].isoformat(),
                "base": (
                    f"{len(perdidos)} dia(s) planejado(s) sem estudo registrado na "
                    f"janela de {JANELA_DE_ANALISE_DIAS} dias"
                ),
            }
        )

    return {
        "cumpridas": cumpridas,
        "pendentes": pendentes,
        "total_declaradas": len(declaradas),
    }


# --------------------------------------------------------------------------- #
# Conquistas: só o que aconteceu
# --------------------------------------------------------------------------- #


def _conquistas(
    sequencia: dict,
    metas: dict,
    relatorio_de_erros: dict,
    mapa_de_fraquezas: dict,
) -> list[dict]:
    """Vitórias observadas no registro — nenhuma inventada para agradar."""
    conquistas: list[dict] = []

    if sequencia["dias"] >= SEQUENCIA_MINIMA_PARA_RECONHECIMENTO:
        conquistas.append(
            {
                "conquista": f"{sequencia['dias']} dias seguidos de estudo",
                "tipo": "constancia",
                "base": sequencia["base"],
            }
        )

    for meta in metas["cumpridas"]:
        conquistas.append(
            {
                "conquista": f"meta cumprida: {meta['meta']}",
                "tipo": "meta",
                "base": meta["base"],
            }
        )

    for resolvido in (relatorio_de_erros.get("indicadores") or {}).get(
        "erros_resolvidos", []
    ):
        conquistas.append(
            {
                "conquista": (
                    f"erro de {resolvido.get('tipo')} em {resolvido.get('topico')} "
                    "não reapareceu"
                ),
                "tipo": "erro_superado",
                "base": resolvido.get("base", "registro do agente 17"),
            }
        )

    for fraqueza in mapa_de_fraquezas.get("fraquezas", []):
        variacao = fraqueza.get("variacao") or {}
        if variacao.get("variacao") is not None and variacao["variacao"] < 0:
            conquistas.append(
                {
                    "conquista": (
                        f"{fraqueza['topico']} caiu de {variacao['indice_anterior']} "
                        f"para {fraqueza['indice_de_fraqueza']} no Índice de Fraqueza"
                    ),
                    "tipo": "fraqueza_reduzida",
                    "base": "comparação com o mapa de fraquezas anterior",
                }
            )

    return conquistas


# --------------------------------------------------------------------------- #
# Mensagens: nenhuma sai sem dado
# --------------------------------------------------------------------------- #


def _tem_dado_concreto(texto: str, dados: list[str]) -> bool:
    """A mensagem cita ao menos um dado medido deste estudante."""
    return any(preenchido(d) and str(d) in texto for d in dados)


def _validar_mensagem(texto: str, dados: list[str]) -> None:
    normalizado = como_texto(texto)
    for termo in TERMOS_MANIPULATIVOS:
        if termo in normalizado:
            raise MensagemManipulativa(
                f"mensagem usa termo manipulativo: '{termo}'"
            )
    for termo in TERMOS_GENERICOS:
        if termo in normalizado:
            raise MensagemGenerica(f"mensagem contém frase genérica: '{termo}'")
    if not _tem_dado_concreto(texto, dados):
        raise MensagemGenerica(
            "mensagem não cita nenhum dado medido do estudante"
        )


def _mensagem(
    tipo: str, chave: str, texto: str, dados: list[str], quando: str
) -> dict:
    """Compõe e valida. Mensagem reprovada não é suavizada: é recusada."""
    registro = {
        "tipo": tipo,
        "chave": chave,
        "texto": texto,
        "dados_citados": [d for d in dados if preenchido(d) and str(d) in texto],
        "melhor_momento": quando,
    }
    try:
        _validar_mensagem(texto, dados)
    except (MensagemGenerica, MensagemManipulativa) as recusa:
        return {**registro, "emitida": False, "motivo_da_recusa": str(recusa)}
    return {**registro, "emitida": True, "motivo_da_recusa": None}


def _melhor_momento(plano: dict, perfil: dict, hoje: date) -> dict:
    """Quando falar com o estudante — a partir da rotina dele, não de palpite."""
    proximos = [
        dia
        for dia in plano.get("cronograma", [])
        if (como_data(dia.get("data")) or hoje) >= hoje
    ]
    if proximos:
        return {
            "momento": f"no início do dia de estudo de {proximos[0]['data']}",
            "base": "próximo dia reservado no Plano de Estudos (agente 06)",
        }
    rotina = (perfil.get("tempo_disponivel") or {}).get("horas_por_dia_declaradas")
    if rotina:
        return {
            "momento": f"no bloco diário de {rotina:g}h declarado no perfil",
            "base": "rotina declarada pelo estudante (agente 01)",
        }
    return {
        "momento": None,
        "base": "nenhum dia de estudo conhecido; momento não definido",
    }


def _ja_enviada(chave: str, campos: dict, hoje: date) -> bool:
    """Mensagem repetida dentro da janela não é reforço, é ruído."""
    for enviada in como_lista_de_dicts(campos.get("mensagens_enviadas")):
        data = como_data(enviada.get("data"))
        if enviada.get("chave") == chave and data is not None:
            if (hoje - data).days < JANELA_ANTIRREPETICAO_DIAS:
                return True
    return False


def _compor_mensagens(
    contexto: dict, campos: dict, hoje: date
) -> tuple[list[dict], list[dict]]:
    """Uma mensagem por situação observada, cada uma amarrada a um dado."""
    quando = contexto["melhor_momento"]["momento"] or "no próximo contato"
    candidatas: list[dict] = []

    sequencia = contexto["sequencia"]
    consistencia = contexto["consistencia"]
    engajamento = contexto["engajamento"]
    foco = contexto["foco"]
    ausencia = contexto["dias_desde_o_ultimo_estudo"]

    if sequencia["dias"] >= SEQUENCIA_MINIMA_PARA_RECONHECIMENTO:
        candidatas.append(
            _mensagem(
                "reconhecimento",
                "sequencia",
                f"Você estudou {sequencia['dias']} dias seguidos. "
                f"Essa é a base que sustenta o resto do plano.",
                [str(sequencia["dias"])],
                quando,
            )
        )

    # Sem engajamento classificado não há mensagem sobre ritmo: "mantenha o
    # ritmo" apoiado num único dia planejado é palpite com cara de dado.
    if consistencia["indice"] is not None and engajamento in NIVEIS_DE_ENGAJAMENTO:
        if engajamento in ("critico", "baixo"):
            candidatas.append(
                _mensagem(
                    "alerta",
                    "consistencia_baixa",
                    f"Você cumpriu {consistencia['dias_estudados']} de "
                    f"{consistencia['dias_planejados']} dias planejados nas últimas "
                    f"{JANELA_DE_ANALISE_DIAS // 7} semanas. Vale rever se a meta "
                    f"diária cabe na sua rotina antes de tentar recuperar tudo de uma vez.",
                    [
                        str(consistencia["dias_estudados"]),
                        str(consistencia["dias_planejados"]),
                    ],
                    quando,
                )
            )
        else:
            candidatas.append(
                _mensagem(
                    "incentivo",
                    "consistencia_boa",
                    f"Você cumpriu {consistencia['dias_estudados']} de "
                    f"{consistencia['dias_planejados']} dias planejados. "
                    f"Manter esse ritmo é o que faz o cronograma fechar no prazo.",
                    [
                        str(consistencia["dias_estudados"]),
                        str(consistencia["dias_planejados"]),
                    ],
                    quando,
                )
            )

    if ausencia is not None and ausencia >= DIAS_DE_AUSENCIA_RELEVANTE:
        candidatas.append(
            _mensagem(
                "alerta",
                "ausencia",
                f"Faz {ausencia} dias sem registro de estudo. "
                f"Retomar com um bloco curto costuma custar menos que tentar "
                f"repor tudo de uma vez.",
                [str(ausencia)],
                quando,
            )
        )

    if foco:
        candidatas.append(
            _mensagem(
                "lembrete",
                "foco",
                f"O ponto de maior retorno agora é {foco['topico']}: "
                f"{foco['motivo']}.",
                [foco["topico"]],
                quando,
            )
        )

    # Conquista já coberta por outra mensagem não vira mensagem nova: dois
    # textos sobre o mesmo fato são repetição, ainda que com palavras
    # diferentes.
    ja_coberto = {c["chave"] for c in candidatas}
    for conquista in contexto["conquistas"]:
        if COBERTURA_POR_CONQUISTA.get(conquista["tipo"]) in ja_coberto:
            continue
        candidatas.append(
            _mensagem(
                "reconhecimento",
                f"conquista:{conquista['tipo']}",
                f"Registro do período: {conquista['conquista']}.",
                [conquista["conquista"]],
                quando,
            )
        )
        break

    emitidas: list[dict] = []
    recusadas: list[dict] = []
    vistas: set[str] = set()
    for mensagem in candidatas:
        if not mensagem["emitida"]:
            recusadas.append(mensagem)
            continue
        if mensagem["chave"] in vistas:
            continue
        if _ja_enviada(mensagem["chave"], campos, hoje):
            recusadas.append(
                {
                    **mensagem,
                    "emitida": False,
                    "motivo_da_recusa": (
                        f"mensagem já enviada nos últimos "
                        f"{JANELA_ANTIRREPETICAO_DIAS} dias"
                    ),
                }
            )
            continue
        vistas.add(mensagem["chave"])
        emitidas.append(mensagem)

    return emitidas, recusadas


# --------------------------------------------------------------------------- #
# Orientação
# --------------------------------------------------------------------------- #


def _foco(mapa_de_fraquezas: dict, relatorio_de_erros: dict) -> dict | None:
    """O ponto de maior retorno, tirado do ranking de urgência do agente 18."""
    urgentes = (mapa_de_fraquezas.get("ranking") or {}).get("mais_urgentes", [])
    if urgentes:
        alvo = urgentes[0]
        fatores = alvo.get("fatores") or []
        return {
            "topico": alvo["topico"],
            "disciplina": alvo.get("disciplina"),
            "motivo": (
                "; ".join(fatores)
                if fatores
                else "maior score de urgência no mapa de fraquezas"
            ),
            "origem": "agente 18",
        }

    recorrentes = (relatorio_de_erros.get("indicadores") or {}).get(
        "erros_recorrentes", []
    )
    if recorrentes:
        alvo = recorrentes[0]
        return {
            "topico": alvo["topico"],
            "disciplina": None,
            "motivo": (
                f"{alvo['frequencia']} erros do tipo {alvo['tipo']} no mesmo tópico"
            ),
            "origem": "agente 17",
        }
    return None


def _risco_de_abandono(relatorio: dict, consistencia: dict, ausencia: int | None) -> dict:
    """Risco do agente 12 somado ao que a frequência mostra.

    O nível do 12 não é recalculado: ele é reaproveitado e, quando a
    frequência agrava o quadro, o coach eleva o nível e diz por quê. Dois
    números discordando sobre a mesma coisa seria pior que um número só.
    """
    do_12 = relatorio.get("risco_de_abandono") or {}
    nivel = do_12.get("nivel", "indeterminado")
    fatores = list(do_12.get("fatores") or [])
    escala = ["baixo", "medio", "alto", "critico"]

    def elevar(atual: str) -> str:
        if atual not in escala:
            return "medio"
        return escala[min(len(escala) - 1, escala.index(atual) + 1)]

    if consistencia["indice"] is not None and consistencia["indice"] < 0.40:
        nivel = elevar(nivel)
        fatores.append(f"consistência de {consistencia['indice']:.0%} na janela")
    if ausencia is not None and ausencia >= DIAS_DE_AUSENCIA_RELEVANTE:
        nivel = elevar(nivel)
        fatores.append(f"{ausencia} dias sem registro de estudo")

    return {
        "nivel": nivel,
        "fatores": fatores,
        "base": (
            f"nível do agente 12 ({do_12.get('nivel', 'não informado')}) ajustado "
            "pela frequência observada"
            if fatores
            else do_12.get("base", "nenhum fator de risco medido")
        ),
    }


def _estrategia(engajamento: str, risco: dict, foco: dict | None) -> dict:
    """Estratégia é escolha de ação, não conselho de vida."""
    if engajamento in ("critico", "baixo") or risco["nivel"] in ("alto", "critico"):
        return {
            "estrategia": "reduzir a meta diária até voltar a cumpri-la todo dia",
            "base": (
                f"engajamento {engajamento} e risco de abandono {risco['nivel']}: "
                "meta não cumprida repetidamente vira desistência"
            ),
            "agente_responsavel": "20",
        }
    if foco:
        return {
            "estrategia": f"concentrar o bloco de reforço em {foco['topico']}",
            "base": foco["motivo"],
            "agente_responsavel": "23",
        }
    return {
        "estrategia": "manter o ritmo atual",
        "base": f"engajamento {engajamento} sem ponto de reforço pendente",
        "agente_responsavel": None,
    }


def _proxima_meta(plano: dict, metas: dict, hoje: date) -> dict | None:
    if metas["pendentes"]:
        return {**metas["pendentes"][0], "origem": "metas pendentes"}
    semanais = (plano.get("metas") or {}).get("semanal") or []
    if semanais:
        proxima = semanais[0]
        return {
            "meta": (
                f"{proxima.get('horas')}h em {proxima.get('dias')} dias na semana "
                f"{proxima.get('semana')}"
            ),
            "prazo": None,
            "base": "meta semanal do Plano de Estudos (agente 06)",
            "origem": "agente 06",
        }
    return None


# --------------------------------------------------------------------------- #
# Entrada principal
# --------------------------------------------------------------------------- #

CONSUMIDORES = ["20", "21", "22", "23", "24"]


def _observacoes(
    consistencia: dict,
    estudados: list[date],
    recusadas: list[dict],
    foco: dict | None,
    engajamento: str,
) -> list[str]:
    observacoes: list[str] = []

    if not estudados:
        observacoes.append(
            "Nenhum dia de estudo registrado: o engajamento não foi estimado. "
            "Sem frequência informada, qualquer índice aqui seria invenção."
        )
    if consistencia["indice"] is None and estudados:
        observacoes.append(f"Índice de consistência não calculado: {consistencia['base']}.")
    if engajamento == "indeterminado" and consistencia["indice"] is not None:
        observacoes.append(
            f"Engajamento não classificado: {consistencia['dias_planejados']} dia(s) "
            f"planejado(s) na janela, abaixo do mínimo de {MINIMO_DE_DIAS_PLANEJADOS} "
            "para a classificação significar alguma coisa."
        )
    genericas = [r for r in recusadas if "genérica" in (r["motivo_da_recusa"] or "")
                 or "não cita" in (r["motivo_da_recusa"] or "")]
    if genericas:
        observacoes.append(
            f"{len(genericas)} mensagem(ns) recusada(s) por não citar dado do "
            "estudante. Mensagem sem dado não é enviada nem reescrita para caber."
        )
    repetidas = [r for r in recusadas if "já enviada" in (r["motivo_da_recusa"] or "")]
    if repetidas:
        observacoes.append(
            f"{len(repetidas)} mensagem(ns) suprimida(s) por repetição dentro de "
            f"{JANELA_ANTIRREPETICAO_DIAS} dias."
        )
    if foco is None:
        observacoes.append(
            "Nenhum ponto de foco: não há fraqueza priorizada pelo agente 18 nem "
            "erro recorrente do agente 17."
        )
    return observacoes


def acompanhar(entradas: dict[str, Any], hoje: date | None = None) -> dict[str, Any]:
    """Constrói o Plano de Acompanhamento."""
    hoje = hoje or date.today()
    dados = entradas.get("dados_usuario", {}) or {}
    campos = {k: v for k, v in dados.items() if k != "perfil"}
    if isinstance(dados.get("perfil"), dict):
        campos = {**campos, **dados["perfil"]}

    anteriores = entradas.get("saidas_anteriores", {})
    perfil = anteriores.get("01", {}) or {}
    plano = anteriores.get("06", {}) or {}
    relatorio = anteriores.get("12", {}) or {}
    revisoes = anteriores.get("15", {}) or {}
    relatorio_de_erros = anteriores.get("17", {}) or {}
    mapa_de_fraquezas = anteriores.get("18", {}) or {}

    estudados = _dias_estudados(campos)
    janela_inicio = hoje - timedelta(days=JANELA_DE_ANALISE_DIAS - 1)
    planejados = _dias_planejados(plano, janela_inicio, hoje)
    consistencia = _consistencia_de(estudados, planejados, JANELA_DE_ANALISE_DIAS)
    sequencia = _sequencia_atual(estudados, hoje)
    ausencia = (hoje - estudados[-1]).days if estudados else None
    engajamento = _nivel_de_engajamento(consistencia)
    evolucao = _evolucao(estudados, plano, hoje)
    metas = _metas(campos, plano, estudados, hoje)
    conquistas = _conquistas(sequencia, metas, relatorio_de_erros, mapa_de_fraquezas)
    foco = _foco(mapa_de_fraquezas, relatorio_de_erros)
    risco = _risco_de_abandono(relatorio, consistencia, ausencia)
    momento = _melhor_momento(plano, perfil, hoje)

    emitidas, recusadas = _compor_mensagens(
        {
            "sequencia": sequencia,
            "consistencia": consistencia,
            "engajamento": engajamento,
            "foco": foco,
            "conquistas": conquistas,
            "dias_desde_o_ultimo_estudo": ausencia,
            "melhor_momento": momento,
        },
        campos,
        hoje,
    )

    return {
        "atualizado_em": hoje.isoformat(),
        "resumo_geral": {
            "nivel_de_engajamento": engajamento,
            "indice_de_consistencia": consistencia["indice"],
            "base_da_consistencia": consistencia["base"],
            "risco_de_abandono": risco,
            "evolucao_recente": evolucao,
            "janela_de_analise_dias": JANELA_DE_ANALISE_DIAS,
        },
        "orientacoes": {
            "principal_foco": foco,
            "recomendacao_prioritaria": (
                (mapa_de_fraquezas.get("fraquezas") or [{}])[0].get("recomendacao")
                if mapa_de_fraquezas.get("fraquezas")
                else None
            ),
            "proxima_meta": _proxima_meta(plano, metas, hoje),
            "estrategia_sugerida": _estrategia(engajamento, risco, foco),
            "tom_da_comunicacao": {
                "tom": TOM_POR_ENGAJAMENTO.get(engajamento, "objetivo"),
                "base": f"nível de engajamento {engajamento}",
                "nota": "o tom muda a forma; o dado citado é o mesmo em qualquer tom",
            },
        },
        "mensagens": emitidas,
        "mensagens_recusadas": recusadas,
        "melhor_momento_de_contato": momento,
        "indicadores": {
            "sequencia_de_dias_estudando": sequencia,
            "dias_desde_o_ultimo_estudo": ausencia,
            "metas_cumpridas": metas["cumpridas"],
            "metas_pendentes": metas["pendentes"],
            "conquistas": conquistas,
            "evolucao_da_disciplina": evolucao,
            "revisoes_agendadas": len(revisoes.get("sessoes", [])),
        },
        "consumido_por": CONSUMIDORES,
        "observacoes": _observacoes(
            consistencia, estudados, recusadas, foco, engajamento
        ),
        "lacunas": [] if estudados else ["historico_frequencia"],
        "confiabilidade": (
            "alta" if consistencia["indice"] is not None and evolucao["disponivel"]
            else "media" if consistencia["indice"] is not None
            else "baixa"
        ),
        "constantes_aplicadas": {
            "janela_de_analise_dias": JANELA_DE_ANALISE_DIAS,
            "minimo_de_dias_planejados": MINIMO_DE_DIAS_PLANEJADOS,
            "faixas_de_engajamento": {nome: limite for limite, nome in FAIXAS_DE_ENGAJAMENTO},
            "dias_de_ausencia_relevante": DIAS_DE_AUSENCIA_RELEVANTE,
            "sequencia_minima_para_reconhecimento": SEQUENCIA_MINIMA_PARA_RECONHECIMENTO,
            "queda_relevante_de_consistencia": QUEDA_RELEVANTE_DE_CONSISTENCIA,
            "janela_antirrepeticao_dias": JANELA_ANTIRREPETICAO_DIAS,
            "termos_genericos": TERMOS_GENERICOS,
            "termos_manipulativos": TERMOS_MANIPULATIVOS,
        },
    }


__all__ = [
    "COBERTURA_POR_CONQUISTA",
    "DIAS_DE_AUSENCIA_RELEVANTE",
    "FAIXAS_DE_ENGAJAMENTO",
    "JANELA_ANTIRREPETICAO_DIAS",
    "JANELA_DE_ANALISE_DIAS",
    "MINIMO_DE_DIAS_PLANEJADOS",
    "MensagemGenerica",
    "MensagemManipulativa",
    "NIVEIS_DE_ENGAJAMENTO",
    "SEQUENCIA_MINIMA_PARA_RECONHECIMENTO",
    "TERMOS_GENERICOS",
    "TERMOS_MANIPULATIVOS",
    "TIPOS_DE_MENSAGEM",
    "acompanhar",
]
