"""Extrai ambientes/modulos de um PDF de projeto via Claude Vision (persona
MARC, ver app/prompts/system_extrator.md).

Fluxo:
  1. Renderiza as paginas do PDF em imagens (orcamento_pdf_to_images.py).
  2. Monta o system prompt: template base + Preferencias Globais da
     empresa + Regras Aprendidas ativas da empresa.
  3. Chama a API de mensagens do Claude com as imagens + tool use
     forcado (tool_choice) usando o JSON Schema de schema_saida.json,
     para receber saida estruturada em vez de texto livre.
  4. Valida a resposta com os schemas Pydantic (app.schemas.orcamento).

As paginas vao em lotes de ate MAX_IMAGENS_POR_CHAMADA imagens (pagina +
recortes), cada lote produz ambientes/modulos que sao agregados no
resultado final. Testado contra a API real num projeto de 9 pranchas A3:
o job inteiro numa chamada so (45 imagens) obriga a reduzir cada imagem
para 2000px e o modelo passou a fundir modulos e localizar pior; lotes
de 20 imagens a 2576px mantiveram os modulos separados.

O modelo informa o bounding_box em pixels da imagem em que mediu (cada
imagem vai rotulada com o proprio tamanho); a conversao para 0-1000
relativo a pagina inteira e feita aqui no codigo.

Nunca inventa dimensao: quando o modelo retorna null pra uma dimensao,
o Modulo correspondente fica com esse campo None (nao um valor
estimado), e a confianca baixa carrega esse sinal adiante pra revisao
humana obrigatoria antes de precificar.

Retorna (ambientes, avisos) em vez de um objeto de resultado persistido
inteiro -- a persistencia em Postgres (OrcamentoJob) e responsabilidade
de quem chama (orcamento_service.py), nao deste modulo, que so sabe falar
com a API do Claude."""
from __future__ import annotations

import json
import logging
from pathlib import Path

from anthropic import Anthropic
from pydantic import ValidationError

from app.schemas.orcamento import Ambiente, Modulo, OrigemModulo, PreferenciasGlobaisConfig
from app.services.orcamento_pdf_to_images import PaginaRenderizada, RecortePagina, renderizar_paginas

logger = logging.getLogger(__name__)

MODELO_PADRAO = "claude-sonnet-5"
LIMIAR_CONFIANCA_REVISAO = 0.7
# Acima de 20 imagens por chamada a API limita cada imagem a 2000px (ver
# LADO_MAX_PX em orcamento_pdf_to_images.py). O limite de tamanho da
# requisicao e 32MB, e o base64 aumenta ~33%: 20MB de PNG ficam abaixo de 27MB.
MAX_IMAGENS_POR_CHAMADA = 20
MAX_BYTES_POR_CHAMADA = 20_000_000

_DIR_PROMPTS = Path(__file__).resolve().parent.parent / "prompts"


class ExtracaoVisionError(Exception):
    pass


def _carregar_schema_ferramenta() -> dict:
    caminho = _DIR_PROMPTS / "schema_saida.json"
    return json.loads(caminho.read_text(encoding="utf-8"))


def _montar_system_prompt(preferencias: PreferenciasGlobaisConfig, regras_ativas: list[str]) -> str:
    template = (_DIR_PROMPTS / "system_extrator.md").read_text(encoding="utf-8")
    # O cabecalho antes do primeiro "---" e nota para desenvolvedores, nao vai pro modelo.
    template = template.split("\n---\n", 1)[1].lstrip()

    bloco_preferencias = (
        "## Preferencias Globais desta empresa (use para inferir o que o desenho nao especificar):\n"
        f"```json\n{preferencias.model_dump_json(indent=2)}\n```"
    )
    bloco_regras = (
        "## Regras Aprendidas ativas desta empresa (aplique como correcoes automaticas):\n"
        + ("\n".join(f"- {r}" for r in regras_ativas) if regras_ativas else "(nenhuma regra aprendida ainda)")
    )

    prompt = template.replace("<!-- PREFERENCIAS_GLOBAIS_DO_USUARIO -->", bloco_preferencias)
    prompt = prompt.replace("<!-- REGRAS_APRENDIDAS_DO_USUARIO -->", bloco_regras)
    return prompt


