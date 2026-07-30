"""Agente 02 — Goal Analyzer.

Única responsabilidade: converter o objetivo informado em um Mapa Estratégico de
Aprendizagem. Não ensina, não cria cronograma, não gera conteúdo.

Regra estruturante: **nenhuma disciplina é inventada**. Elas só saem do edital,
das matérias informadas ou do que o estudante declarou no perfil — e cada uma
carrega a `origem`. Sem edital, o agente diz que será preciso usar uma matriz
curricular equivalente, em vez de preencher a grade por conta própria.
"""

from __future__ import annotations

import re
from datetime import date
from typing import Any

from app.studyos.agentes.comum import (
    como_data,
    como_lista,
    como_numero,
    como_texto,
    filhos_estruturais,
    preenchido,
)

# --------------------------------------------------------------------------- #
# Constantes declaradas
# --------------------------------------------------------------------------- #

#: Horas de estudo estimadas por tópico de edital (primeira passada + fixação).
HORAS_POR_TOPICO = 2.5

#: Usado quando se conhece a disciplina mas não o detalhamento de tópicos.
HORAS_POR_DISCIPLINA_SEM_DETALHE = 30.0

#: Folga mínima entre horas disponíveis e carga estimada para o prazo ser viável.
MARGEM_VIABILIDADE = 1.0
MARGEM_APERTADO = 0.75

PRIORIDADE_NIVEL_MINIMO = {
    "alta": "avancado",
    "media": "intermediario",
    "baixa": "basico",
}

CAMPOS_ENTRADA: tuple[str, ...] = (
    "objetivo",
    "objetivos_secundarios",
    "exame",
    "categoria",
    "data_prova",
    "edital",
    "materias",
    "bibliografia",
    "materiais_obrigatorios",
    "nota_corte",
)

CAMPOS_OPCIONAIS: tuple[str, ...] = (
    "objetivos_secundarios",
    "categoria",
    "bibliografia",
    "materiais_obrigatorios",
    "nota_corte",
)

CATEGORIAS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("enem", ("enem", "exame nacional do ensino medio")),
    (
        "vestibular",
        ("vestibular", "fuvest", "unicamp", "unesp", "ita", "ime", "uerj", "ufrj", "sisu"),
    ),
    (
        "concurso_publico",
        (
            "concurso", "edital", "cargo publico", "servidor", "tribunal", "receita",
            "icms", "iss", "inss", "policia", "banca", "cespe", "cebraspe", "fgv",
            "vunesp", "trt", "trf", "tj", "camara", "senado", "prefeitura", "efetivo",
        ),
    ),
    (
        "certificacao",
        (
            "certificacao", "certificado", "aws", "azure", "gcp", "scrum", "pmp",
            "cisco", "comptia", "oracle", "itil", "cka", "certified",
        ),
    ),
    (
        "idiomas",
        (
            "ingles", "espanhol", "frances", "alemao", "italiano", "japones",
            "toefl", "ielts", "toeic", "dele", "celpe", "fluencia", "idioma",
            "conversacao",
        ),
    ),
    (
        "faculdade",
        (
            "faculdade", "universidade", "graduacao", "semestre", "prova final",
            "materia da faculdade", "disciplina da faculdade", "tcc", "mestrado",
        ),
    ),
    (
        "desenvolvimento_profissional",
        (
            "promocao", "carreira", "mudar de area", "transicao de carreira",
            "entrevista", "portfolio", "freelance", "trabalho", "profissional",
        ),
    ),
    (
        "aprendizado_livre",
        ("hobby", "curiosidade", "por conta propria", "aprender por diversao"),
    ),
)

#: Competências por categoria. Catálogo declarado — a saída marca a origem para
#: que nenhuma competência apareça como se tivesse vindo do usuário.
COMPETENCIAS_POR_CATEGORIA: dict[str, tuple[str, ...]] = {
    "concurso_publico": (
        "interpretação de texto",
        "resolução de questões objetivas sob pressão de tempo",
        "memorização e recuperação de legislação",
        "resolução de questões da banca organizadora",
    ),
    "enem": (
        "interpretação de texto e de dados",
        "redação dissertativo-argumentativa",
        "resolução de questões contextualizadas",
        "gestão de tempo em prova longa",
    ),
    "vestibular": (
        "resolução de questões objetivas",
        "produção de redação",
        "raciocínio quantitativo",
    ),
    "faculdade": (
        "estudo por bibliografia obrigatória",
        "resolução de listas de exercícios",
        "produção acadêmica escrita",
    ),
    "idiomas": (
        "compreensão oral",
        "compreensão escrita",
        "produção oral",
        "produção escrita",
        "vocabulário ativo",
        "gramática aplicada",
    ),
    "certificacao": (
        "domínio prático da ferramenta",
        "resolução de cenários aplicados",
        "simulados cronometrados no formato oficial",
    ),
    "desenvolvimento_profissional": (
        "aplicação prática no trabalho",
        "construção de portfólio demonstrável",
    ),
    "aprendizado_livre": (
        "autonomia de estudo",
        "prática deliberada",
    ),
}

