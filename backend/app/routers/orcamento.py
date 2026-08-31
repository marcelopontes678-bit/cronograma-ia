import shutil
import uuid
from pathlib import Path

import fitz  # PyMuPDF
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.dependencies import get_current_user, get_db
from app.models.usuario import Usuario
from app.schemas.orcamento import (
    FeedbackRequest,
    FeedbackResponse,
    Modulo,
    ModuloManualCreate,
    ModuloPatch,
    OrcamentoJobResponse,
    OrcamentoRequest,
    OrcamentoResponse,
    PreferenciasGlobaisConfig,
    PreferenciasGlobaisResponse,
    RegraAprendidaResponse,
)
from app.services import orcamento_feedback_service, orcamento_pricing_service, orcamento_service
from app.services.orcamento_feedback_service import FeedbackInvalidoError

router = APIRouter(prefix="/orcamentos", tags=["orcamentos"])


# --------------------------------------------------------------------------
# Preferencias Globais
# --------------------------------------------------------------------------

@router.get("/preferencias", response_model=PreferenciasGlobaisResponse)
async def get_preferencias(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return await orcamento_service.get_preferencias(db, current_user)


@router.put("/preferencias", response_model=PreferenciasGlobaisResponse)
async def atualizar_preferencias(
    data: PreferenciasGlobaisConfig,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return await orcamento_service.atualizar_preferencias(db, current_user, data)


# --------------------------------------------------------------------------
# Upload e extracao
# --------------------------------------------------------------------------

@router.post("/jobs", status_code=202)
async def criar_job(
    arquivo: UploadFile,
    background_tasks: BackgroundTasks,
    projeto_id: uuid.UUID | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    if arquivo.content_type not in ("application/pdf", "application/octet-stream") and not (
        arquivo.filename or ""
    ).lower().endswith(".pdf"):
        raise HTTPException(400, "Apenas arquivos PDF sao aceitos.")

    job = await orcamento_service.criar_job(db, current_user, arquivo.filename or "arquivo.pdf", projeto_id)

    pasta_trabalho = Path(settings.ORCAMENTO_STORAGE_DIR) / str(current_user.empresa_id) / str(job.id)
    pasta_trabalho.mkdir(parents=True, exist_ok=True)
    caminho_pdf = pasta_trabalho / "original.pdf"
    with open(caminho_pdf, "wb") as f:
        shutil.copyfileobj(arquivo.file, f)

    try:
        doc = fitz.open(str(caminho_pdf))
        total_paginas = len(doc)
        doc.close()
    except Exception as exc:
        raise HTTPException(400, f"Nao foi possivel abrir o PDF: {exc}") from exc

    background_tasks.add_task(
        orcamento_service.rodar_extracao_em_background, job.id, caminho_pdf, pasta_trabalho, current_user.empresa_id
    )

    return {"job_id": str(job.id), "status": "processando", "paginas": total_paginas}


@router.get("/jobs", response_model=list[OrcamentoJobResponse])
async def listar_jobs(
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return await orcamento_service.listar_jobs(db, current_user, skip, limit)


@router.get("/jobs/{job_id}", response_model=OrcamentoJobResponse)
async def get_job(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return await orcamento_service.get_job(db, job_id, current_user)


# --------------------------------------------------------------------------
# Revisao humana
# --------------------------------------------------------------------------

@router.patch("/jobs/{job_id}/modulos/{modulo_id}", response_model=Modulo)
async def corrigir_modulo(
    job_id: uuid.UUID,
    modulo_id: str,
    patch: ModuloPatch,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    try:
        return await orcamento_service.atualizar_modulo(
            db, job_id, modulo_id, patch.model_dump(exclude_unset=True), current_user
        )
    except orcamento_service.JobInvalidoError as exc:
        raise HTTPException(400, str(exc)) from exc


@router.post("/jobs/{job_id}/modulos", status_code=201, response_model=Modulo)
async def criar_modulo(
    job_id: uuid.UUID,
    data: ModuloManualCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return await orcamento_service.adicionar_modulo(db, job_id, current_user, data)


@router.post("/jobs/{job_id}/confirmar", response_model=OrcamentoJobResponse)
async def confirmar_job(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    try:
        return await orcamento_service.confirmar_job(db, job_id, current_user)
    except orcamento_service.ConfirmacaoBloqueadaError as exc:
        raise HTTPException(409, str(exc)) from exc


# --------------------------------------------------------------------------
# Auto-aprendizado / feedback
# --------------------------------------------------------------------------

@router.post("/feedback", status_code=201, response_model=FeedbackResponse)
async def registrar_feedback(
    request: FeedbackRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    try:
        regra, total_ativas = await orcamento_feedback_service.registrar_feedback(
            db, current_user, request, settings.ANTHROPIC_API_KEY, settings.ORCAMENTO_MODELO_CLAUDE
        )
    except FeedbackInvalidoError as exc:
        raise HTTPException(400, str(exc)) from exc
    return FeedbackResponse(regra=regra, total_regras_ativas_empresa=total_ativas)


@router.get("/regras", response_model=list[RegraAprendidaResponse])
async def listar_regras(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return await orcamento_feedback_service.listar_regras(db, current_user)


@router.delete("/regras/{regra_id}", response_model=RegraAprendidaResponse)
async def desativar_regra(
    regra_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return await orcamento_feedback_service.desativar_regra(db, current_user, regra_id)


# --------------------------------------------------------------------------
# Precificacao
# --------------------------------------------------------------------------

@router.post("", response_model=OrcamentoResponse)
async def gerar_orcamento(
    request: OrcamentoRequest,
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    job = await orcamento_service.get_job(db, job_id, current_user)
    try:
        response, avisos = orcamento_pricing_service.gerar_orcamento(
            job,
            settings.ORCAMENTO_TABELA_PRECOS,
            settings.ORCAMENTO_CONFIG_PRECIFICACAO,
            faturamento_acumulado=request.faturamento_acumulado,
            custo_hora_mao_de_obra=request.custo_hora_mao_de_obra,
            horas_estimadas=request.horas_estimadas,
            fator_area_frontal_para_chapa=request.fator_area_frontal_para_chapa,
        )
    except orcamento_pricing_service.PrecificacaoInvalidaError as exc:
        raise HTTPException(409, str(exc)) from exc

    if avisos:
        return JSONResponse(status_code=200, content={**response.model_dump(mode="json"), "avisos": avisos})
    return response