def _montar_lotes(
    paginas: list[PaginaRenderizada],
    recortes_por_pagina: dict[tuple[int, int], list[RecortePagina]],
) -> list[list[PaginaRenderizada]]:
    """Agrupa as paginas (cada uma junto com seus recortes) no menor numero
    de chamadas que respeita MAX_IMAGENS_POR_CHAMADA e MAX_BYTES_POR_CHAMADA."""
    lotes: list[list[PaginaRenderizada]] = []
    lote: list[PaginaRenderizada] = []
    imagens = bytes_lote = 0
    for pagina in paginas:
        recortes = recortes_por_pagina.get((pagina.arquivo_indice, pagina.numero), [])
        imagens_pagina = 1 + len(recortes)
        bytes_pagina = pagina.caminho_arquivo.stat().st_size + sum(r.caminho_arquivo.stat().st_size for r in recortes)
        if lote and (imagens + imagens_pagina > MAX_IMAGENS_POR_CHAMADA or bytes_lote + bytes_pagina > MAX_BYTES_POR_CHAMADA):
            lotes.append(lote)
            lote, imagens, bytes_lote = [], 0, 0
        lote.append(pagina)
        imagens += imagens_pagina
        bytes_lote += bytes_pagina
    if lote:
        lotes.append(lote)
    return lotes


def _chamar_claude_para_lote(
    client: Anthropic,
    system_prompt: str,
    lote: list[PaginaRenderizada],
    recortes_por_pagina: dict[tuple[int, int], list[RecortePagina]],
    ferramenta: dict,
    modelo: str,
) -> dict:
    blocos_conteudo = []
    for pagina in lote:
        blocos_conteudo.append(
            {
                "type": "text",
                "text": (
                    f"Pagina {pagina.numero} do arquivo {pagina.arquivo_indice} "
                    f"({pagina.nome_arquivo}) -- visao geral, imagem de "
                    f"{pagina.largura_px}x{pagina.altura_px} px:"
                ),
            }
        )
        blocos_conteudo.append(
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": pagina.media_type,
                    "data": pagina.base64(),
                },
            }
        )
        for recorte in recortes_por_pagina.get((pagina.arquivo_indice, pagina.numero), []):
            blocos_conteudo.append(
                {
                    "type": "text",
                    "text": (
                        f"Recorte em alta resolucao da pagina {pagina.numero} do arquivo "
                        f"{pagina.arquivo_indice} ({pagina.nome_arquivo}), quadrante "
                        f"{recorte.rotulo}, imagem de {recorte.largura_px}x{recorte.altura_px} px "
                        f"(use para ler texto pequeno/cotas finas ilegiveis na visao geral acima)."
                    ),
                }
            )
            blocos_conteudo.append(
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": recorte.media_type,
                        "data": recorte.base64(),
                    },
                }
            )
    blocos_conteudo.append(
        {
            "type": "text",
            "text": "Extraia os ambientes e modulos de marcenaria destas paginas, seguindo as instrucoes do system prompt. Use a ferramenta 'registrar_extracao' para responder.",
        }
    )

    # Streaming porque a resposta de um lote de pranchas densas pode ser
    # longa, e o thinking adaptativo (padrao no Sonnet 5) conta dentro de
    # max_tokens. Sem streaming o SDK recusa max_tokens desse tamanho.
    with client.messages.stream(
        model=modelo,
        max_tokens=64000,
        system=system_prompt,
        tools=[ferramenta],
        tool_choice={"type": "tool", "name": ferramenta["name"]},
        messages=[{"role": "user", "content": blocos_conteudo}],
    ) as stream:
        resposta = stream.get_final_message()

    if resposta.stop_reason == "max_tokens":
        raise ExtracaoVisionError(
            "Resposta cortada por max_tokens -- a lista de modulos deste lote veio incompleta."
        )

    for bloco in resposta.content:
        if bloco.type == "tool_use" and bloco.name == ferramenta["name"]:
            return bloco.input

    raise ExtracaoVisionError(
        f"Claude nao retornou o tool_use esperado ('{ferramenta['name']}'). Resposta: {resposta.content}"
    )


def _pixels_para_normalizado(bbox_px: list, largura_px: int, altura_px: int) -> list[float]:
    """Converte [y_min, x_min, y_max, x_max] em pixels de uma imagem de
    largura_px x altura_px para a escala 0-1000 dessa mesma imagem."""
    return [
        bbox_px[0] * 1000 / altura_px,
        bbox_px[1] * 1000 / largura_px,
        bbox_px[2] * 1000 / altura_px,
        bbox_px[3] * 1000 / largura_px,
    ]


