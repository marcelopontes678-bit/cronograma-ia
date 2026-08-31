import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import not_found
from app.models.orcamento import OrcamentoJob, PreferenciasGlobais, StatusOrcamentoJob
from app.models.usuario import Usuario
from app.schemas.orcamento import OrcamentoJobCreate, PreferenciasGlobaisConfig


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
    db: AsyncSession, current_user: Usuario, data: OrcamentoJobCreate
) -> OrcamentoJob:
    """Fase 1 (ver plano de integracao): so persiste o job com status
    PROCESSANDO -- ainda nao dispara a extracao via Claude Vision, isso e
    Fase 2, quando vision_extractor.py for movido pra dentro do backend."""
    job = OrcamentoJob(
        empresa_id=current_user.empresa_id,
        usuario_id=current_user.id,
        projeto_id=data.projeto_id,
        arquivo_origem=data.arquivo_origem,
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
