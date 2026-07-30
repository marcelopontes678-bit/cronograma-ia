"""Agente 01 — Profile Analyzer.

Única responsabilidade: transformar as informações do usuário em um Perfil
Cognitivo Estruturado. Não cria cronograma, não ensina, não gera exercícios.

O agente é determinístico: tudo que ele devolve é derivado do que o usuário
informou. Campo não informado vira lacuna declarada — nunca um valor assumido.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from app.studyos.intents import normalizar

# --------------------------------------------------------------------------- #
# Constantes declaradas (heurísticas explícitas, não valores inventados)
# --------------------------------------------------------------------------- #

#: Fração das horas declaradas que sobra depois de deslocamento, imprevisto e
#: queda de atenção. Rotina de trabalho integral reduz o fator.
FATOR_EFETIVIDADE_PADRAO = 0.85
FATOR_EFETIVIDADE_ROTINA_INTENSA = 0.70

#: Teto de estudo focado por dia antes de a retenção cair.
TETO_COGNITIVO_DIARIO_H = 6.0

#: Ciclo de foco/pausa usado para converter carga em blocos.
BLOCO_FOCO_MIN = 50
BLOCO_PAUSA_MIN = 10

#: Abaixo disso, a disponibilidade total até a prova é tratada como risco.
LIMIAR_RISCO_HORAS_TOTAIS = 150.0
LIMIAR_ALTA_DISPONIBILIDADE_SEMANAL_H = 15.0
LIMIAR_DIAS_DESCONTINUIDADE = 3

CAMPOS_ENTRADA: tuple[str, ...] = (
    "nome",
    "idade",
    "escolaridade",
    "objetivo",
    "exame",
    "profissao",
    "rotina",
    "horas_por_dia",
    "dias_por_semana",
    "data_prova",
    "experiencia_anterior",
    "disciplinas_favoritas",
    "disciplinas_dificuldade",
    "preferencia_estudo",
    "idioma",
    "restricoes",
    "necessidades_especiais",
)

#: Campos que não bloqueiam o perfil quando ausentes.
CAMPOS_OPCIONAIS: tuple[str, ...] = (
    "nome",
    "exame",
    "data_prova",
    "restricoes",
    "necessidades_especiais",
    "idioma",
)

NIVEIS = ("iniciante", "intermediario", "avancado")

ESCOLARIDADE_NIVEL: tuple[tuple[tuple[str, ...], str], ...] = (
    (("doutorado", "mestrado", "pos-graduacao", "pos graduacao", "especializacao"), "avancado"),
    (("superior completo", "graduacao completa", "graduado", "bacharel", "licenciatura"), "intermediario"),
    (("superior incompleto", "cursando superior", "graduacao", "tecnico", "tecnologo"), "intermediario"),
    (("medio completo", "ensino medio", "medio", "fundamental"), "iniciante"),
)

EXPERIENCIA_POSITIVA = (
    "ja estudei", "ja fiz", "ja prestei", "aprovado", "passei", "anos de estudo",
    "cursinho", "ja tentei", "segunda vez", "experiencia",
)
EXPERIENCIA_NULA = ("nenhuma", "primeira vez", "nunca", "zero", "do zero", "iniciando")

ROTINA_INTENSA = (
    "integral", "40h", "44h", "tempo integral", "clt", "8 horas", "12x36",
    "dois empregos", "plantao", "trabalho o dia todo", "filhos pequenos",
)

ESTILOS: dict[str, tuple[str, ...]] = {
    "visual": ("video", "videos", "assistir", "mapa mental", "esquema", "diagrama", "imagem", "grafico", "slide"),
    "auditivo": ("audio", "podcast", "ouvir", "escutar", "aula narrada", "explicacao falada"),
    "leitura_escrita": ("ler", "leitura", "livro", "apostila", "pdf", "resumo", "escrever", "anotar", "texto"),
    "cinestesico": ("exercicio", "exercicios", "questoes", "praticar", "pratica", "resolver", "projeto", "mao na massa", "simulado"),
}


def _texto(valor: Any) -> str:
    if valor is None:
        return ""
    if isinstance(valor, (list, tuple, set)):
        return normalizar(" ".join(str(v) for v in valor))
    return normalizar(str(valor))


def _lista(valor: Any) -> list[str]:
    if valor in (None, "", [], {}):
        return []
    if isinstance(valor, (list, tuple, set)):
        return [str(v).strip() for v in valor if str(v).strip()]
    return [parte.strip() for parte in str(valor).split(",") if parte.strip()]


def _numero(valor: Any) -> float | None:
    if valor in (None, "", [], {}):
        return None
    try:
        return float(str(valor).replace(",", "."))
    except ValueError:
        return None


def _data(valor: Any) -> date | None:
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, date):
        return valor
    if not valor:
        return None
    for formato in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(str(valor).strip(), formato).date()
        except ValueError:
            continue
    return None


def _achatar(dados: dict[str, Any]) -> dict[str, Any]:
    """Aceita os campos soltos ou aninhados em ``perfil``."""
    plano = {k: v for k, v in dados.items() if k != "perfil"}
    aninhado = dados.get("perfil")
    if isinstance(aninhado, dict):
        plano = {**plano, **aninhado}
    return plano


# --------------------------------------------------------------------------- #
# Processamento (passos 1 a 8 da spec do agente)
# --------------------------------------------------------------------------- #


def _perfil_academico(campos: dict[str, Any]) -> dict[str, Any]:
    return {
        "nome": campos.get("nome"),
        "idade": _numero(campos.get("idade")),
        "escolaridade": campos.get("escolaridade"),
        "profissao": campos.get("profissao"),
        "objetivo": campos.get("objetivo"),
        "exame_alvo": campos.get("exame"),
        "idioma": campos.get("idioma") or "pt-BR",
    }


def _nivel_conhecimento(campos: dict[str, Any]) -> dict[str, Any]:
    escolaridade = _texto(campos.get("escolaridade"))
    base = None
    for termos, nivel in ESCOLARIDADE_NIVEL:
        if any(termo in escolaridade for termo in termos):
            base = nivel
            break

    if base is None:
        return {
            "estimativa": None,
            "base": "escolaridade não informada",
            "confianca": "nenhuma",
        }

    experiencia = _texto(campos.get("experiencia_anterior"))
    ajuste = "nenhum"
    indice = NIVEIS.index(base)
    if any(termo in experiencia for termo in EXPERIENCIA_POSITIVA):
        indice = min(indice + 1, len(NIVEIS) - 1)
        ajuste = "+1 por experiência anterior declarada"
    elif any(termo in experiencia for termo in EXPERIENCIA_NULA):
        indice = max(indice - 1, 0)
        ajuste = "-1 por ausência declarada de experiência"

    return {
        "estimativa": NIVEIS[indice],
        "base": f"escolaridade ('{campos.get('escolaridade')}') com ajuste: {ajuste}",
        "confianca": "media" if experiencia else "baixa",
        "observacao": (
            "Estimativa de partida. O agente 03 Knowledge Analyzer mede o nível real."
        ),
    }


def _tempo_disponivel(campos: dict[str, Any]) -> dict[str, Any]:
    horas_dia = _numero(campos.get("horas_por_dia"))
    dias_semana = _numero(campos.get("dias_por_semana"))
    rotina_intensa = any(
        termo in _texto(campos.get("rotina")) or termo in _texto(campos.get("profissao"))
        for termo in ROTINA_INTENSA
    )
    fator = (
        FATOR_EFETIVIDADE_ROTINA_INTENSA
        if rotina_intensa
        else FATOR_EFETIVIDADE_PADRAO
    )

    if horas_dia is None or dias_semana is None:
        return {
            "horas_por_dia_declaradas": horas_dia,
            "dias_por_semana_declarados": dias_semana,
            "horas_semanais_declaradas": None,
            "horas_semanais_efetivas": None,
            "fator_efetividade": fator,
            "rotina_intensa": rotina_intensa,
            "calculavel": False,
        }

    semanais = horas_dia * dias_semana
    return {
        "horas_por_dia_declaradas": horas_dia,
        "dias_por_semana_declarados": dias_semana,
        "horas_semanais_declaradas": round(semanais, 2),
        "horas_semanais_efetivas": round(semanais * fator, 2),
        "fator_efetividade": fator,
        "rotina_intensa": rotina_intensa,
        "calculavel": True,
    }


def _prazo(campos: dict[str, Any], tempo: dict[str, Any], hoje: date) -> dict[str, Any]:
    data_prova = _data(campos.get("data_prova"))
    if data_prova is None:
        return {"data_prova": None, "dias_restantes": None, "horas_totais_efetivas": None}

    dias = (data_prova - hoje).days
    horas_totais = None
    if tempo["calculavel"] and dias > 0:
        horas_totais = round(tempo["horas_semanais_efetivas"] * dias / 7, 2)
    return {
        "data_prova": data_prova.isoformat(),
        "dias_restantes": dias,
        "semanas_restantes": round(dias / 7, 1) if dias > 0 else 0,
        "horas_totais_efetivas": horas_totais,
    }


def _carga_maxima(tempo: dict[str, Any]) -> dict[str, Any]:
    horas_dia = tempo["horas_por_dia_declaradas"]
    if horas_dia is None:
        return {"horas": None, "blocos": None, "calculavel": False}

    carga = min(horas_dia * tempo["fator_efetividade"], TETO_COGNITIVO_DIARIO_H)
    minutos = carga * 60
    blocos = int(minutos // (BLOCO_FOCO_MIN + BLOCO_PAUSA_MIN))
    return {
        "horas": round(carga, 2),
        "blocos": max(blocos, 1 if minutos >= BLOCO_FOCO_MIN else 0),
        "bloco_foco_min": BLOCO_FOCO_MIN,
        "bloco_pausa_min": BLOCO_PAUSA_MIN,
        "limitado_pelo_teto": horas_dia * tempo["fator_efetividade"] > TETO_COGNITIVO_DIARIO_H,
        "teto_cognitivo_h": TETO_COGNITIVO_DIARIO_H,
        "calculavel": True,
    }


def _estilo_aprendizagem(campos: dict[str, Any]) -> dict[str, Any]:
    texto = " ".join(
        _texto(campos.get(campo))
        for campo in ("preferencia_estudo", "rotina", "experiencia_anterior")
    )
    pontuacao = {
        estilo: sum(1 for termo in termos if termo in texto)
        for estilo, termos in ESTILOS.items()
    }
    pontuacao = {estilo: n for estilo, n in pontuacao.items() if n}
    if not pontuacao:
        return {"predominante": None, "pontuacao": {}, "base": "preferência não informada"}

    predominante = max(pontuacao, key=lambda e: pontuacao[e])
    return {
        "predominante": predominante,
        "pontuacao": dict(sorted(pontuacao.items(), key=lambda kv: -kv[1])),
        "base": "termos declarados em preferência de estudo/rotina",
    }


def _riscos(
    campos: dict[str, Any],
    tempo: dict[str, Any],
    prazo: dict[str, Any],
    carga: dict[str, Any],
) -> list[dict[str, str]]:
    riscos: list[dict[str, str]] = []

    if prazo["horas_totais_efetivas"] is not None and (
        prazo["horas_totais_efetivas"] < LIMIAR_RISCO_HORAS_TOTAIS
    ):
        riscos.append(
            {
                "risco": "prazo_curto",
                "severidade": "alta",
                "evidencia": (
                    f"{prazo['horas_totais_efetivas']}h efetivas até a prova "
                    f"({prazo['dias_restantes']} dias)"
                ),
            }
        )

    if prazo["dias_restantes"] is not None and prazo["dias_restantes"] <= 0:
        riscos.append(
            {
                "risco": "data_de_prova_invalida",
                "severidade": "alta",
                "evidencia": "a data informada não está no futuro",
            }
        )

    if carga.get("limitado_pelo_teto"):
        riscos.append(
            {
                "risco": "sobrecarga",
                "severidade": "media",
                "evidencia": (
                    f"{tempo['horas_por_dia_declaradas']}h/dia declaradas acima do teto "
                    f"de {TETO_COGNITIVO_DIARIO_H}h de estudo focado"
                ),
            }
        )

    dias = tempo["dias_por_semana_declarados"]
    if dias is not None and dias < LIMIAR_DIAS_DESCONTINUIDADE:
        riscos.append(
            {
                "risco": "descontinuidade",
                "severidade": "media",
                "evidencia": f"{int(dias)} dia(s) de estudo por semana",
            }
        )

    if tempo["rotina_intensa"]:
        riscos.append(
            {
                "risco": "rotina_conflitante",
                "severidade": "media",
                "evidencia": "rotina/profissão declarada como de alta ocupação",
            }
        )

    dificuldades = _lista(campos.get("disciplinas_dificuldade"))
    favoritas = _lista(campos.get("disciplinas_favoritas"))
    if dificuldades and len(dificuldades) > len(favoritas):
        riscos.append(
            {
                "risco": "concentracao_de_lacunas",
                "severidade": "media",
                "evidencia": (
                    f"{len(dificuldades)} disciplina(s) com dificuldade contra "
                    f"{len(favoritas)} de domínio"
                ),
            }
        )

    if _lista(campos.get("necessidades_especiais")) or _lista(campos.get("restricoes")):
        riscos.append(
            {
                "risco": "adaptacao_necessaria",
                "severidade": "informativo",
                "evidencia": "restrições/necessidades especiais declaradas exigem adaptação de formato",
            }
        )

    return riscos


def _pontos(campos: dict[str, Any], tempo: dict[str, Any], estilo: dict) -> tuple[list[str], list[str]]:
    fortes: list[str] = []
    fracos: list[str] = []

    favoritas = _lista(campos.get("disciplinas_favoritas"))
    dificuldades = _lista(campos.get("disciplinas_dificuldade"))

    if favoritas:
        fortes.append("Domínio declarado em: " + ", ".join(favoritas))
    if dificuldades:
        fracos.append("Dificuldade declarada em: " + ", ".join(dificuldades))

    semanais = tempo["horas_semanais_efetivas"]
    if semanais is not None:
        if semanais >= LIMIAR_ALTA_DISPONIBILIDADE_SEMANAL_H:
            fortes.append(f"Disponibilidade alta: {semanais}h efetivas por semana")
        else:
            fracos.append(f"Disponibilidade baixa: {semanais}h efetivas por semana")

    dias = tempo["dias_por_semana_declarados"]
    if dias is not None and dias >= 5:
        fortes.append(f"Regularidade: {int(dias)} dias de estudo por semana")

    experiencia = _texto(campos.get("experiencia_anterior"))
    if any(termo in experiencia for termo in EXPERIENCIA_POSITIVA):
        fortes.append("Experiência anterior com o conteúdo/exame")
    elif any(termo in experiencia for termo in EXPERIENCIA_NULA):
        fracos.append("Sem experiência anterior declarada")

    if estilo["predominante"]:
        fortes.append(f"Estilo de aprendizagem definido: {estilo['predominante']}")

    return fortes, fracos


def analisar(entradas: dict[str, Any], hoje: date | None = None) -> dict[str, Any]:
    """Constrói o Perfil Cognitivo Estruturado a partir das entradas do usuário."""
    hoje = hoje or date.today()
    campos = _achatar(entradas.get("dados_usuario", {}) or {})

    informados = {
        campo for campo in CAMPOS_ENTRADA if campos.get(campo) not in (None, "", [], {})
    }
    lacunas = [
        campo
        for campo in CAMPOS_ENTRADA
        if campo not in informados and campo not in CAMPOS_OPCIONAIS
    ]

    tempo = _tempo_disponivel(campos)
    prazo = _prazo(campos, tempo, hoje)
    carga = _carga_maxima(tempo)
    estilo = _estilo_aprendizagem(campos)
    fortes, fracos = _pontos(campos, tempo, estilo)

    obrigatorios = [c for c in CAMPOS_ENTRADA if c not in CAMPOS_OPCIONAIS]
    completude = len(informados & set(obrigatorios)) / len(obrigatorios)

    return {
        "perfil_academico": _perfil_academico(campos),
        "nivel_conhecimento_geral": _nivel_conhecimento(campos),
        "tempo_disponivel": tempo,
        "prazo": prazo,
        "carga_maxima_diaria": carga,
        "estilo_aprendizagem": estilo,
        "riscos": _riscos(campos, tempo, prazo, carga),
        "pontos_fortes": fortes,
        "pontos_fracos": fracos,
        "restricoes": _lista(campos.get("restricoes")),
        "necessidades_especiais": _lista(campos.get("necessidades_especiais")),
        "campos_informados": sorted(informados),
        "lacunas": lacunas,
        "completude": round(completude, 2),
        "confiabilidade": (
            "alta" if completude >= 0.8 else "media" if completude >= 0.5 else "baixa"
        ),
        "constantes_aplicadas": {
            "fator_efetividade": tempo["fator_efetividade"],
            "teto_cognitivo_diario_h": TETO_COGNITIVO_DIARIO_H,
            "bloco_foco_min": BLOCO_FOCO_MIN,
            "limiar_risco_horas_totais": LIMIAR_RISCO_HORAS_TOTAIS,
        },
    }


__all__ = ["analisar", "CAMPOS_ENTRADA", "CAMPOS_OPCIONAIS"]
