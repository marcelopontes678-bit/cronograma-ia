import copy
import logging
import uuid
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from app.config import settings
from app.core.exceptions import not_found
from app.database import AsyncSessionLocal
from app.models.orcamento import OrcamentoJob, PreferenciasGlobais, StatusOrcamentoJob
from app.models.usuario import Usuario
from app.schemas.orcamento import Modulo, ModuloManualCreate, PreferenciasGlobaisConfig
from app.services import orcamento_feedback_service
from app.services.orcamento_vision_extractor import (
    LIMIAR_CONFIANCA_REVISAO,
    ExtracaoVisionError,
    extrair_de_pdf,
)

logger = logging.getLogger("smartfactory.orcamento")


class JobInvalidoError(Exception):
    pass


class ConfirmacaoBloqueadaError(Exception):
    """Levantado quando o job ainda tem modulo de baixa confianca nao
    revisado e alguem tenta confirmar mesmo assim."""


async def get_preferencias(db: AsyncSession, current_user: Usuario) -> PreferenciasGlobais:
    """Retorna as PreferenciasGlobais da empresa do usuario autenticado,
    criando o registro com os defaults se ainda nao existir (uma por
    empresa -- nunca 404 aqui, sempre ha um conjunto de diretrizes, mesmo
    que so os defaults)."""
    result = await db.execute(
        select(PreferenciasGlobais).where(PreferenciasGlobais.empresa_id == current_user.empresa_id)
    )
    prefs = result.scalar_one_or_none()
    if prefs is None:
        prefs = PreferenciasGlobais(
            empresa_id=current_user.empresa_id,
            configuracao=PreferenciasGlobaisConfig().model_dump(mode="json"),
        )
        db.add(prefs)
        await db.commit()
        await db.refresh(prefs)
    return prefs


async def atualizar_preferencias(
    db: AsyncSession, current_user: Usuario, config: PreferenciasGlobaisConfig
) -> PreferenciasGlobais:
    prefs = await get_preferencias(db, current_user)
    prefs.configuracao = config.model_dump(mode="json")
    await db.commit()
    await db.refresh(prefs)
    return prefs


