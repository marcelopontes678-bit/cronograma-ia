"""Engenharia manual: ambientes, módulos e peças de um projeto.

Toda verificação de acesso ancora na empresa do projeto — subir a cadeia
peça → módulo → ambiente → projeto garante o isolamento multi-tenant.
"""
import uuid
from collections import defaultdict
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import forbidden_exception, not_found
from app.models.engenharia import Ambiente, Modulo, Peca
from app.models.material import Material
from app.models.projeto import Projeto
from app.models.usuario import RoleUsuario, Usuario
from app.schemas.engenharia import (
    AmbienteCreate,
    AmbienteUpdate,
    EngenhariaResumo,
    ModuloCreate,
    ModuloUpdate,
    PecaCreate,
    PecaUpdate,
    ResumoMaterial,
)


def _check_empresa(projeto: Projeto, current_user: Usuario) -> None:
    if (
        current_user.role != RoleUsuario.ADMIN
        and current_user.empresa_id != projeto.empresa_id
    ):
        raise forbidden_exception


async def _get_projeto_autorizado(
    db: AsyncSession, projeto_id: uuid.UUID, current_user: Usuario
) -> Projeto:
    result = await db.execute(
        select(Projeto).where(Projeto.id == projeto_id, Projeto.is_active.is_(True))
    )
    projeto = result.scalar_one_or_none()
    if not projeto:
        raise not_found("Projeto")
    _check_empresa(projeto, current_user)
    return projeto


async def _get_ambiente_autorizado(
    db: AsyncSession, ambiente_id: uuid.UUID, current_user: Usuario
) -> Ambiente:
    result = await db.execute(
        select(Ambiente)
        .options(selectinload(Ambiente.projeto))
        .where(Ambiente.id == ambiente_id, Ambiente.is_active.is_(True))
    )
    ambiente = result.scalar_one_or_none()
    if not ambiente:
        raise not_found("Ambiente")
    _check_empresa(ambiente.projeto, current_user)
    return ambiente


async def _get_modulo_autorizado(
    db: AsyncSession, modulo_id: uuid.UUID, current_user: Usuario
) -> Modulo:
    result = await db.execute(
        select(Modulo)
        .options(selectinload(Modulo.ambiente).selectinload(Ambiente.projeto))
        .where(Modulo.id == modulo_id, Modulo.is_active.is_(True))
    )
    modulo = result.scalar_one_or_none()
    if not modulo:
        raise not_found("Módulo")
    _check_empresa(modulo.ambiente.projeto, current_user)
    return modulo


# ── Ambientes ────────────────────────────────────────────────────────────────

async def create_ambiente(
    db: AsyncSession,
    projeto_id: uuid.UUID,
    data: AmbienteCreate,
    current_user: Usuario,
) -> Ambiente:
    await _get_projeto_autorizado(db, projeto_id, current_user)
    ambiente = Ambiente(**data.model_dump(), projeto_id=projeto_id)
    db.add(ambiente)
    await db.commit()
    return await _load_ambiente(db, ambiente.id)


async def list_ambientes(
    db: AsyncSession, projeto_id: uuid.UUID, current_user: Usuario
) -> list[Ambiente]:
    await _get_projeto_autorizado(db, projeto_id, current_user)
    result = await db.execute(
        select(Ambiente)
        .options(selectinload(Ambiente.modulos).selectinload(Modulo.pecas))
        .where(Ambiente.projeto_id == projeto_id, Ambiente.is_active.is_(True))
        .order_by(Ambiente.ordem, Ambiente.created_at)
    )
    return list(result.scalars().all())


async def update_ambiente(
    db: AsyncSession,
    ambiente_id: uuid.UUID,
    data: AmbienteUpdate,
    current_user: Usuario,
) -> Ambiente:
    ambiente = await _get_ambiente_autorizado(db, ambiente_id, current_user)
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(ambiente, field, value)
    await db.commit()
    return await _load_ambiente(db, ambiente.id)


async def deactivate_ambiente(
    db: AsyncSession, ambiente_id: uuid.UUID, current_user: Usuario
) -> None:
    ambiente = await _get_ambiente_autorizado(db, ambiente_id, current_user)
    ambiente.is_active = False
    await db.commit()


async def _load_ambiente(db: AsyncSession, ambiente_id: uuid.UUID) -> Ambiente:
    result = await db.execute(
        select(Ambiente)
        .options(selectinload(Ambiente.modulos).selectinload(Modulo.pecas))
        .where(Ambiente.id == ambiente_id)
    )
    return result.scalar_one()


# ── Módulos ──────────────────────────────────────────────────────────────────

async def create_modulo(
    db: AsyncSession,
    ambiente_id: uuid.UUID,
    data: ModuloCreate,
    current_user: Usuario,
) -> Modulo:
    await _get_ambiente_autorizado(db, ambiente_id, current_user)
    modulo = Modulo(**data.model_dump(), ambiente_id=ambiente_id)
    db.add(modulo)
    await db.commit()
    return await _load_modulo(db, modulo.id)


async def update_modulo(
    db: AsyncSession,
    modulo_id: uuid.UUID,
    data: ModuloUpdate,
    current_user: Usuario,
) -> Modulo:
    modulo = await _get_modulo_autorizado(db, modulo_id, current_user)
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(modulo, field, value)
    await db.commit()
    return await _load_modulo(db, modulo.id)