SEPARADORES_SECUNDARIOS = (
    ";", " e tambem ", " alem de ", " e depois ", " e em seguida ", " e ainda ",
)


# --------------------------------------------------------------------------- #
# Extração de disciplinas — só do que existe
# --------------------------------------------------------------------------- #


def _disciplina(nome: str, topicos: Any, peso: Any, questoes: Any, origem: str) -> dict:
    return {
        "nome": nome.strip(),
        # `filhos_estruturais` no lugar de `como_lista` porque o tópico pode
        # chegar como dicionário ({"nome": ..., "pre_requisitos": [...]}), e
        # nesse caso a coerção genérica devolveria o dicionário inteiro como
        # se fosse o nome do tópico.
        "topicos": [nome_topico for nome_topico, _ in filhos_estruturais(topicos)],
        "peso": como_numero(peso),
        "questoes": como_numero(questoes),
        "origem": origem,
    }


def _topicos_da_disciplina(conteudo: dict) -> Any:
    """Tópicos de uma disciplina, achatando a modularização quando existir.

    O agente 04 preserva os módulos; aqui eles só interessam como lista plana
    de tópicos, que é o que o Mapa Estratégico consome.
    """
    direto = conteudo.get("topicos") or conteudo.get("conteudos")
    if preenchido(direto):
        return direto
    if preenchido(conteudo.get("modulos")):
        return [
            nome_topico
            for _, filhos in filhos_estruturais(conteudo["modulos"])
            for nome_topico, _ in filhos_estruturais(filhos)
        ]
    return None


def _extrair(fonte: Any, origem: str) -> list[dict]:
    """Aceita dict, lista de dicts, lista de nomes ou texto."""
    if not preenchido(fonte):
        return []

    if isinstance(fonte, dict):
        interno = fonte.get("disciplinas")
        if interno is not None:
            return _extrair(interno, origem)
        return [
            _disciplina(str(nome), conteudo, None, None, origem)
            if not isinstance(conteudo, dict)
            else _disciplina(
                str(nome),
                _topicos_da_disciplina(conteudo),
                conteudo.get("peso"),
                conteudo.get("questoes"),
                origem,
            )
            for nome, conteudo in fonte.items()
        ]

    if isinstance(fonte, (list, tuple)):
        disciplinas: list[dict] = []
        for item in fonte:
            if isinstance(item, dict):
                nome = item.get("nome") or item.get("disciplina") or item.get("materia")
                if not nome:
                    continue
                disciplinas.append(
                    _disciplina(
                        str(nome),
                        item.get("topicos") or item.get("conteudos"),
                        item.get("peso"),
                        item.get("questoes"),
                        origem,
                    )
                )
            elif str(item).strip():
                disciplinas.append(_disciplina(str(item), None, None, None, origem))
        return disciplinas

    return [
        _disciplina(nome, None, None, None, origem)
        for nome in re.split(r"[,;\n]", str(fonte))
        if nome.strip()
    ]


def _disciplinas(campos: dict[str, Any], perfil: dict) -> tuple[list[dict], str]:
    """Devolve as disciplinas e o grau de cobertura da fonte usada."""
    do_edital = _extrair(campos.get("edital"), "edital")
    if do_edital:
        return do_edital, "edital"

    das_materias = _extrair(campos.get("materias"), "materias_informadas")
    if das_materias:
        return das_materias, "materias_informadas"

    declaradas = [
        *como_lista(campos.get("disciplinas_favoritas")),
        *como_lista(campos.get("disciplinas_dificuldade")),
    ]
    if declaradas:
        vistas: dict[str, dict] = {}
        for nome in declaradas:
            vistas.setdefault(
                como_texto(nome),
                _disciplina(nome, None, None, None, "declaradas_no_perfil"),
            )
        return list(vistas.values()), "parcial_declarada_no_perfil"

    return [], "indefinida"


# --------------------------------------------------------------------------- #
# Processamento (passos 1 a 11 da spec)
# --------------------------------------------------------------------------- #


