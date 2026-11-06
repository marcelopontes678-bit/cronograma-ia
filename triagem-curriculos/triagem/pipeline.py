"""Fluxo completo da triagem, usado pela linha de comando e pela tela web."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Callable

from pydantic import TypeAdapter

from .ia import MODELO_PADRAO, Triador
from .leitura import ler
from .modelos import Candidato, ResumoVagaIA, Vaga
from .relatorio import ranking, salvar_csv, salvar_html

# Chamado a cada currículo concluído: (feitos, total, candidato).
Progresso = Callable[[int, int, Candidato], None]


class VagasInvalidas(ValueError):
    pass


def validar_vagas(dados) -> list[Vaga]:
    try:
        vagas = TypeAdapter(list[Vaga]).validate_python(dados)
    except Exception as e:
        raise VagasInvalidas(f"Vagas em formato inválido: {e}") from e
    if not vagas:
        raise VagasInvalidas("Cadastre pelo menos uma vaga.")
    ids = [v.id for v in vagas]
    if len(ids) != len(set(ids)):
        raise VagasInvalidas("Há vagas com o mesmo id.")
    for v in vagas:
        if not v.titulo.strip():
            raise VagasInvalidas("Toda vaga precisa de um título.")
        if not (v.obrigatorios or v.desejaveis):
            raise VagasInvalidas(f"A vaga '{v.titulo}' não tem nenhum requisito.")
    return vagas


def carregar_vagas(caminho: Path) -> list[Vaga]:
    return validar_vagas(json.loads(caminho.read_text(encoding="utf-8")))


async def triar(
    vagas: list[Vaga],
    arquivos: list[Path],
    saida: Path,
    *,
    top: int = 5,
    modelo: str = MODELO_PADRAO,
    concorrencia: int = 5,
    usar_cache: bool = True,
    ao_progredir: Progresso | None = None,
    ao_resumir: Callable[[], None] | None = None,
) -> list[Candidato]:
    """Fase 1 (cada currículo), fase 2 (resumo por vaga) e grava relatório + CSV em `saida`."""
    saida.mkdir(parents=True, exist_ok=True)
    triador = Triador(
        vagas,
        modelo=modelo,
        concorrencia=concorrencia,
        pasta_cache=saida / ".cache" if usar_cache else None,
    )
    feitos = 0

    async def um(caminho: Path) -> Candidato:
        nonlocal feitos
        try:
            doc = ler(caminho)
        except Exception as e:  # arquivo corrompido não pode derrubar os outros 199
            c = Candidato(arquivo=caminho.name, erro=f"Não foi possível ler o arquivo: {e}")
        else:
            c = await triador.analisar(doc)
        feitos += 1
        if ao_progredir:
            ao_progredir(feitos, len(arquivos), c)
        return c

    candidatos = list(await asyncio.gather(*(um(p) for p in arquivos)))

    if ao_resumir:
        ao_resumir()
    resumos: dict[str, ResumoVagaIA | str] = {}

    async def resumo(vaga: Vaga):
        aprovados, _ = ranking(vaga, candidatos)
        if not aprovados or top <= 0:
            return
        try:
            resumos[vaga.id] = await triador.resumir_vaga(vaga, aprovados[:top])
        except Exception as e:
            resumos[vaga.id] = str(e)

    await asyncio.gather(*(resumo(v) for v in vagas))

    salvar_csv(saida / "ranking.csv", vagas, candidatos)
    salvar_html(saida / "relatorio.html", vagas, candidatos, resumos)
    return candidatos
