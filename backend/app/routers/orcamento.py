import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.models.usuario import Usuario
from app.schemas.orcamento import (
    OrcamentoJobCreate,
    OrcamentoJobResponse,
    PreferenciasGlobaisConfig,
    PreferenciasGlobaisResponse,
)
from app.services import orcamento_service

router = APIRouter(prefix="/orcamentos", tags=["orcamentos"])


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


@router.post("/jobs", response_model=OrcamentoJobResponse, status_code=201)
async def criar_job(
    data: OrcamentoJobCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return await orcamento_service.criar_job(db, current_user, data)


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