def _categoria(campos: dict[str, Any]) -> dict[str, Any]:
    informada = como_texto(campos.get("categoria"))
    if informada:
        for nome, _ in CATEGORIAS:
            if nome in informada.replace(" ", "_"):
                return {"categoria": nome, "base": "informada pelo usuário"}

    # O objetivo declarado é a fonte primária; a solicitação só entra se o
    # objetivo não permitir classificar — assim um pedido genérico não
    # sobrepõe o que o usuário disse explicitamente querer.
    fontes = (
        ("objetivo/exame", ("objetivo", "exame", "bibliografia")),
        ("texto da solicitação", ("solicitacao",)),
    )

    for base, campos_da_fonte in fontes:
        texto = " ".join(como_texto(campos.get(campo)) for campo in campos_da_fonte)
        encontrados = {
            nome: [termo for termo in termos if termo in texto]
            for nome, termos in CATEGORIAS
        }
        encontrados = {nome: t for nome, t in encontrados.items() if t}
        if not encontrados:
            continue

        ordem = [nome for nome, _ in CATEGORIAS]
        categoria = min(encontrados, key=lambda n: (-len(encontrados[n]), ordem.index(n)))
        return {
            "categoria": categoria,
            "base": f"termos encontrados em {base}",
            "termos": encontrados[categoria],
        }

    return {
        "categoria": None,
        "base": "objetivo não permite classificar a categoria",
        "termos": [],
    }


def _objetivos(campos: dict[str, Any]) -> tuple[str | None, list[str]]:
    principal = campos.get("objetivo")
    principal = str(principal).strip() if preenchido(principal) else None

    secundarios = como_lista(campos.get("objetivos_secundarios"))
    if not secundarios and principal:
        texto = principal
        for separador in SEPARADORES_SECUNDARIOS:
            padrao = re.escape(separador.strip())
            partes = re.split(rf"\s*{padrao}\s*", texto, flags=re.IGNORECASE)
            if len(partes) > 1:
                texto = partes[0].strip()
                secundarios = [p.strip() for p in partes[1:] if p.strip()]
                break
        principal = texto
    return principal, secundarios


def _prioridades(disciplinas: list[dict], campos: dict[str, Any]) -> list[dict]:
    """Prioriza por peso no edital, dificuldade declarada e volume de conteúdo."""
    if not disciplinas:
        return []

    dificuldades = {como_texto(d) for d in como_lista(campos.get("disciplinas_dificuldade"))}
    favoritas = {como_texto(d) for d in como_lista(campos.get("disciplinas_favoritas"))}

    pesos = [d["peso"] or d["questoes"] or 0 for d in disciplinas]
    maior_peso = max(pesos) or 0
    maior_volume = max(len(d["topicos"]) for d in disciplinas) or 0

    prioridades: list[dict] = []
    for disciplina in disciplinas:
        nome_normalizado = como_texto(disciplina["nome"])
        fatores: list[str] = []
        score = 0.0

        peso = disciplina["peso"] or disciplina["questoes"]
        if peso and maior_peso:
            score += 3 * (peso / maior_peso)
            fatores.append(f"peso no edital ({peso})")

        if nome_normalizado in dificuldades:
            score += 2
            fatores.append("dificuldade declarada pelo estudante")
        if nome_normalizado in favoritas:
            score -= 1
            fatores.append("domínio declarado pelo estudante")

        volume = len(disciplina["topicos"])
        if volume and maior_volume:
            score += 2 * (volume / maior_volume)
            fatores.append(f"{volume} tópico(s)")

        if not fatores:
            fatores.append("sem peso, dificuldade ou volume informados")

        nivel = "alta" if score >= 4 else "media" if score >= 2 else "baixa"
        prioridades.append(
            {
                "disciplina": disciplina["nome"],
                "prioridade": nivel,
                "score": round(score, 2),
                "fatores": fatores,
                "nivel_minimo_esperado": PRIORIDADE_NIVEL_MINIMO[nivel],
            }
        )

    ordem = {"alta": 0, "media": 1, "baixa": 2}
    prioridades.sort(key=lambda p: (ordem[p["prioridade"]], -p["score"]))
    return prioridades


