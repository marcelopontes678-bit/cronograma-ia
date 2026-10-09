"""Classifica as paginas de um job antes da extracao: quais tem desenho de
marcenaria (vistas, elevacoes, cortes, detalhamentos de moveis) e quais sao
so pranchas de outras disciplinas (paginacao de piso, pontos eletricos e
hidraulicos, iluminacao, circuitos, pintura, gesso, layout geral).

Motivo: o extrator processa as paginas em lotes, e um lote so com plantas
de outras disciplinas nao ve as pranchas de marcenaria dos outros lotes --
na extracao real do projeto Home Office ele deduziu 3 modulos a partir das
plantas de piso/eletrica. Mandar so as pranchas de marcenaria para o
extrator evita isso.

Busca por palavras-chave no texto do PDF nao serve: "gaveta" aparece em
"registro de gaveta" na planta hidraulica, "nicho"/"prateleira" na legenda
de iluminacao, "marcenaria" na tabela de pintura. Por isso a classificacao
e uma chamada curta ao modelo com miniaturas das paginas.

A classificacao e uma otimizacao, nunca um ponto de falha: se a chamada
falhar, ou se nenhuma pagina for classificada como marcenaria, o extrator
segue com todas as paginas e registra um aviso."""
from __future__ import annotations

import base64
import logging
from dataclasses import dataclass

import fitz  # PyMuPDF
from anthropic import Anthropic

from app.services.orcamento_pdf_to_images import PaginaRenderizada

logger = logging.getLogger(__name__)

LADO_MINIATURA_PX = 1000  # suficiente para reconhecer o tipo de prancha pelo titulo e pelo desenho
MAX_MINIATURAS_POR_CHAMADA = 90  # limite da API: 100 imagens por requisicao

_FERRAMENTA = {
    "name": "registrar_classificacao",
    "description": "Registra, para cada pagina recebida, se ela contem desenho de marcenaria.",
    "strict": True,
    "input_schema": {
        "type": "object",
        "properties": {
            "paginas": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "arquivo_indice": {"type": "integer"},
                        "pagina": {"type": "integer"},
                        "tem_marcenaria": {"type": "boolean"},
                        "tipo_prancha": {
                            "type": "string",
                            "description": "Titulo ou tipo da prancha, ex: 'Vista A - Marcenaria', 'Planta de Pontos Eletricos'",
                        },
                    },
                    "required": ["arquivo_indice", "pagina", "tem_marcenaria", "tipo_prancha"],
                    "additionalProperties": False,
                },
            }
        },
        "required": ["paginas"],
        "additionalProperties": False,
    },
}

_SYSTEM_PROMPT = """\
Voce classifica pranchas de projetos de arquitetura de interiores para uma \
fabrica de moveis planejados. Para cada pagina recebida, diga se ela contem \
desenho de marcenaria: vista frontal, elevacao, corte, perspectiva ou \
detalhamento de moveis sob medida (armarios, gaveteiros, nichos, paineis, \
prateleiras, bancadas de MDF), com cotas ou especificacao de material.

Pranchas de outras disciplinas nao contem marcenaria, mesmo quando citam \
moveis numa legenda ou mostram o contorno deles: paginacao de piso ou de \
parede, pontos eletricos, pontos hidraulicos, iluminacao, circuitos, gesso e \
forro, pintura, demolir/construir e planta de layout geral. Se uma pagina \
mistura as duas coisas (por exemplo, uma miniatura da planta de layout ao \
lado das vistas de marcenaria), ela contem marcenaria.

Responda com a ferramenta registrar_classificacao, uma entrada por pagina."""


@dataclass
class ResultadoClassificacao:
    paginas_marcenaria: list[PaginaRenderizada]
    avisos: list[str]


def _miniatura_base64(pagina: PaginaRenderizada) -> str:
    """Reduz o PNG ja renderizado da pagina para LADO_MINIATURA_PX no lado maior."""
    doc = fitz.open(str(pagina.caminho_arquivo))
    try:
        retangulo = doc[0].rect
        escala = min(1.0, LADO_MINIATURA_PX / max(retangulo.width, retangulo.height))
        pix = doc[0].get_pixmap(matrix=fitz.Matrix(escala, escala))
        return base64.standard_b64encode(pix.tobytes("png")).decode("ascii")
    finally:
        doc.close()