def _converter_bbox_de_recorte(bbox: list[int], faixa_recorte: list[int]) -> list[int]:
    """Converte um bounding_box 0-1000 relativo a um recorte para 0-1000
    relativo a pagina inteira, dada a faixa [y_min, x_min, y_max, x_max]
    que o recorte ocupa na pagina."""
    y0, x0, y1, x1 = faixa_recorte
    return [
        y0 + bbox[0] * (y1 - y0) / 1000,
        x0 + bbox[1] * (x1 - x0) / 1000,
        y0 + bbox[2] * (y1 - y0) / 1000,
        x0 + bbox[3] * (x1 - x0) / 1000,
    ]


def _dict_para_modulo(
    dado_modulo: dict,
    contador_id: int,
    total_arquivos: int,
    paginas_por_chave: dict[tuple[int, int], PaginaRenderizada],
    recortes_por_pagina: dict[tuple[int, int], list[RecortePagina]],
) -> tuple[Modulo, list[str]]:
    """Constroi o Modulo a partir do dict retornado pelo tool_use do MARC.
    O `id` que o MARC sugere (ex: 'MOD-001') pode colidir entre lotes, entao
    substituimos por um contador globalmente unico do job; o restante do
    dict ja tem o mesmo formato aninhado do schema Pydantic.

    O bounding_box chega em pixels da imagem em que o modelo mediu (a
    visao geral da pagina, ou o recorte indicado em `recorte_rotulo`) e sai
    em 0-1000 relativo a pagina inteira. Se a imagem nao for encontrada, ou
    o valor convertido cair fora de 0-1000, o valor e limitado (clamp) ao
    range valido e o desvio fica registrado num aviso, nunca escondido --
    em vez de descartar o modulo inteiro. O mesmo
    vale para `arquivo_indice`: se o modelo relatar um indice fora da faixa
    de arquivos enviados, ele e limitado a 0 e o desvio e registrado."""
    dado = dict(dado_modulo)
    dado["id"] = f"mod_{contador_id:04d}"
    dado["origem"] = OrigemModulo.VISION_AUTOMATICO

    avisos: list[str] = []
    auditoria = dado.get("auditoria_visual", {})
    rotulo_recorte = auditoria.pop("recorte_rotulo", None)
    bbox_px = auditoria.get("bounding_box")
    if isinstance(bbox_px, list) and len(bbox_px) == 4:
        chave = (auditoria.get("arquivo_indice", 0), auditoria.get("pagina_pdf"))
        if rotulo_recorte:
            recorte = next((r for r in recortes_por_pagina.get(chave, []) if r.rotulo == rotulo_recorte), None)
            if recorte:
                bbox_recorte = _pixels_para_normalizado(bbox_px, recorte.largura_px, recorte.altura_px)
                auditoria["bounding_box"] = _converter_bbox_de_recorte(bbox_recorte, recorte.bbox_pagina_normalizado)
            else:
                avisos.append(
                    f"{dado['id']} ({dado.get('nome', '?')}): bounding_box informado no recorte '{rotulo_recorte}', "
                    f"que nao existe para essa pagina -- confira a posicao do destaque visual manualmente."
                )
        elif chave in paginas_por_chave:
            pagina = paginas_por_chave[chave]
            auditoria["bounding_box"] = _pixels_para_normalizado(bbox_px, pagina.largura_px, pagina.altura_px)
        else:
            avisos.append(
                f"{dado['id']} ({dado.get('nome', '?')}): pagina {chave[1]} do arquivo {chave[0]} nao existe no job "
                f"-- confira a posicao do destaque visual manualmente."
            )
    bbox = auditoria.get("bounding_box")
    if isinstance(bbox, list) and all(isinstance(v, (int, float)) and 0 <= v <= 1000 for v in bbox):
        auditoria["bounding_box"] = [round(v) for v in bbox]
        bbox = auditoria["bounding_box"]
    if isinstance(bbox, list) and any(not isinstance(v, int) or v < 0 or v > 1000 for v in bbox):
        bbox_original = [round(v) if isinstance(v, (int, float)) else v for v in bbox]
        bbox_corrigido = [max(0, min(1000, round(v))) for v in bbox]
        dado["auditoria_visual"]["bounding_box"] = bbox_corrigido
        avisos.append(
            f"{dado['id']} ({dado.get('nome', '?')}): bounding_box {bbox_original} fora do range 0-1000, "
            f"ajustado para {bbox_corrigido} -- confira a posicao do destaque visual manualmente."
        )

    arquivo_indice = dado.get("auditoria_visual", {}).get("arquivo_indice")
    if isinstance(arquivo_indice, int) and not (0 <= arquivo_indice < total_arquivos):
        avisos.append(
            f"{dado['id']} ({dado.get('nome', '?')}): arquivo_indice {arquivo_indice} fora da faixa de "
            f"arquivos enviados (0-{total_arquivos - 1}), ajustado para 0 -- confira o destaque visual manualmente."
        )
        dado["auditoria_visual"]["arquivo_indice"] = 0

    return Modulo.model_validate(dado), avisos


