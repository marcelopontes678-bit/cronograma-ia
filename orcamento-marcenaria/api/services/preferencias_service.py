"""Carrega e persiste as Preferencias Globais de producao de cada usuario.

Um arquivo JSON por usuario em storage/preferencias/{usuario_id}.json.
Quando o usuario ainda nao tem preferencias salvas, carregar_preferencias
retorna os defaults do schema (PreferenciasGlobais(usuario_id=...)) em vez
de erro -- e assim que o vision_extractor.py deve poder rodar mesmo antes
do usuario configurar nada.
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

from api.schemas.preferencias import PreferenciasGlobais

_DIR_STORAGE_PADRAO = Path(__file__).resolve().parent.parent / "storage" / "preferencias"


class PreferenciasInvalidasError(Exception):
    pass


def _caminho_arquivo(usuario_id: str, dir_storage: Path) -> Path:
    if not usuario_id or "/" in usuario_id or "\\" in usuario_id or usuario_id in (".", ".."):
        raise PreferenciasInvalidasError(f"usuario_id invalido: {usuario_id!r}")
    return dir_storage / f"{usuario_id}.json"


def carregar_preferencias(usuario_id: str, dir_storage: str | Path | None = None) -> PreferenciasGlobais:
    dir_storage = Path(dir_storage) if dir_storage else _DIR_STORAGE_PADRAO
    caminho = _caminho_arquivo(usuario_id, dir_storage)

    if not caminho.exists():
        return PreferenciasGlobais(usuario_id=usuario_id)

    try:
        dados = json.loads(caminho.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise PreferenciasInvalidasError(f"Arquivo de preferencias corrompido para {usuario_id!r}: {exc}") from exc

    return PreferenciasGlobais.model_validate(dados)


def salvar_preferencias(preferencias: PreferenciasGlobais, dir_storage: str | Path | None = None) -> Path:
    dir_storage = Path(dir_storage) if dir_storage else _DIR_STORAGE_PADRAO
    dir_storage.mkdir(parents=True, exist_ok=True)
    caminho = _caminho_arquivo(preferencias.usuario_id, dir_storage)

    conteudo = preferencias.model_dump_json(indent=2)

    # escrita atomica: grava em arquivo temporario no mesmo diretorio e
    # renomeia -- evita corromper o arquivo se o processo morrer no meio
    # da escrita (renomear e uma operacao atomica no mesmo filesystem).
    fd, caminho_temp_str = tempfile.mkstemp(dir=dir_storage, prefix=".tmp_pref_", suffix=".json")
    caminho_temp = Path(caminho_temp_str)
    try:
        with open(fd, "w", encoding="utf-8") as f:
            f.write(conteudo)
        caminho_temp.replace(caminho)
    finally:
        caminho_temp.unlink(missing_ok=True)  # no-op se o replace() acima ja moveu o arquivo

    return caminho
