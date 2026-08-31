"""Extrai ambientes/modulos de um PDF de projeto via Claude Vision.

Fluxo:
  1. Renderiza as paginas do PDF em imagens (pdf_to_images.py).
  2. Monta o system prompt: template base + Preferencias Globais do
     usuario + Regras Aprendidas ativas do usuario.
  3. Chama a API de mensagens do Claude com as imagens + tool use
     forcado (tool_choice) usando o JSON Schema de schema_saida.json,
     para receber saida estruturada em vez de texto livre.
  4. Valida a resposta com os schemas Pydantic e monta ExtracaoResultado.

Paginas sao processadas em lotes (chunks) para nao estourar o contexto
nem custar caro numa chamada so -- cada lote produz ambientes/modulos
que sao agregados no resultado final.

Nunca inventa dimensao: quando o modelo retorna null pra uma dimensao,
o Modulo correspondente fica com esse campo None (nao um valor
estimado), e a confianca baixa carrega esse sinal adiante pra revisao
humana obrigatoria antes de precificar.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from anthropic import Anthropic

from api.schemas.extracao import Ambiente, ExtracaoResultado, Modulo, OrigemModulo, StatusExtracao
from api.schemas.preferencias import PreferenciasGlobais
from api.services.pdf_to_images import PaginaRenderizada, renderizar_paginas

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


def _montar_system_prompt(preferencias: PreferenciasGlobais, regras_ativas: list[str]) -> str:
    template = (_DIR_PROMPTS / "system_extrator.md").read_text(encoding="utf-8")

    bloco_preferencias = (
        "## Preferencias Globais deste usuario (use para inferir o que o desenho nao especificar):\n"
        f"```json\n{preferencias.model_dump_json(indent=2)}\n```"
    )
    bloco_regras = (
        "## Regras Aprendidas ativas deste usuario (aplique como correcoes automaticas):\n"
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
            return bloco.input

    raise ExtracaoVisionError(
        f"Claude nao retornou o tool_use esperado ('{ferramenta['name']}'). Resposta: {resposta.content}"
    )


def _dict_para_modulo(dado_modulo: dict, contador_id: int) -> Modulo:
    """Constroi o Modulo a partir do dict retornado pelo tool_use do MAX.
    O `id` que o MAX sugere (ex: 'MOD-001') pode colidir entre lotes, entao
    substituimos por um contador globalmente unico do job; o restante do
    dict ja tem o mesmo formato aninhado do schema Pydantic."""
    dado = dict(dado_modulo)
    dado["id"] = f"mod_{contador_id:04d}"
    dado["origem"] = OrigemModulo.VISION_AUTOMATICO
    return Modulo.model_validate(dado)


def extrair_de_pdf(
    job_id: str,
    caminho_pdf: str | Path,
    pasta_trabalho: str | Path,
    preferencias: PreferenciasGlobais,
    regras_ativas: list[str],
    api_key: str,
    modelo: str = MODELO_PADRAO,
    paginas_por_lote: int = PAGINAS_POR_LOTE,
) -> ExtracaoResultado:
    """Ponto de entrada principal. Levanta ExtracaoVisionError em falha
    de comunicacao/parsing -- o chamador (rota da API) decide como
    marcar o job como status=erro."""
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
                modulo = _dict_para_modulo(mod_dado, contador_id)
                ambiente.modulos.append(modulo)

        avisos.extend(resultado_lote.get("avisos", []))

    # Status sempre comeca em AGUARDANDO_REVISAO, mesmo com confianca alta
    # em tudo -- so uma confirmacao humana explicita (rota
    # POST /jobs/{id}/confirmar) muda para CONFIRMADO. Extracao por
    # Vision nunca pula a revisao.
    status = StatusExtracao.AGUARDANDO_REVISAO

    agora = datetime.now(timezone.utc)
    return ExtracaoResultado(
        job_id=job_id,
        arquivo_origem=caminho_pdf.name,
        status=status,
        ambientes=list(ambientes_por_nome.values()),
        avisos=avisos,
        criado_em=agora,
        atualizado_em=agora,
    )