def _classificar_grupo(client: Anthropic, grupo: list[PaginaRenderizada], modelo: str) -> dict[tuple[int, int], bool]:
    conteudo: list[dict] = []
    for pagina in grupo:
        conteudo.append(
            {
                "type": "text",
                "text": f"Pagina {pagina.numero} do arquivo {pagina.arquivo_indice} ({pagina.nome_arquivo}):",
            }
        )
        conteudo.append(
            {
                "type": "image",
                "source": {"type": "base64", "media_type": "image/png", "data": _miniatura_base64(pagina)},
            }
        )
    conteudo.append({"type": "text", "text": "Classifique cada pagina acima."})

    resposta = client.messages.create(
        model=modelo,
        max_tokens=8000,
        system=_SYSTEM_PROMPT,
        tools=[_FERRAMENTA],
        tool_choice={"type": "tool", "name": _FERRAMENTA["name"]},
        messages=[{"role": "user", "content": conteudo}],
        output_config={"effort": "low"},
    )
    if resposta.stop_reason == "max_tokens":
        raise ValueError("resposta da classificacao cortada por max_tokens")

    for bloco in resposta.content:
        if bloco.type == "tool_use" and bloco.name == _FERRAMENTA["name"]:
            return {
                (item["arquivo_indice"], item["pagina"]): bool(item["tem_marcenaria"])
                for item in bloco.input["paginas"]
            }
    raise ValueError("o modelo nao retornou a classificacao")


def classificar_paginas(
    client: Anthropic, paginas: list[PaginaRenderizada], modelo: str, job_id: str
) -> ResultadoClassificacao:
    """Retorna as paginas que vao para o extrator e os avisos para o job.
    Uma pagina que o modelo nao classificou e mantida (na duvida, extrair)."""
    try:
        classificacao: dict[tuple[int, int], bool] = {}
        for i in range(0, len(paginas), MAX_MINIATURAS_POR_CHAMADA):
            classificacao.update(_classificar_grupo(client, paginas[i : i + MAX_MINIATURAS_POR_CHAMADA], modelo))
    except Exception as exc:  # otimizacao, nunca ponto de falha
        logger.warning("job=%s: classificacao de paginas falhou, extraindo todas: %s", job_id, exc)
        return ResultadoClassificacao(
            paginas_marcenaria=paginas,
            avisos=[
                "Nao foi possivel separar as pranchas de marcenaria das demais; todas as paginas foram "
                "analisadas -- confira se algum modulo foi deduzido de planta eletrica, de piso ou de iluminacao."
            ],
        )

    selecionadas = [p for p in paginas if classificacao.get((p.arquivo_indice, p.numero), True)]
    descartadas = [p for p in paginas if p not in selecionadas]

    if not selecionadas:
        logger.warning("job=%s: nenhuma pagina classificada como marcenaria, extraindo todas", job_id)
        return ResultadoClassificacao(
            paginas_marcenaria=paginas,
            avisos=[
                "Nenhuma prancha foi reconhecida como desenho de marcenaria; todas as paginas foram analisadas "
                "-- confira se o arquivo enviado contem as vistas e detalhamentos dos moveis."
            ],
        )

    avisos = []
    if descartadas:
        lista = ", ".join(f"pagina {p.numero} de {p.nome_arquivo}" for p in descartadas)
        avisos.append(
            f"Pranchas sem desenho de marcenaria (piso, eletrica, iluminacao etc.) nao foram analisadas: {lista}. "
            "Se alguma delas tiver moveis, adicione os modulos manualmente."
        )
    logger.info(
        "job=%s: %d de %d paginas classificadas como marcenaria", job_id, len(selecionadas), len(paginas)
    )
    return ResultadoClassificacao(paginas_marcenaria=selecionadas, avisos=avisos)