async def criar_job(
    db: AsyncSession, current_user: Usuario, arquivo_origem: str, projeto_id: uuid.UUID | None
) -> OrcamentoJob:
    job = OrcamentoJob(
        empresa_id=current_user.empresa_id,
        usuario_id=current_user.id,
        projeto_id=projeto_id,
        arquivo_origem=arquivo_origem,
        status=StatusOrcamentoJob.PROCESSANDO,
        ambientes=[],
        avisos=[],
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return job


async def get_job(db: AsyncSession, job_id: uuid.UUID, current_user: Usuario) -> OrcamentoJob:
    result = await db.execute(select(OrcamentoJob).where(OrcamentoJob.id == job_id))
    job = result.scalar_one_or_none()
    # 404 (nao 403) para nao vazar pra outra empresa nem a existencia do job
    if not job or job.empresa_id != current_user.empresa_id:
        raise not_found("Job de orçamento")
    return job


async def listar_jobs(
    db: AsyncSession, current_user: Usuario, skip: int = 0, limit: int = 20
) -> list[OrcamentoJob]:
    query = (
        select(OrcamentoJob)
        .where(OrcamentoJob.empresa_id == current_user.empresa_id)
        .order_by(OrcamentoJob.created_at.desc())
    )
    result = await db.execute(query.offset(skip).limit(limit))
    return list(result.scalars().all())


async def rodar_extracao_em_background(
    job_id: uuid.UUID, caminho_pdf: Path, pasta_trabalho: Path, empresa_id: uuid.UUID
) -> None:
    """Roda depois da resposta HTTP ja ter sido enviada (FastAPI
    BackgroundTasks) -- precisa da sua propria sessao de banco, a da
    requisicao original ja pode estar fechada."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(OrcamentoJob).where(OrcamentoJob.id == job_id))
        job = result.scalar_one_or_none()
        if job is None:
            logger.error("job=%s: sumiu antes da extracao rodar", job_id)
            return

        result_prefs = await db.execute(
            select(PreferenciasGlobais).where(PreferenciasGlobais.empresa_id == empresa_id)
        )
        prefs_row = result_prefs.scalar_one_or_none()
        preferencias = PreferenciasGlobaisConfig.model_validate(prefs_row.configuracao if prefs_row else {})
        regras_ativas = await orcamento_feedback_service.listar_regras_normalizadas_ativas(db, empresa_id)

        try:
            ambientes, avisos = extrair_de_pdf(
                job_id=str(job_id),
                caminho_pdf=caminho_pdf,
                pasta_trabalho=pasta_trabalho,
                preferencias=preferencias,
                regras_ativas=regras_ativas,
                api_key=settings.ANTHROPIC_API_KEY,
                modelo=settings.ORCAMENTO_MODELO_CLAUDE,
            )
            job.ambientes = [a.model_dump(mode="json") for a in ambientes]
            job.avisos = avisos
            # Status sempre comeca em AGUARDANDO_REVISAO, mesmo com confianca
            # alta em tudo -- so uma confirmacao humana explicita (rota
            # POST /jobs/{id}/confirmar) muda para CONFIRMADO.
            job.status = StatusOrcamentoJob.AGUARDANDO_REVISAO
        except ExtracaoVisionError as exc:
            logger.exception("job=%s: falha na extracao", job_id)
            job.status = StatusOrcamentoJob.ERRO
            job.avisos = [f"Falha na extracao: {exc}"]

        await db.commit()


def _patch_dict_em_lista(ambientes: list[dict], modulo_id: str, patch: dict) -> tuple[list[dict], dict] | None:
    """Aplica um patch parcial (merge raso nos subcampos aninhados) ao
    modulo com esse id, dentro da arvore ambientes/modulos. Retorna
    (nova_arvore, modulo_atualizado) ou None se o modulo nao existir.

    deepcopy de proposito: um shallow copy (`dict(a)` por ambiente) ainda
    compartilha a lista `modulos` original por referencia -- mutar essa
    lista compartilhada ANTES de reatribuir `job.ambientes` faz o valor
    "antigo" (ainda preso na instancia) mudar junto, e o SQLAlchemy, ao
    comparar novo==antigo na reatribuicao, acha que nada mudou e nunca
    emite o UPDATE (bug real encontrado rodando isso de verdade)."""
    nova_arvore = copy.deepcopy(ambientes)
    for ambiente in nova_arvore:
        modulos = ambiente.get("modulos", [])
        for i, modulo in enumerate(modulos):
            if modulo.get("id") == modulo_id:
                atualizado = dict(modulo)
                for chave, valor in patch.items():
                    if isinstance(valor, dict) and isinstance(atualizado.get(chave), dict):
                        atualizado[chave] = {**atualizado[chave], **valor}
                    else:
                        atualizado[chave] = valor
                atualizado["origem"] = patch.get("origem", "confirmado_humano")
                modulos[i] = atualizado
                return nova_arvore, atualizado
    return None


async def atualizar_modulo(
    db: AsyncSession, job_id: uuid.UUID, modulo_id: str, patch: dict, current_user: Usuario
) -> Modulo:
    """Aplica um patch parcial a um modulo especifico (ex: correcao humana
    de dimensao/material) e persiste. Marca origem=confirmado_humano."""
    job = await get_job(db, job_id, current_user)

    resultado = _patch_dict_em_lista(job.ambientes, modulo_id, patch)
    if resultado is None:
        raise JobInvalidoError(f"Modulo {modulo_id!r} nao encontrado no job {job_id!r}")

    nova_arvore, modulo_atualizado = resultado
    job.ambientes = nova_arvore
    flag_modified(job, "ambientes")  # defensivo -- ver docstring de _patch_dict_em_lista
    await db.commit()
    return Modulo.model_validate(modulo_atualizado)


async def adicionar_modulo(
    db: AsyncSession, job_id: uuid.UUID, current_user: Usuario, data: ModuloManualCreate
) -> Modulo:
    job = await get_job(db, job_id, current_user)

    nova_arvore = copy.deepcopy(job.ambientes)  # ver docstring de _patch_dict_em_lista
    ambiente_existente = next((a for a in nova_arvore if a.get("nome_ambiente") == data.nome_ambiente), None)
    if ambiente_existente is None:
        ambiente_existente = {"nome_ambiente": data.nome_ambiente, "modulos": []}
        nova_arvore.append(ambiente_existente)

    ambiente_existente["modulos"].append(data.modulo.model_dump(mode="json"))
    job.ambientes = nova_arvore
    flag_modified(job, "ambientes")
    await db.commit()
    return data.modulo


async def confirmar_job(db: AsyncSession, job_id: uuid.UUID, current_user: Usuario) -> OrcamentoJob:
    """So permite confirmar quando nenhum modulo de origem vision_automatico
    tem confianca abaixo do limiar -- forca revisao humana desses casos
    (via atualizar_modulo) antes de liberar para precificacao."""
    job = await get_job(db, job_id, current_user)

    pendentes = [
        f"{m['id']} ({m.get('nome', '?')}, confianca={m.get('confianca')})"
        for amb in job.ambientes
        for m in amb.get("modulos", [])
        if m.get("origem") == "vision_automatico" and m.get("confianca", 1.0) < LIMIAR_CONFIANCA_REVISAO
    ]
    if pendentes:
        raise ConfirmacaoBloqueadaError(
            f"Job {job_id!s} tem {len(pendentes)} modulo(s) de baixa confianca ainda nao revisados: "
            + "; ".join(pendentes)
        )

    job.status = StatusOrcamentoJob.CONFIRMADO
    await db.commit()
    await db.refresh(job)
    return job
