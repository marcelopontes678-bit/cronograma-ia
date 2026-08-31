"""Armazenamento de jobs de extracao -- um arquivo JSON por job em
storage/jobs/{job_id}/resultado.json. Sem banco de dados de verdade
nesta versao (MVP); a interface fica isolada aqui para trocar por um
banco depois sem mexer nas rotas.
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

from api.schemas.extracao import Ambiente, ExtracaoResultado, Modulo, StatusExtracao
from api.services.vision_extractor import LIMIAR_CONFIANCA_REVISAO


class JobNaoEncontradoError(Exception):
    pass


class JobInvalidoError(Exception):
    pass


class ConfirmacaoBloqueadaError(Exception):
    """Levantado quando o job ainda tem modulo de baixa confianca nao
    revisado e alguem tenta confirmar mesmo assim."""


def _validar_job_id(job_id: str) -> None:
    if not job_id or "/" in job_id or "\\" in job_id or job_id in (".", ".."):
        raise JobInvalidoError(f"job_id invalido: {job_id!r}")


def _dir_job(job_id: str, dir_jobs: Path) -> Path:
    _validar_job_id(job_id)
    return dir_jobs / job_id


def _caminho_resultado(job_id: str, dir_jobs: Path) -> Path:
    return _dir_job(job_id, dir_jobs) / "resultado.json"


def salvar(resultado: ExtracaoResultado, dir_jobs: Path) -> Path:
    dir_job = _dir_job(resultado.job_id, dir_jobs)
    dir_job.mkdir(parents=True, exist_ok=True)
    caminho = _caminho_resultado(resultado.job_id, dir_jobs)

    conteudo = resultado.model_dump_json(indent=2)
    fd, caminho_temp_str = tempfile.mkstemp(dir=dir_job, prefix=".tmp_job_", suffix=".json")
    caminho_temp = Path(caminho_temp_str)
    try:
        with open(fd, "w", encoding="utf-8") as f:
            f.write(conteudo)
        caminho_temp.replace(caminho)
    finally:
        caminho_temp.unlink(missing_ok=True)

    return caminho


def carregar(job_id: str, dir_jobs: Path) -> ExtracaoResultado:
    caminho = _caminho_resultado(job_id, dir_jobs)
    if not caminho.exists():
        raise JobNaoEncontradoError(f"Job nao encontrado: {job_id!r}")
    dados = json.loads(caminho.read_text(encoding="utf-8"))
    return ExtracaoResultado.model_validate(dados)


def atualizar_modulo(job_id: str, modulo_id: str, patch: dict, dir_jobs: Path) -> Modulo:
    """Aplica um patch parcial a um modulo especifico (ex: correcao humana
    de dimensao/material) e persiste. Marca origem=confirmado_humano."""
    resultado = carregar(job_id, dir_jobs)

    for ambiente in resultado.ambientes:
        for i, modulo in enumerate(ambiente.modulos):
            if modulo.id == modulo_id:
                dados_atualizados = modulo.model_dump()
                for chave, valor in patch.items():
                    # merge raso em campos aninhados (dimensoes, componentes,
                    # especificacoes_materiais, auditoria_visual) para nao
                    # exigir o objeto inteiro so pra corrigir um subcampo
                    if isinstance(valor, dict) and isinstance(dados_atualizados.get(chave), dict):
                        dados_atualizados[chave] = {**dados_atualizados[chave], **valor}
                    else:
                        dados_atualizados[chave] = valor
                dados_atualizados["origem"] = patch.get("origem", "confirmado_humano")
                novo_modulo = Modulo.model_validate(dados_atualizados)
                ambiente.modulos[i] = novo_modulo
                salvar(resultado, dir_jobs)
                return novo_modulo

    raise JobInvalidoError(f"Modulo {modulo_id!r} nao encontrado no job {job_id!r}")


def adicionar_modulo(job_id: str, nome_ambiente: str, modulo: Modulo, dir_jobs: Path) -> Modulo:
    resultado = carregar(job_id, dir_jobs)

    ambiente_existente = next((a for a in resultado.ambientes if a.nome_ambiente == nome_ambiente), None)
    if ambiente_existente is None:
        ambiente_existente = Ambiente(nome_ambiente=nome_ambiente)
        resultado.ambientes.append(ambiente_existente)

    ambiente_existente.modulos.append(modulo)
    salvar(resultado, dir_jobs)
    return modulo


def confirmar(job_id: str, dir_jobs: Path) -> ExtracaoResultado:
    """So permite confirmar quando nenhum modulo de origem vision_automatico
    tem confianca abaixo do limiar -- forca revisao humana desses casos
    (via atualizar_modulo) antes de liberar para precificacao."""
    resultado = carregar(job_id, dir_jobs)

    pendentes = [
        f"{m.id} ({m.nome}, confianca={m.confianca})"
        for amb in resultado.ambientes
        for m in amb.modulos
        if m.origem.value == "vision_automatico" and m.confianca < LIMIAR_CONFIANCA_REVISAO
    ]
    if pendentes:
        raise ConfirmacaoBloqueadaError(
            f"Job {job_id!r} tem {len(pendentes)} modulo(s) de baixa confianca ainda nao revisados: "
            + "; ".join(pendentes)
        )

    resultado.status = StatusExtracao.CONFIRMADO
    salvar(resultado, dir_jobs)
    return resultado
