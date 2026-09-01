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

Paginas sao processadas em lotes (chunks) para nao estourar o contexto
nem custar caro numa chamada so -- cada lote produz ambientes/modulos
que sao agregados no resultado final.

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
from app.services.orcamento_pdf_to_images import PaginaRenderizada, renderizar_paginas

logger = logging.getLogger(__name__)

MODELO_PADRAO = "claude-sonnet-5"
LIMIAR_CONFIANCA_REVISAO = 0.7
PAGINAS_POR_LOTE = 4  # paginas de planta/vista sao densas; lotes menores mantem a leitura precisa

_DIR_PROMPTS = Path(__file__).resolve().parent.parent / "prompts"


class ExtracaoVisionError(Exception):
    pass


def _carregar_schema_ferramenta() -> dict:
    caminho = _DIR_PROMPTS / "schema_saida.json"
    return json.loads(caminho.read_text(encoding="utf-8"))


def _montar_system_prompt(preferencias: PreferenciasGlobaisConfig, regras_ativas: list[str]) -> str:
    template = (_DIR_PROMPTS / "system_extrator.md").read_text(encoding="utf-8")

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


def _paginas_para_lotes(paginas: list[PaginaRenderizada], tamanho_lote: int) -> list[list[PaginaRenderizada]]:
    return [paginas[i : i + tamanho_lote] for i in range(0, len(paginas), tamanho_lote)]


def _chamar_claude_para_lote(
    client: Anthropic,
    system_prompt: str,
    lote: list[PaginaRenderizada],
    ferramenta: dict,
    modelo: str,
) -> dict:
    blocos_conteudo = []
    for pagina in lote:
        blocos_conteudo.append({"type": "text", "text": f"Pagina {pagina.numero} do PDF:"})
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
    blocos_conteudo.append(
        {
            "type": "text",
            "text": "Extraia os ambientes e modulos de marcenaria destas paginas, seguindo as instrucoes do system prompt. Use a ferramenta 'registrar_extracao' para responder.",
        }
    )

    resposta = client.messages.create(
        model=modelo,
        max_tokens=8192,
        system=system_prompt,
        tools=[ferramenta],
        tool_choice={"type": "tool", "name": ferramenta["name"]},
        messages=[{"role": "user", "content": blocos_conteudo}],
    )

    for bloco in resposta.content:
        if bloco.type == "tool_use" and bloco.name == ferramenta["name"]:
            return _normalizar_input_ferramenta(bloco.input)

    raise ExtracaoVisionError(
        f"Claude nao retornou o tool_use esperado ('{ferramenta['name']}'). Resposta: {resposta.content}"
    )


def _normalizar_input_ferramenta(entrada: dict) -> dict:
    """Confirmado empiricamente contra a API real (nao era um risco
    hipotetico do schema): as vezes o modelo serializa o objeto
    {"ambientes": [...], "avisos": [...]} inteiro como uma STRING dentro
    do proprio campo "ambientes", em vez de popular o array direto --
    provavelmente por causa da profundidade do schema aninhado. Detecta
    esse formato e desembrulha, registrando um aviso explicito em vez de
    aceitar silenciosamente."""
    if not isinstance(entrada.get("ambientes"), str):
        return entrada

    try:
        desembrulhado = json.loads(entrada["ambientes"])
    except json.JSONDecodeError as exc:
        raise ExtracaoVisionError(
            f"Campo 'ambientes' veio como string mas nao e JSON valido: {exc}"
        ) from exc

    if not isinstance(desembrulhado, dict) or "ambientes" not in desembrulhado:
        raise ExtracaoVisionError(
            "Campo 'ambientes' veio como string, mas o JSON desembrulhado nao tem o formato esperado "
            f"(chaves: {list(desembrulhado.keys()) if isinstance(desembrulhado, dict) else type(desembrulhado)})."
        )

    logger.warning(
        "Resposta do modelo veio com 'ambientes' serializado como string em vez de array -- desembrulhado automaticamente."
    )
    avisos = list(entrada.get("avisos") or []) + list(desembrulhado.get("avisos") or [])
    avisos.append(
        "A resposta do modelo veio com o campo 'ambientes' serializado como string (formato inesperado do schema) "
        "-- corrigida automaticamente, mas revise os dados deste lote com atencao extra."
    )
    return {"ambientes": desembrulhado["ambientes"], "avisos": avisos}