def _carga(disciplinas: list[dict], cobertura: str) -> dict[str, Any]:
    if not disciplinas:
        return {
            "horas_estimadas": None,
            "base": "nenhuma disciplina identificada",
            "precisao": "indisponivel",
            "calculavel": False,
        }

    total_topicos = sum(len(d["topicos"]) for d in disciplinas)
    if total_topicos:
        return {
            "horas_estimadas": round(total_topicos * HORAS_POR_TOPICO, 1),
            "total_topicos": total_topicos,
            "total_disciplinas": len(disciplinas),
            "base": f"{total_topicos} tópicos × {HORAS_POR_TOPICO}h",
            "precisao": "alta" if cobertura == "edital" else "media",
            "calculavel": True,
        }

    return {
        "horas_estimadas": round(
            len(disciplinas) * HORAS_POR_DISCIPLINA_SEM_DETALHE, 1
        ),
        "total_topicos": 0,
        "total_disciplinas": len(disciplinas),
        "base": (
            f"{len(disciplinas)} disciplinas × {HORAS_POR_DISCIPLINA_SEM_DETALHE}h "
            "(sem detalhamento de tópicos)"
        ),
        "precisao": "baixa",
        "calculavel": True,
    }


def _tempo_do_perfil(perfil: dict) -> dict[str, Any]:
    tempo = perfil.get("tempo_disponivel") or {}
    prazo = perfil.get("prazo") or {}
    return {
        "horas_semanais_efetivas": tempo.get("horas_semanais_efetivas"),
        "horas_totais_ate_a_prova": prazo.get("horas_totais_efetivas"),
        "dias_restantes": prazo.get("dias_restantes"),
        "semanas_restantes": prazo.get("semanas_restantes"),
        "origem": "agente 01 Profile Analyzer" if perfil else "perfil indisponível",
    }


def _restricoes_de_prazo(carga: dict, tempo: dict, prazo_final: dict) -> dict[str, Any]:
    horas_necessarias = carga.get("horas_estimadas")
    horas_disponiveis = tempo.get("horas_totais_ate_a_prova")

    if horas_necessarias is None or horas_disponiveis is None:
        return {
            "viabilidade": "indeterminada",
            "motivo": (
                "faltam carga estimada e/ou tempo disponível até a data da prova"
            ),
            "deficit_horas": None,
        }

    saldo = horas_disponiveis - horas_necessarias
    if horas_disponiveis >= horas_necessarias * MARGEM_VIABILIDADE:
        viabilidade = "viavel"
    elif horas_disponiveis >= horas_necessarias * MARGEM_APERTADO:
        viabilidade = "apertado"
    else:
        viabilidade = "inviavel_no_ritmo_atual"

    semanas = tempo.get("semanas_restantes") or 0
    necessarias_semana = (
        round(horas_necessarias / semanas, 1) if semanas else None
    )

    return {
        "viabilidade": viabilidade,
        "horas_necessarias": horas_necessarias,
        "horas_disponiveis": horas_disponiveis,
        "deficit_horas": round(max(0.0, -saldo), 1),
        "saldo_horas": round(saldo, 1),
        "horas_semanais_necessarias": necessarias_semana,
        "horas_semanais_disponiveis": tempo.get("horas_semanais_efetivas"),
        "prazo_final": prazo_final.get("data"),
    }


def _requisitos(campos: dict[str, Any], cobertura: str) -> list[dict[str, str]]:
    requisitos: list[dict[str, str]] = []

    if cobertura == "edital":
        requisitos.append(
            {
                "requisito": "edital",
                "status": "disponivel",
                "acao": "usar o edital como referência principal da grade",
            }
        )
    else:
        requisitos.append(
            {
                "requisito": "edital",
                "status": "ausente",
                "acao": (
                    "sem edital, o agente 04 deverá usar uma matriz curricular "
                    "equivalente como referência"
                ),
            }
        )

    bibliografia = como_lista(campos.get("bibliografia"))
    requisitos.append(
        {
            "requisito": "bibliografia",
            "status": "disponivel" if bibliografia else "ausente",
            "acao": (
                "usar a bibliografia informada: " + ", ".join(bibliografia)
                if bibliografia
                else "confirmar bibliografia obrigatória com o estudante"
            ),
        }
    )

    materiais = como_lista(campos.get("materiais_obrigatorios"))
    if materiais:
        requisitos.append(
            {
                "requisito": "materiais_obrigatorios",
                "status": "disponivel",
                "acao": "garantir acesso a: " + ", ".join(materiais),
            }
        )

    return requisitos


