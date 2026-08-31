"""Auto-aprendizado: normaliza uma correcao em linguagem natural do
marceneiro numa regra reusavel e persiste por usuario, para injecao no
system prompt do vision_extractor.py nas proximas extracoes.

Um arquivo JSON por usuario em storage/regras_aprendidas/{usuario_id}.json,
contendo a lista de RegraAprendida (ativas e desativadas -- desativar e
soft delete, nunca apaga o historico).
"""
from __future__ import annotations

import json
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path

from anthropic import Anthropic

from api.schemas.feedback import FeedbackRequest, FeedbackResponse, RegraAprendida

_DIR_STORAGE_PADRAO = Path(__file__).resolve().parent.parent / "storage" / "regras_aprendidas"

MODELO_PADRAO = "claude-sonnet-5"

_SYSTEM_PROMPT_NORMALIZACAO = """\
Voce reescreve uma correcao informal de um marceneiro sobre a leitura de \
projetos de marcenaria (feita por um extrator de IA) numa REGRA DE SISTEMA \
reusavel, objetiva e sem ambiguidade -- para ser injetada no prompt de um \
agente extrator em execucoes futuras.

Regras de estilo:
- Uma frase imperativa, comecando com "Quando..." ou "Sempre que...".
- Sem referencia a um projeto/modulo especifico (generalize).
- Sem inventar excecoes ou condicoes que o usuario nao mencionou.
- Se a instrucao do usuario for ambigua ou nao fizer sentido como regra \
geral, responda exatamente com a instrucao original sem reescrever \
(nao tente adivinhar a intencao).

Responda APENAS com a regra reescrita, sem explicacoes."""


class FeedbackInvalidoError(Exception):
    pass


def _caminho_arquivo(usuario_id: str, dir_storage: Path) -> Path:
    if not usuario_id or "/" in usuario_id or "\\" in usuario_id or usuario_id in (".", ".."):
        raise FeedbackInvalidoError(f"usuario_id invalido: {usuario_id!r}")
    return dir_storage / f"{usuario_id}.json"


def _carregar_regras(usuario_id: str, dir_storage: Path) -> list[RegraAprendida]:
    caminho = _caminho_arquivo(usuario_id, dir_storage)
    if not caminho.exists():
        return []
    try:
        dados = json.loads(caminho.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise FeedbackInvalidoError(f"Arquivo de regras corrompido para {usuario_id!r}: {exc}") from exc
    return [RegraAprendida.model_validate(r) for r in dados]


def _salvar_regras(usuario_id: str, regras: list[RegraAprendida], dir_storage: Path) -> None:
    dir_storage.mkdir(parents=True, exist_ok=True)
    caminho = _caminho_arquivo(usuario_id, dir_storage)
    conteudo = json.dumps([json.loads(r.model_dump_json()) for r in regras], ensure_ascii=False, indent=2)

    fd, caminho_temp_str = tempfile.mkstemp(dir=dir_storage, prefix=".tmp_regras_", suffix=".json")
    caminho_temp = Path(caminho_temp_str)
    try:
        with open(fd, "w", encoding="utf-8") as f:
            f.write(conteudo)
        caminho_temp.replace(caminho)
    finally:
        caminho_temp.unlink(missing_ok=True)


def _normalizar_instrucao_via_llm(instrucao: str, api_key: str, modelo: str) -> str:
    client = Anthropic(api_key=api_key)
    resposta = client.messages.create(
        model=modelo,
        max_tokens=300,
        system=_SYSTEM_PROMPT_NORMALIZACAO,
        messages=[{"role": "user", "content": instrucao}],
    )
    blocos_texto = [b.text for b in resposta.content if b.type == "text"]
    if not blocos_texto:
        raise FeedbackInvalidoError(f"Claude nao retornou texto ao normalizar a instrucao: {resposta.content}")
    return "".join(blocos_texto).strip()


def registrar_feedback(
    request: FeedbackRequest,
    api_key: str,
    modelo: str = MODELO_PADRAO,
    dir_storage: str | Path | None = None,
) -> FeedbackResponse:
    dir_storage = Path(dir_storage) if dir_storage else _DIR_STORAGE_PADRAO

    try:
        regra_normalizada = _normalizar_instrucao_via_llm(request.instrucao, api_key, modelo)
    except FeedbackInvalidoError:
        raise
    except Exception as exc:  # falha de rede/API -- nao mascarar
        raise FeedbackInvalidoError(f"usuario={request.usuario_id}: falha ao normalizar instrucao via LLM: {exc}") from exc

    nova_regra = RegraAprendida(
        id=f"regra_{uuid.uuid4().hex[:8]}",
        usuario_id=request.usuario_id,
        instrucao_original=request.instrucao,
        regra_normalizada=regra_normalizada,
        origem_job_id=request.job_id,
        origem_modulo_id=request.modulo_id,
        ativa=True,
        criado_em=datetime.now(timezone.utc),
    )

    regras = _carregar_regras(request.usuario_id, dir_storage)
    regras.append(nova_regra)
    _salvar_regras(request.usuario_id, regras, dir_storage)

    total_ativas = sum(1 for r in regras if r.ativa)
    return FeedbackResponse(regra=nova_regra, total_regras_ativas_usuario=total_ativas)


def listar_regras(usuario_id: str, dir_storage: str | Path | None = None) -> list[RegraAprendida]:
    """Todas as regras (ativas e desativadas), para o marceneiro revisar."""
    dir_storage = Path(dir_storage) if dir_storage else _DIR_STORAGE_PADRAO
    return _carregar_regras(usuario_id, dir_storage)


def listar_regras_normalizadas_ativas(usuario_id: str, dir_storage: str | Path | None = None) -> list[str]:
    """Usado por vision_extractor.py para montar o system prompt -- so o
    texto das regras ativas, na ordem em que foram criadas."""
    dir_storage = Path(dir_storage) if dir_storage else _DIR_STORAGE_PADRAO
    return [r.regra_normalizada for r in _carregar_regras(usuario_id, dir_storage) if r.ativa]


def desativar_regra(usuario_id: str, regra_id: str, dir_storage: str | Path | None = None) -> RegraAprendida:
    """Soft delete -- nunca remove do historico, so marca ativa=False."""
    dir_storage = Path(dir_storage) if dir_storage else _DIR_STORAGE_PADRAO
    regras = _carregar_regras(usuario_id, dir_storage)

    for regra in regras:
        if regra.id == regra_id:
            regra.ativa = False
            _salvar_regras(usuario_id, regras, dir_storage)
            return regra

    raise FeedbackInvalidoError(f"Regra {regra_id!r} nao encontrada para usuario {usuario_id!r}")