def _dict_para_modulo(dado_modulo: dict, contador_id: int) -> tuple[Modulo, str | None]:
    """Constroi o Modulo a partir do dict retornado pelo tool_use do MARC.
    O `id` que o MARC sugere (ex: 'MOD-001') pode colidir entre lotes, entao
    substituimos por um contador globalmente unico do job; o restante do
    dict ja tem o mesmo formato aninhado do schema Pydantic.

    Retorna (modulo, aviso). Confirmado empiricamente contra a API real: o
    modelo as vezes estoura levemente o range 0-1000 do bounding_box (e uma
    coordenada normalizada estimada visualmente, nao uma cota exata) -- em
    vez de descartar o modulo inteiro, o valor e limitado (clamp) ao range
    valido e o desvio fica registrado num aviso, nunca escondido."""
    dado = dict(dado_modulo)
    dado["id"] = f"mod_{contador_id:04d}"
    dado["origem"] = OrigemModulo.VISION_AUTOMATICO

    aviso = None
    bbox = dado.get("auditoria_visual", {}).get("bounding_box")
    if isinstance(bbox, list) and any(not isinstance(v, int) or v < 0 or v > 1000 for v in bbox):
        bbox_original = list(bbox)
        bbox_corrigido = [max(0, min(1000, round(v))) for v in bbox]
        dado["auditoria_visual"]["bounding_box"] = bbox_corrigido
        aviso = (
            f"{dado['id']} ({dado.get('nome', '?')}): bounding_box {bbox_original} fora do range 0-1000, "
            f"ajustado para {bbox_corrigido} -- confira a posicao do destaque visual manualmente."
        )

    return Modulo.model_validate(dado), aviso


def extrair_de_pdf(
    job_id: str,
    caminho_pdf: str | Path,
    pasta_trabalho: str | Path,
    preferencias: PreferenciasGlobaisConfig,
    regras_ativas: list[str],
    api_key: str,
    modelo: str = MODELO_PADRAO,
    paginas_por_lote: int = PAGINAS_POR_LOTE,
) -> tuple[list[Ambiente], list[str]]:
    """Ponto de entrada principal. Levanta ExtracaoVisionError em falha
    de comunicacao/parsing -- o chamador decide como marcar o job como
    status=erro. Sincrono/bloqueante de proposito -- quem chama a partir
    de uma rota async deve rodar via asyncio.to_thread (ver
    orcamento_service.py)."""
    caminho_pdf = Path(caminho_pdf)
    pasta_paginas = Path(pasta_trabalho) / "paginas"

    paginas = renderizar_paginas(caminho_pdf, pasta_paginas)
    logger.info("job=%s: %d paginas renderizadas", job_id, len(paginas))

    system_prompt = _montar_system_prompt(preferencias, regras_ativas)
    ferramenta = _carregar_schema_ferramenta()
    client = Anthropic(api_key=api_key)

    ambientes_por_nome: dict[str, Ambiente] = {}
    avisos: list[str] = []
    contador_id = 0

    for lote in _paginas_para_lotes(paginas, paginas_por_lote):
        try:
            resultado_lote = _chamar_claude_para_lote(client, system_prompt, lote, ferramenta, modelo)
        except Exception as exc:  # falha de rede/API -- nao mascarar, propagar com contexto
            paginas_str = ",".join(str(p.numero) for p in lote)
            raise ExtracaoVisionError(f"job={job_id}: falha ao extrair paginas {paginas_str}: {exc}") from exc

        for amb_dado in resultado_lote.get("ambientes", []):
            nome_amb = amb_dado["nome_ambiente"]
            ambiente = ambientes_por_nome.setdefault(nome_amb, Ambiente(nome_ambiente=nome_amb))
            for mod_dado in amb_dado.get("modulos", []):
                contador_id += 1
                try:
                    modulo, aviso_bbox = _dict_para_modulo(mod_dado, contador_id)
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
                if aviso_bbox:
                    avisos.append(aviso_bbox)

        avisos.extend(resultado_lote.get("avisos", []))

    return list(ambientes_por_nome.values()), avisos
