import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db, require_role
from app.models.usuario import RoleUsuario, Usuario
from app.schemas.engenharia import (
    AmbienteCreate,
    AmbienteResponse,
    AmbienteUpdate,
    EngenhariaResumo,
    ModuloCreate,
    ModuloResponse,
    ModuloUpdate,
    PecaCreate,
    PecaResponse,
    PecaUpdate,
)
from app.schemas.plano_corte import PlanoCorteOut
from app.services import engenharia_service, plano_corte_service

router = APIRouter(tags=["engenharia"])

_pode_editar = require_role(RoleUsuario.ADMIN, RoleUsuario.GERENTE)


# ── Ambientes (aninhados no projeto) ─────────────────────────────────────────

@router.post(
    "/projetos/{projeto_id}/ambientes",
    response_model=AmbienteResponse,
    status_code=201,
)
async def create_ambiente(
    projeto_id: uuid.UUID,
    data: AmbienteCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(_pode_editar),
):
    return await engenharia_service.create_ambiente(db, projeto_id, data, current_user)


@router.get(
    "/projetos/{projeto_id}/ambientes", response_model=list[AmbienteResponse]
)
async def list_ambientes(
    projeto_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return await engenharia_service.list_ambientes(db, projeto_id, current_user)


@router.get(
    "/projetos/{projeto_id}/engenharia", response_model=EngenhariaResumo
)
async def resumo_engenharia(
    projeto_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return await engenharia_service.resumo_engenharia(db, projeto_id, current_user)


@router.get(
    "/projetos/{projeto_id}/plano-corte", response_model=PlanoCorteOut
)
async def plano_corte(
    projeto_id: uuid.UUID,
    kerf_mm: int = Query(3, ge=0, le=20),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return await plano_corte_service.gerar_plano_corte(
        db, projeto_id, current_user, kerf_mm
    )


@router.put("/ambientes/{ambiente_id}", response_model=AmbienteResponse)
async def update_ambiente(
    ambiente_id: uuid.UUID,
    data: AmbienteUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(_pode_editar),
):
    return await engenharia_service.update_ambiente(db, ambiente_id, data, current_user)


@router.delete("/ambientes/{ambiente_id}", status_code=204)
async def deactivate_ambiente(
    ambiente_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(_pode_editar),
):
    await engenharia_service.deactivate_ambiente(db, ambiente_id, current_user)


# ── Módulos (aninhados no ambiente) ──────────────────────────────────────────

@router.post(
    "/ambientes/{ambiente_id}/modulos",
    response_model=ModuloResponse,
    status_code=201,
)
async def create_modulo(
    ambiente_id: uuid.UUID,
    data: ModuloCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(_pode_editar),
):
    return await engenharia_service.create_modulo(db, ambiente_id, data, current_user)


@router.put("/modulos/{modulo_id}", response_model=ModuloResponse)
async def update_modulo(
    modulo_id: uuid.UUID,
    data: ModuloUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(_pode_editar),
):
    return await engenharia_service.update_modulo(db, modulo_id, data, current_user)


@router.delete("/modulos/{modulo_id}", status_code=204)
async def deactivate_modulo(
    modulo_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(_pode_editar),
):
    await engenharia_service.deactivate_modulo(db, modulo_id, current_user)


# ── Peças (aninhadas no módulo) ──────────────────────────────────────────────

@router.post(
    "/modulos/{modulo_id}/pecas", response_model=PecaResponse, status_code=201
)
async def create_peca(
    modulo_id: uuid.UUID,
    data: PecaCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(_pode_editar),
):
    return await engenharia_service.create_peca(db, modulo_id, data, current_user)


@router.put("/pecas/{peca_id}", response_model=PecaResponse)
async def update_peca(
    peca_id: uuid.UUID,
    data: PecaUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(_pode_editar),
):
    return await engenharia_service.update_peca(db, peca_id, data, current_user)


@router.delete("/pecas/{peca_id}", status_code=204)
async def deactivate_peca(
    peca_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(_pode_editar),
):
    await engenharia_service.deactivate_peca(db, peca_id, current_user)