def _criterios_sucesso(
    prioridades: list[dict], cobertura: str, prazo_final: dict, campos: dict[str, Any]
) -> list[str]:
    criterios: list[str] = []

    nota_corte = como_numero(campos.get("nota_corte"))
    if nota_corte is not None:
        criterios.append(f"Atingir pontuação igual ou superior a {nota_corte:g}")

    altas = [p["disciplina"] for p in prioridades if p["prioridade"] == "alta"]
    if altas:
        criterios.append(
            "Atingir nível avançado nas disciplinas de prioridade alta: "
            + ", ".join(altas)
        )
    if prioridades:
        criterios.append(
            "Atingir o nível mínimo esperado em 100% das disciplinas mapeadas"
        )

    if cobertura == "edital":
        criterios.append("Cobrir 100% dos tópicos do edital")
    elif cobertura in ("materias_informadas", "parcial_declarada_no_perfil"):
        criterios.append("Cobrir 100% das matérias informadas")

    if prazo_final.get("data"):
        criterios.append(f"Concluir a cobertura até {prazo_final['data']}")

    return criterios


def analisar(entradas: dict[str, Any], hoje: date | None = None) -> dict[str, Any]:
    """Constrói o Mapa Estratégico de Aprendizagem."""
    hoje = hoje or date.today()
    dados = entradas.get("dados_usuario", {}) or {}
    campos = {k: v for k, v in dados.items() if k != "perfil"}
    if isinstance(dados.get("perfil"), dict):
        campos = {**campos, **dados["perfil"]}
    campos.setdefault("solicitacao", entradas.get("solicitacao", ""))

    perfil = entradas.get("saidas_anteriores", {}).get("01", {}) or {}

    principal, secundarios = _objetivos(campos)
    categoria = _categoria(campos)
    disciplinas, cobertura = _disciplinas(campos, perfil)
    prioridades = _prioridades(disciplinas, campos)
    carga = _carga(disciplinas, cobertura)
    tempo = _tempo_do_perfil(perfil)

    data_prova = como_data(campos.get("data_prova"))
    prazo_final = {
        "data": data_prova.isoformat() if data_prova else None,
        "dias_restantes": (data_prova - hoje).days if data_prova else None,
        "definido": data_prova is not None,
    }

    restricoes = _restricoes_de_prazo(carga, tempo, prazo_final)

    competencias = [
        {"competencia": c, "origem": "catalogo_por_categoria"}
        for c in COMPETENCIAS_POR_CATEGORIA.get(categoria["categoria"] or "", ())
    ]

    lacunas = [
        campo
        for campo in CAMPOS_ENTRADA
        if campo not in CAMPOS_OPCIONAIS and not preenchido(campos.get(campo))
    ]
    if not perfil:
        lacunas.append("perfil_cognitivo_do_agente_01")

    obrigatorios = [c for c in CAMPOS_ENTRADA if c not in CAMPOS_OPCIONAIS]
    completude = 1 - len([l for l in lacunas if l in obrigatorios]) / len(obrigatorios)

    observacoes: list[str] = []
    if cobertura != "edital":
        observacoes.append(
            "Sem edital disponível: a grade deverá ser montada a partir de uma "
            "matriz curricular equivalente pelo agente 04 Curriculum Builder."
        )
    if cobertura == "indefinida":
        observacoes.append(
            "Nenhuma disciplina foi informada — nenhuma foi inferida. Informe o "
            "edital ou a lista de matérias para que a grade possa ser mapeada."
        )
    if categoria["categoria"] is None:
        observacoes.append(
            "Categoria do objetivo indeterminada: competências necessárias não "
            "foram derivadas."
        )

    return {
        "objetivo_principal": principal,
        "objetivos_secundarios": secundarios,
        "categoria_objetivo": categoria,
        "disciplinas": disciplinas,
        "cobertura_das_disciplinas": cobertura,
        "competencias_necessarias": competencias,
        "prioridade_disciplinas": prioridades,
        "estimativa_carga_estudo": carga,
        "tempo_disponivel": tempo,
        "prazo_final": prazo_final,
        "restricoes_de_prazo": restricoes,
        "requisitos_obrigatorios": _requisitos(campos, cobertura),
        "criterios_sucesso": _criterios_sucesso(
            prioridades, cobertura, prazo_final, campos
        ),
        "consumido_por": ["04", "05", "06", "16", "21", "22"],
        "observacoes": observacoes,
        "lacunas": lacunas,
        "completude": round(completude, 2),
        "confiabilidade": (
            "alta"
            if cobertura == "edital" and completude >= 0.8
            else "media"
            if disciplinas
            else "baixa"
        ),
        "constantes_aplicadas": {
            "horas_por_topico": HORAS_POR_TOPICO,
            "horas_por_disciplina_sem_detalhe": HORAS_POR_DISCIPLINA_SEM_DETALHE,
            "margem_viabilidade": MARGEM_VIABILIDADE,
            "margem_apertado": MARGEM_APERTADO,
        },
    }


__all__ = ["analisar", "CAMPOS_ENTRADA", "CAMPOS_OPCIONAIS"]