def extrair_de_pdf(
    job_id: str,
    caminhos_pdf: list[str | Path],
    pasta_trabalho: str | Path,
    preferencias: PreferenciasGlobaisConfig,
    regras_ativas: list[str],
    api_key: str,
    modelo: str = MODELO_PADRAO,
) -> tuple[list[Ambiente], list[str]]:
    """Ponto de entrada principal. Aceita um ou mais PDFs do mesmo job (ex:
    planta tecnica + render 3D do mesmo ambiente) para que o extrator cruze
    as referencias visuais entre eles na mesma chamada -- o caso de um
    unico arquivo e so o caso trivial de uma lista de tamanho 1, sem
    mudanca de comportamento observavel. Levanta ExtracaoVisionError em
    falha de comunicacao/parsing -- o chamador decide como marcar o job
    como status=erro. Sincrono/bloqueante de proposito -- quem chama a
    partir de uma rota async deve rodar via asyncio.to_thread (ver
    orcamento_service.py)."""
    caminhos_pdf = [Path(c) for c in caminhos_pdf]
    pasta_paginas = Path(pasta_trabalho) / "paginas"

    paginas, recortes = renderizar_paginas(caminhos_pdf, pasta_paginas)
    paginas_por_chave = {(p.arquivo_indice, p.numero): p for p in paginas}
    recortes_por_pagina: dict[tuple[int, int], list[RecortePagina]] = {}
    for recorte in recortes:
        recortes_por_pagina.setdefault((recorte.arquivo_indice, recorte.pagina_numero), []).append(recorte)
    logger.info(
        "job=%s: %d arquivo(s), %d paginas renderizadas, %d recortes de alta resolucao gerados",
        job_id,
        len(caminhos_pdf),
        len(paginas),
        len(recortes),
    )

    system_prompt = _montar_system_prompt(preferencias, regras_ativas)
    ferramenta = _carregar_schema_ferramenta()
    client = Anthropic(api_key=api_key)

    ambientes_por_nome: dict[str, Ambiente] = {}
    avisos: list[str] = []
    contador_id = 0

    for lote in _montar_lotes(paginas, recortes_por_pagina):
        try:
            resultado_lote = _chamar_claude_para_lote(client, system_prompt, lote, recortes_por_pagina, ferramenta, modelo)
        except Exception as exc:  # falha de rede/API -- nao mascarar, propagar com contexto
            paginas_str = ",".join(str(p.numero) for p in lote)
            raise ExtracaoVisionError(f"job={job_id}: falha ao extrair paginas {paginas_str}: {exc}") from exc

        for amb_dado in resultado_lote.get("ambientes", []):
            nome_amb = amb_dado["nome_ambiente"]
            ambiente = ambientes_por_nome.setdefault(nome_amb, Ambiente(nome_ambiente=nome_amb))
            for mod_dado in amb_dado.get("modulos", []):
                contador_id += 1
                try:
                    modulo, avisos_modulo = _dict_para_modulo(
                        mod_dado, contador_id, len(caminhos_pdf), paginas_por_chave, recortes_por_pagina
                    )
                except ValidationError as exc:
                    nome_mod = mod_dado.get("nome", "?")
                    avisos.append(
                        f"mod_{contador_id:04d} ({nome_mod}) no ambiente '{nome_amb}': descartado, "
                        f"resposta do modelo veio com dados invalidos ({exc.error_count()} erro(s) de validacao) "
                        f"-- confira o desenho manualmente, este modulo NAO entrou no orcamento. Detalhe: {exc}"
                    )
                    logger.warning("job=%s: modulo descartado por ValidationError: %s", job_id, exc)
                    continue
                ambiente.modulos.append(modulo)
                avisos.extend(avisos_modulo)

        avisos.extend(resultado_lote.get("avisos", []))

    return list(ambientes_por_nome.values()), avisos