async def deactivate_modulo(
    db: AsyncSession, modulo_id: uuid.UUID, current_user: Usuario
) -> None:
    modulo = await _get_modulo_autorizado(db, modulo_id, current_user)
    modulo.is_active = False
    await db.commit()


async def _load_modulo(db: AsyncSession, modulo_id: uuid.UUID) -> Modulo:
    result = await db.execute(
        select(Modulo)
        .options(selectinload(Modulo.pecas))
        .where(Modulo.id == modulo_id)
    )
    return result.scalar_one()


# ── Peças ────────────────────────────────────────────────────────────────────

async def create_peca(
    db: AsyncSession,
    modulo_id: uuid.UUID,
    data: PecaCreate,
    current_user: Usuario,
) -> Peca:
    await _get_modulo_autorizado(db, modulo_id, current_user)
    if data.material_id:
        await _check_material(db, data.material_id, current_user)
    peca = Peca(**data.model_dump(), modulo_id=modulo_id)
    db.add(peca)
    await db.commit()
    await db.refresh(peca)
    return peca


async def update_peca(
    db: AsyncSession,
    peca_id: uuid.UUID,
    data: PecaUpdate,
    current_user: Usuario,
) -> Peca:
    result = await db.execute(
        select(Peca)
        .options(
            selectinload(Peca.modulo)
            .selectinload(Modulo.ambiente)
            .selectinload(Ambiente.projeto)
        )
        .where(Peca.id == peca_id, Peca.is_active.is_(True))
    )
    peca = result.scalar_one_or_none()
    if not peca:
        raise not_found("Peça")
    _check_empresa(peca.modulo.ambiente.projeto, current_user)

    update_data = data.model_dump(exclude_none=True)
    if "material_id" in update_data:
        await _check_material(db, update_data["material_id"], current_user)
    for field, value in update_data.items():
        setattr(peca, field, value)
    await db.commit()
    await db.refresh(peca)
    return peca


async def deactivate_peca(
    db: AsyncSession, peca_id: uuid.UUID, current_user: Usuario
) -> None:
    result = await db.execute(
        select(Peca)
        .options(
            selectinload(Peca.modulo)
            .selectinload(Modulo.ambiente)
            .selectinload(Ambiente.projeto)
        )
        .where(Peca.id == peca_id, Peca.is_active.is_(True))
    )
    peca = result.scalar_one_or_none()
    if not peca:
        raise not_found("Peça")
    _check_empresa(peca.modulo.ambiente.projeto, current_user)
    peca.is_active = False
    await db.commit()


async def _check_material(
    db: AsyncSession, material_id: uuid.UUID, current_user: Usuario
) -> None:
    """Material referenciado precisa existir e ser da mesma empresa."""
    result = await db.execute(
        select(Material).where(
            Material.id == material_id, Material.is_active.is_(True)
        )
    )
    material = result.scalar_one_or_none()
    if not material:
        raise not_found("Material")
    if (
        current_user.role != RoleUsuario.ADMIN
        and material.empresa_id != current_user.empresa_id
    ):
        raise forbidden_exception


# ── Resumo (base da lista de corte) ──────────────────────────────────────────

async def resumo_engenharia(
    db: AsyncSession, projeto_id: uuid.UUID, current_user: Usuario
) -> EngenhariaResumo:
    projeto = await _get_projeto_autorizado(db, projeto_id, current_user)
    ambientes = await list_ambientes(db, projeto_id, current_user)

    materiais_result = await db.execute(
        select(Material).where(Material.empresa_id == projeto.empresa_id)
    )
    nomes_materiais = {m.id: m.nome for m in materiais_result.scalars().all()}

    total_modulos = 0
    total_pecas = 0
    acumulado: dict = defaultdict(lambda: {"pecas": 0, "area": 0.0, "fita": 0.0})

    for amb in ambientes:
        for mod in amb.modulos:
            if not mod.is_active:
                continue
            total_modulos += 1
            for p in mod.pecas:
                if not p.is_active:
                    continue
                qtd_total = p.quantidade * mod.quantidade
                total_pecas += qtd_total
                key = p.material_id
                comp_m = p.comprimento_mm / 1000
                larg_m = p.largura_mm / 1000
                fita_m = (
                    (comp_m if p.fita_c1 else 0)
                    + (comp_m if p.fita_c2 else 0)
                    + (larg_m if p.fita_l1 else 0)
                    + (larg_m if p.fita_l2 else 0)
                ) * qtd_total
                acumulado[key]["pecas"] += qtd_total
                acumulado[key]["area"] += comp_m * larg_m * qtd_total
                acumulado[key]["fita"] += fita_m

    materiais = [
        ResumoMaterial(
            material_id=key,
            material_nome=nomes_materiais.get(key, "Sem material definido"),
            total_pecas=v["pecas"],
            area_m2=round(v["area"], 3),
            fita_borda_m=round(v["fita"], 2),
        )
        for key, v in acumulado.items()
    ]

    return EngenhariaResumo(
        projeto_id=projeto_id,
        total_ambientes=len(ambientes),
        total_modulos=total_modulos,
        total_pecas=total_pecas,
        materiais=materiais,
        ambientes=ambientes,
    )
